"""Long Kitten Nation (mc.mattkrupa.net): roles and announcements from the site's account states.

Every LKN_SYNC_SECONDS the bot asks the site who signed in with Discord. Approved players get the
LKN role, banned ones lose it. When an account goes from "pending" to "approved" Sprytek welcomes
the player, and when someone starts waiting for approval the admins get a DM.
"""
import logging

import aiohttp
import discord

logger = logging.getLogger(__name__)

SITE = "https://mc.mattkrupa.net"


class LongKittenNation:
    def __init__(self, client: discord.Client, config: dict, store):
        self.client = client
        self.config = config
        self.store = store

    @property
    def enabled(self) -> bool:
        c = self.config
        return bool(c['LKN_BOT_SECRET'] and c['LKN_GUILD_ID'] and c['LKN_ROLE_ID'])

    async def fetch_members(self):
        url = f"{self.config['LKN_URL']}/internal/bot/members"
        headers = {"Authorization": f"Bearer {self.config['LKN_BOT_SECRET']}"}
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as s:
            async with s.get(url, headers=headers) as r:
                r.raise_for_status()
                return await r.json()

    async def sync(self):
        guild = self.client.get_guild(self.config['LKN_GUILD_ID'])
        if guild is None:
            logger.warning("LKN guild not found")
            return
        role = guild.get_role(self.config['LKN_ROLE_ID'])
        if role is None:
            logger.warning("LKN role not found")
            return

        members = await self.fetch_members()
        known = self.store.lkn_known()
        first_run = self.store.get_meta('lkn_synced') is None

        for m in members:
            did, status, name = m['discord_id'], m['status'], m.get('mc_name') or 'someone'
            member = guild.get_member(int(did))

            # roles
            if member is not None:
                try:
                    if status == 'approved' and role not in member.roles:
                        await member.add_roles(role, reason="Approved on mc.mattkrupa.net")
                        logger.info(f"Gave {role.name} to {member} ({name})")
                    elif status == 'banned' and role in member.roles:
                        await member.remove_roles(role, reason="Banned on mc.mattkrupa.net")
                        logger.info(f"Took {role.name} from {member} ({name})")
                except discord.HTTPException as e:
                    logger.error(f"Role change for {did} failed: {e}")

            if first_run:
                continue
            before = known.get(did, (None, None))[0]

            # someone is waiting for approval: tell the admins
            if status == 'pending' and before != 'pending':
                await self.tell_admins(members, f"**{name}** linked their Minecraft account and is waiting for approval: {SITE}/admin")

            # approved after waiting: welcome
            if status == 'approved' and before == 'pending':
                await self.welcome(member, name)

        self.store.lkn_save(members)
        self.store.set_meta('lkn_synced', '1')

    async def tell_admins(self, members: list, text: str):
        for m in members:
            if m['role'] != 'admin' or m['status'] != 'approved':
                continue
            try:
                user = self.client.get_user(int(m['discord_id'])) or await self.client.fetch_user(int(m['discord_id']))
                await user.send(text)
            except discord.HTTPException as e:
                logger.warning(f"Could not DM admin {m['discord_id']}: {e}")

    async def welcome(self, member, name: str):
        channel = self.client.get_channel(self.config['LKN_CHANNEL_ID'])
        if channel is None:
            return
        who = member.mention if member else f"**{name}**"
        try:
            await channel.send(
                f"🐈 {who} ({name}) is now part of Long Kitten Nation. Long has one more friend with time for him.",
                allowed_mentions=discord.AllowedMentions(users=True),
            )
        except discord.HTTPException as e:
            logger.warning(f"Welcome message failed: {e}")
