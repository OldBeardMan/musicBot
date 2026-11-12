"""Seasons Clicker (mattkrupa.net/seasons-clicker): the leaderboard on Discord.

The game keeps its leaderboard on mattkrupa.net (repo mattnet, worker/scores.js). Players who link
their Discord account in the game (Menu > Scores > Link my Discord, then /clicker link CODE here)
get the Seasons Clicker roles they have earned, and Sprytek tells #sc-scores about new records.

Every CLICKER_SYNC_SECONDS the bot reads the linked players and the new records from the site.
Roles are only ever given, never taken: older roles from the points system stay with their owners.
"""
import logging

import aiohttp
import discord
from discord import app_commands

logger = logging.getLogger(__name__)

GAME = "https://mattkrupa.net/seasons-clicker?from=discord"

# The Seasons Clicker ladder on the server (role names, see longkitten-nation docs/discord.md),
# from the easiest; each with what a player needs in the game
LADDER = [
    ("Autumn Wanderer", "finish the story: 19 kittens home", lambda p: p["finished"]),
    ("Do-Not-Listener", "send 1,000 Whispers away", lambda p: p["whispers"] >= 1000),
    ("Winter Gifter", "start one more song 5 times", lambda p: p["melodies"] >= 5),
    ("Nordic Mountaineer", "a score of 1 sextillion notes", lambda p: p["score"] >= 1e21),
    ("Icelandic Fugitive", "a score of 1 octillion notes", lambda p: p["score"] >= 1e27),
    ("Spring Lighter", "every achievement in the game",
     lambda p: p["achievements_total"] > 0 and p["achievements"] >= p["achievements_total"]),
]

BIG = [(1e33, "decillion"), (1e30, "nonillion"), (1e27, "octillion"), (1e24, "septillion"), (1e21, "sextillion"),
       (1e18, "quintillion"), (1e15, "quadrillion"), (1e12, "trillion"), (1e9, "billion"), (1e6, "million")]


def notes(n: float) -> str:
    """3.2 septillion, like the game writes big numbers."""
    for value, word in BIG:
        if n >= value:
            return f"{n / value:.3f}".rstrip("0").rstrip(".") + " " + word
    return f"{int(n):,}"


class SeasonsClicker:
    def __init__(self, client: discord.Client, config: dict, store):
        self.client = client
        self.config = config
        self.store = store

    @property
    def enabled(self) -> bool:
        return bool(self.config['CLICKER_BOT_SECRET'] and self.config['CLICKER_GUILD_ID'])

    async def api(self, method: str, path: str, body: dict = None):
        url = f"{self.config['CLICKER_URL']}{path}"
        headers = {"Authorization": f"Bearer {self.config['CLICKER_BOT_SECRET']}"}
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as s:
            async with s.request(method, url, headers=headers, json=body) as r:
                data = await r.json(content_type=None)
                if r.status >= 400:
                    raise ClickerError(data.get("error", f"HTTP {r.status}") if isinstance(data, dict) else f"HTTP {r.status}")
                return data

    def guild(self):
        return self.client.get_guild(self.config['CLICKER_GUILD_ID'])

    def channel(self):
        return self.client.get_channel(self.config['CLICKER_CHANNEL_ID']) if self.config['CLICKER_CHANNEL_ID'] else None

    # ------------------------------------------------------------ roles

    async def give_roles(self, guild: discord.Guild, member: discord.Member, player: dict, announce: bool = True):
        """Gives every ladder role the player has earned and does not have yet. Returns their names."""
        given = []
        for name, _, earned in LADDER:
            role = discord.utils.get(guild.roles, name=name)
            if role is None:
                logger.warning(f"Seasons Clicker role {name!r} not found")
                continue
            if role in member.roles or not earned(player):
                continue
            try:
                await member.add_roles(role, reason="Earned in Seasons Clicker")
                given.append(name)
                logger.info(f"Gave {name} to {member} ({player['name']})")
            except discord.HTTPException as e:
                logger.error(f"Giving {name} to {member} failed: {e}")
        channel = self.channel()
        if given and announce and channel is not None:
            roles = ", ".join(f"**{n}**" for n in given)
            try:
                await channel.send(f"🏅 {member.mention} earned {roles} in Seasons Clicker!",
                                   allowed_mentions=discord.AllowedMentions(users=True))
            except discord.HTTPException as e:
                logger.warning(f"Role announcement failed: {e}")
        return given

    # ------------------------------------------------------------ the loop

    async def sync(self):
        guild = self.guild()
        if guild is None:
            logger.warning("Seasons Clicker guild not found")
            return

        players = (await self.api("GET", "/api/bot/players"))["players"]
        for player in players:
            member = guild.get_member(int(player["discord_id"]))
            if member is not None:
                await self.give_roles(guild, member, player)

        # New records since last time; on the very first run only remember where the list ends
        after = int(self.store.get_meta('clicker_seq') or 0)
        first_run = self.store.get_meta('clicker_seq') is None
        events = (await self.api("GET", f"/api/bot/events?after={after}"))["events"]
        for event in events:
            if not first_run:
                await self.announce(guild, event)
            after = max(after, event["seq"])
        if events or first_run:
            self.store.set_meta('clicker_seq', str(after))

    async def announce(self, guild: discord.Guild, event: dict):
        channel = self.channel()
        if channel is None:
            return
        data = event.get("data") or {}
        member = guild.get_member(int(event["discord_id"])) if event.get("discord_id") else None
        who = f"{member.mention} (**{data.get('name', '?')}**)" if member else f"**{data.get('name', 'someone')}**"
        if event["kind"] == "first":
            text = f"👑 {who} is the new **#1** in Seasons Clicker with **{notes(data.get('score', 0))}** notes!"
        elif event["kind"] == "top10":
            text = f"🎵 {who} just reached **#{data.get('place', '?')}** in Seasons Clicker with {notes(data.get('score', 0))} notes."
        else:
            return
        try:
            await channel.send(text, allowed_mentions=discord.AllowedMentions(users=True))
        except discord.HTTPException as e:
            logger.warning(f"Record announcement failed: {e}")


class ClickerError(Exception):
    pass


def setup_clicker_commands(client, clicker: SeasonsClicker):
    group = app_commands.Group(name="clicker", description="Seasons Clicker: the leaderboard and its roles")

    @group.command(name="link", description="Link your Seasons Clicker game (code from Menu > Scores in the game)")
    @app_commands.describe(code="The 6-letter code from the game")
    async def link(interaction: discord.Interaction, code: str):
        if not clicker.enabled:
            await interaction.response.send_message("The leaderboard is not connected yet.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        try:
            player = (await clicker.api("POST", "/api/bot/link", {"code": code.strip().upper(), "discord_id": str(interaction.user.id)}))["player"]
        except ClickerError as e:
            await interaction.followup.send(f"That did not work ({e}). Make a new code in the game: Menu > Scores > Link my Discord.", ephemeral=True)
            return
        except Exception as e:
            logger.warning(f"/clicker link failed: {e}")
            await interaction.followup.send("The leaderboard did not answer. Try again in a minute.", ephemeral=True)
            return
        given = []
        if interaction.guild and isinstance(interaction.user, discord.Member):
            given = await clicker.give_roles(interaction.guild, interaction.user, player, announce=False)
        text = f"🐾 Linked! You are **{player['name']}** with **{notes(player['score'])}** notes."
        if given:
            text += "\nNew roles: " + ", ".join(f"**{n}**" for n in given)
        await interaction.followup.send(text, ephemeral=True)

    @group.command(name="top", description="The best Seasons Clicker players")
    async def top(interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            url = f"{clicker.config['CLICKER_URL']}/api/top"
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as s:
                async with s.get(url) as r:
                    players = (await r.json(content_type=None))["players"][:10]
        except Exception as e:
            logger.warning(f"/clicker top failed: {e}")
            await interaction.followup.send("The leaderboard did not answer. Try again in a minute.")
            return
        embed = discord.Embed(title="Seasons Clicker: the best players", url=GAME, color=0xF3C26B)
        if not players:
            embed.description = f"Nobody on the board yet. [Play]({GAME}) and join it in Menu > Scores!"
        else:
            embed.description = "\n".join(
                f"**{i}.** {p['name']}{' 🐾' if p.get('discord') else ''}: {notes(p['score'])}"
                for i, p in enumerate(players, 1))
        embed.set_footer(text="Join from the game: Menu > Scores")
        await interaction.followup.send(embed=embed)

    @group.command(name="roles", description="What the Seasons Clicker roles are for")
    async def roles(interaction: discord.Interaction):
        lines = [f"**{name}**: {need}" for name, need, _ in LADDER]
        await interaction.response.send_message(
            "🏅 Seasons Clicker roles (link your game with `/clicker link` and Sprytek gives them by himself):\n" + "\n".join(lines),
            ephemeral=True)

    @group.command(name="hide", description="Take a name off the Seasons Clicker leaderboard (moderators)")
    @app_commands.describe(name="The name as it shows on the leaderboard")
    @app_commands.default_permissions(manage_messages=True)
    async def hide(interaction: discord.Interaction, name: str):
        try:
            hidden = (await clicker.api("POST", "/api/bot/hide", {"name": name}))["hidden"]
        except Exception as e:
            await interaction.response.send_message(f"Could not hide it: {e}", ephemeral=True)
            return
        await interaction.response.send_message(f"Hidden {hidden} entr{'y' if hidden == 1 else 'ies'} named **{name}**.", ephemeral=True)

    client.tree.add_command(group)
