import discord
from discord.ext import tasks
import asyncio
import os
import logging
import random
from datetime import timezone, timedelta
from typing import Optional

from .config import CONFIG
from .playlist import PlaylistManager
from .points import PointSystem
from .commands import setup_commands
from .achievements import AchievementSystem

logger = logging.getLogger(__name__)

class MusicBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.voice_states = True
        super().__init__(intents=intents)

        self.tree = discord.app_commands.CommandTree(self)
        
        self.config = CONFIG
        self.synced = False
        self.playlist_manager = PlaylistManager(CONFIG['MUSIC_FOLDER'])
        self.point_system = PointSystem(CONFIG['USERS_DATA_FILE'])
        self.achievement_system = AchievementSystem(self.point_system)
        self.last_message_times = {}

        # Konfiguracja komend
        setup_commands(self, self.config, self.point_system, self.achievement_system, self.playlist_manager)
    
    async def setup_hook(self):
        """Hook wywoływany przed połączeniem - synchronizacja przeniesiona do on_ready."""
        pass
    
    async def on_ready(self):
        """Wywoływane gdy bot jest gotowy."""
        logger.info(f'Zalogowano jako {self.user}')

        # Synchronizacja komend per-guild (natychmiastowa)
        if not self.synced:
            for guild in self.guilds:
                try:
                    self.tree.copy_global_to(guild=guild)
                    synced = await self.tree.sync(guild=guild)
                    logger.info(f"Zsynchronizowano {len(synced)} komend na serwerze {guild.name}")
                except Exception as e:
                    logger.error(f"Błąd synchronizacji komend na {guild.name}: {e}")
            self.synced = True

        # Sprawdzenie whitelisty serwerów
        await self._check_guild_whitelist()

        # Ustawienie statusu
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name='Matt Krupa'))

        # Połączenie z kanałem głosowym
        await self._connect_to_voice_channel()

        # Start odtwarzania muzyki
        if not self.background_music.is_running():
            self.background_music.start()

    async def _check_guild_whitelist(self):
        """Sprawdza i opuszcza serwery spoza whitelisty."""
        allowed_guilds = self.config.get('ALLOWED_GUILDS', [])
        if not allowed_guilds:
            logger.info("Whitelist serwerów jest pusta - bot pozostaje na wszystkich serwerach")
            return

        for guild in self.guilds:
            if guild.id not in allowed_guilds:
                logger.warning(f"Opuszczam serwer spoza whitelisty: {guild.name} ({guild.id})")
                await guild.leave()

    async def on_guild_join(self, guild):
        """Wywoływane gdy bot dołącza do nowego serwera."""
        allowed_guilds = self.config.get('ALLOWED_GUILDS', [])
        if allowed_guilds and guild.id not in allowed_guilds:
            logger.warning(f"Odmowa dołączenia do serwera spoza whitelisty: {guild.name} ({guild.id})")
            await guild.leave()
            return

        # Synchronizacja komend na nowym serwerze
        try:
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            logger.info(f"Zsynchronizowano {len(synced)} komend na nowym serwerze {guild.name}")
        except Exception as e:
            logger.error(f"Błąd synchronizacji komend na {guild.name}: {e}")
    
    async def _connect_to_voice_channel(self):
        """Łączy z określonym kanałem głosowym."""
        try:
            channel = self.get_channel(self.config['VOICE_CHANNEL_ID'])
            if channel and isinstance(channel, discord.VoiceChannel):
                await channel.connect()
                logger.info(f"Połączono z kanałem głosowym: {channel.name}")
            else:
                logger.error("Nie można znaleźć kanału głosowego")
        except Exception as e:
            logger.error(f"Błąd połączenia z kanałem głosowym: {e}")
    
    def _get_random_cat_image(self) -> Optional[str]:
        """Zwraca losowy obraz kota."""
        try:
            cat_images = [
                file for file in os.listdir(self.config['CAT_IMAGES_FOLDER']) 
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))
            ]
            if cat_images:
                return os.path.join(self.config['CAT_IMAGES_FOLDER'], random.choice(cat_images))
        except FileNotFoundError:
            logger.error(f"Folder {self.config['CAT_IMAGES_FOLDER']} nie istnieje")
        return None
    
    async def on_message(self, message):
        """Obsługa wiadomości."""
        if message.author.bot:
            return
        
        # Anti-spam
        current_time = message.created_at.timestamp()
        user_id = str(message.author.id)
        
        if user_id in self.last_message_times:
            time_diff = current_time - self.last_message_times[user_id]
            if time_diff < self.config['SPAM_COOLDOWN']:
                try:
                    await message.reply(f"{message.author.mention}, nie spamuj! Odczekaj chwilę.")
                except discord.Forbidden:
                    pass
                return
        
        self.last_message_times[user_id] = current_time

        # Dodawanie punktów
        points_to_add = 1
        if message.channel.name == 'memes':
            # Sprawdź czy wiadomość zawiera obraz
            image_extensions = ('png', 'jpg', 'jpeg', 'gif')
            if any(att.filename.lower().endswith(image_extensions) for att in message.attachments):
                points_to_add = 5
                # Ustaw flagę first_meme jeśli jeszcze nie ustawiona
                if not self.achievement_system.get_flag(user_id, 'first_meme'):
                    self.achievement_system.set_flag(user_id, 'first_meme', True)

        self.point_system.add_points(user_id, points_to_add)

        # Achievement za napisanie "kuna"
        if "kuna" in message.content.lower():
            if not self.achievement_system.get_flag(user_id, 'kuna'):
                self.achievement_system.set_flag(user_id, 'kuna', True)

        # Achievement za wiadomość o 21:37 (czas polski)
        poland_tz = timezone(timedelta(hours=1))  # CET (zimą +1, latem +2)
        msg_time = message.created_at.astimezone(poland_tz)
        if msg_time.hour == 21 and msg_time.minute == 37:
            if not self.achievement_system.get_flag(user_id, 'jp2'):
                self.achievement_system.set_flag(user_id, 'jp2', True)

        # Sprawdź achievementy
        new_achievements = self.achievement_system.check_and_award_achievements(user_id)
        if new_achievements:
            from .achievements import ACHIEVEMENTS
            achievement_names = [ACHIEVEMENTS[a]['emoji'] + ' ' + ACHIEVEMENTS[a]['name'] for a in new_achievements]
            try:
                await message.channel.send(
                    f"{message.author.mention} zdobywa: {', '.join(achievement_names)}"
                )
            except discord.Forbidden:
                pass

        # Odpowiedź na słowo kluczowe "kuna"
        if "kuna" in message.content.lower():
            try:
                await message.reply("kuna")
            except discord.Forbidden:
                pass
    
    @tasks.loop(seconds=CONFIG['MUSIC_BREAK'])
    async def background_music(self):
        """Odtwarza muzykę w tle."""
        # Sprawdź czy jest połączenie, jeśli nie - połącz ponownie
        if not self.voice_clients:
            logger.warning("Brak połączenia głosowego, próba ponownego połączenia...")
            await self._connect_to_voice_channel()
            return

        voice_client = self.voice_clients[0]

        # Sprawdź czy połączenie jest aktywne
        if not voice_client.is_connected():
            logger.warning("Połączenie głosowe nieaktywne, rozłączam i łączę ponownie...")
            try:
                await voice_client.disconnect(force=True)
            except:
                pass
            await self._connect_to_voice_channel()
            return

        if voice_client.is_playing():
            return

        song = self.playlist_manager.get_next_song()
        if song and os.path.isfile(song):
            try:
                source = discord.FFmpegPCMAudio(song)
                voice_client.play(source)
                logger.info(f"Odtwarzam: {os.path.basename(song)}")
            except Exception as e:
                logger.error(f"Błąd odtwarzania {song}: {e}")