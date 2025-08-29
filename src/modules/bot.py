import discord
from discord.ext import tasks
import asyncio
import os
import logging
import random
from typing import Optional

from .config import CONFIG
from .playlist import PlaylistManager
from .points import PointSystem
from .commands import setup_commands

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
        self.last_message_times = {}
        
        # Poziomy i nagrody
        self.levels = [
            (10, "printer"),
            (100, "Autumn Wanderer"),
            (500, "Do-Not-Listener"),
            (2500, "Winter Gifter"),
            (10000, "Nordic Mountaineer"),
            (100000, "Icelandic Fugitive"),
            (1000000, "The Matt Devotee")
        ]
        
        # Konfiguracja komend
        setup_commands(self, self.config, self.point_system)
    
    async def setup_hook(self):
        """Synchronizuje komendy przy starcie."""
        try:
            synced = await self.tree.sync()
            logger.info(f"Zsynchronizowano {len(synced)} komend")
        except Exception as e:
            logger.error(f"Błąd synchronizacji komend: {e}")
    
    async def on_ready(self):
        """Wywoływane gdy bot jest gotowy."""
        logger.info(f'Zalogowano jako {self.user}')
        
        # Ustawienie statusu
        await self.change_presence(activity=discord.Game(name='Matt Krupa'))
        
        # Połączenie z kanałem głosowym
        await self._connect_to_voice_channel()
        
        # Start odtwarzania muzyki
        if not self.background_music.is_running():
            self.background_music.start()
    
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
    
    async def _check_level_up(self, user, channel, old_points, new_points):
        """Sprawdza czy użytkownik awansował na wyższy poziom."""
        for points_needed, role_name in self.levels:
            if new_points >= points_needed and old_points < points_needed:
                role = discord.utils.get(user.guild.roles, name=role_name)
                if role:
                    try:
                        await user.add_roles(role)
                        level_num = self.levels.index((points_needed, role_name)) + 1
                        
                        if points_needed == 1000000:  # Najwyższy poziom
                            await channel.send(
                                f"🎉 {user.mention} osiągnął najwyższy poziom! "
                                f"Rola: {role_name}! Właśnie wysłał swoją milionową wiadomość! 🎉"
                            )
                        else:
                            await channel.send(
                                f"🎊 {user.mention} osiągnął poziom {level_num}! "
                                f"Nowa rola: {role_name}!"
                            )
                    except discord.Forbidden:
                        logger.error(f"Brak uprawnień do nadania roli {role_name}")
                break
    
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
        
        # Zapisz stare punkty dla sprawdzenia poziomu
        old_points = self.point_system.get_points(user_id)
        
        # Dodawanie punktów
        points_to_add = 1
        if message.channel.name == 'memes':
            # Sprawdź czy wiadomość zawiera obraz
            image_extensions = ('png', 'jpg', 'jpeg', 'gif')
            if any(att.filename.lower().endswith(image_extensions) for att in message.attachments):
                points_to_add = 5
        
        self.point_system.add_points(user_id, points_to_add)
        new_points = self.point_system.get_points(user_id)
        
        # Sprawdź awans
        await self._check_level_up(message.author, message.channel, old_points, new_points)
        
        # Odpowiedzi na słowa kluczowe
        keyword_responses = {
            "kuna": "kuna",
            "matt": "Jeśli chcesz wiedzieć więcej o Matt, sprawdź: https://mattkrupa.net/",
            "sprytek": "To ja!",
            "sus": "amogus"
        }
        
        content_lower = message.content.lower()
        for keyword, response in keyword_responses.items():
            if keyword in content_lower:
                try:
                    await message.reply(response)
                except discord.Forbidden:
                    pass
                break
    
    @tasks.loop(seconds=CONFIG['MUSIC_BREAK'])
    async def background_music(self):
        """Odtwarza muzykę w tle."""
        if not self.voice_clients:
            return
        
        voice_client = self.voice_clients[0]
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