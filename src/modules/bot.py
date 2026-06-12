import discord
import logging

from .config import CONFIG
from .commands import setup_commands

logger = logging.getLogger(__name__)

class SprytekBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.guilds = True
        super().__init__(intents=intents)

        self.tree = discord.app_commands.CommandTree(self)

        self.config = CONFIG
        self.synced = False

        # Set up commands
        setup_commands(self, self.config)

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

    async def on_guild_join(self, guild):
        """Called when the bot joins a new server - synchronizes commands."""
        try:
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            logger.info(f"Synchronized {len(synced)} commands on new server {guild.name}")
        except Exception as e:
            logger.error(f"Error synchronizing commands on {guild.name}: {e}")
