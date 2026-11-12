import discord
import logging
from discord.ext import tasks

from .config import CONFIG
from .clicker import SeasonsClicker, setup_clicker_commands
from .commands import setup_commands
from .lkn import LongKittenNation
from .store import Store

logger = logging.getLogger(__name__)

class SprytekBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True
        # needed to see members for Long Kitten Nation roles
        intents.members = True
        super().__init__(intents=intents)

        self.tree = discord.app_commands.CommandTree(self)

        self.config = CONFIG
        self.synced = False
        self.store = Store(CONFIG['DATA_DB'])
        self.lkn = LongKittenNation(self, CONFIG, self.store)
        self.clicker = SeasonsClicker(self, CONFIG, self.store)

        # Set up commands
        setup_commands(self, self.config, self.store)
        setup_clicker_commands(self, self.clicker)

    async def on_ready(self):
        """Called when the bot is ready."""
        logger.info(f'Logged in as {self.user}')

        # Per-guild command synchronization (immediate)
        if not self.synced:
            # Save commands from the tree
            commands = self.tree.get_commands()

            # Clear global commands from the Discord API
            self.tree.clear_commands(guild=None)
            await self.tree.sync()
            logger.info("Cleared global commands from Discord")

            # Restore commands to the tree
            for cmd in commands:
                self.tree.add_command(cmd)

            # Synchronize per-guild
            for guild in self.guilds:
                try:
                    self.tree.copy_global_to(guild=guild)
                    synced = await self.tree.sync(guild=guild)
                    logger.info(f"Synchronized {len(synced)} commands on server {guild.name}")
                except Exception as e:
                    logger.error(f"Error synchronizing commands on {guild.name}: {e}")
            self.synced = True

        # Set the presence
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='Sprytek'))

        # Long Kitten Nation roles and announcements
        if self.lkn.enabled and not self.lkn_loop.is_running():
            self.lkn_loop.change_interval(seconds=max(15, CONFIG['LKN_SYNC_SECONDS']))
            self.lkn_loop.start()
        elif not self.lkn.enabled:
            logger.info("Long Kitten Nation sync is off (LKN_BOT_SECRET, LKN_GUILD_ID or LKN_ROLE_ID missing)")

        # Seasons Clicker leaderboard: roles and records
        if self.clicker.enabled and not self.clicker_loop.is_running():
            self.clicker_loop.change_interval(seconds=max(30, CONFIG['CLICKER_SYNC_SECONDS']))
            self.clicker_loop.start()
        elif not self.clicker.enabled:
            logger.info("Seasons Clicker sync is off (CLICKER_BOT_SECRET or CLICKER_GUILD_ID missing)")

    @tasks.loop(seconds=60)
    async def lkn_loop(self):
        try:
            await self.lkn.sync()
        except Exception as e:
            logger.warning(f"Long Kitten Nation sync failed: {e}")

    @tasks.loop(seconds=120)
    async def clicker_loop(self):
        try:
            await self.clicker.sync()
        except Exception as e:
            logger.warning(f"Seasons Clicker sync failed: {e}")

    async def on_guild_join(self, guild):
        """Called when the bot joins a new server - synchronizes commands."""
        try:
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            logger.info(f"Synchronized {len(synced)} commands on new server {guild.name}")
        except Exception as e:
            logger.error(f"Error synchronizing commands on {guild.name}: {e}")
