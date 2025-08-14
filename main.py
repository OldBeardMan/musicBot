import discord
from discord.ext import tasks
from discord import app_commands
import asyncio
import os
import logging
import random
from typing import Optional
import json

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Konfiguracja
CONFIG = {
    'VOICE_CHANNEL_ID': 1173158666174742538,
    'CAT_IMAGES_FOLDER': 'cat_images',
    'MUSIC_FOLDER': 'music',
    'USERS_DATA_FILE': 'users_data.json',
    'SPAM_COOLDOWN': 3,  # sekundy
    'MUSIC_BREAK': 5,    # sekundy między utworami
}

# Moduł playlist
class PlaylistManager:
    def __init__(self, folder_path: str):
        self.folder_path = folder_path
        self.playlist = self._create_playlist()
    
    def _create_playlist(self):
        """Tworzy playlistę z plików w folderze."""
        try:
            files = os.listdir(self.folder_path)
            playlist = []
            for filename in files:
                file_path = os.path.join(self.folder_path, filename)
                if os.path.isfile(file_path) and filename.lower().endswith(('.mp3', '.wav', '.ogg', '.m4a')):
                    playlist.append(file_path)
            return playlist
        except FileNotFoundError:
            logger.error(f"Folder {self.folder_path} nie został znaleziony")
            return []
    
    def get_next_song(self):
        """Zwraca następny utwór i przenosi go na koniec listy."""
        if self.playlist:
            song = self.playlist.pop(0)
            self.playlist.append(song)
            return song
        return None

# Klasa użytkownika
class User:
    def __init__(self, user_id: str, points: int = 0):
        self.user_id = user_id
        self.points = points

# System punktów
class PointSystem:
    def __init__(self, file_path: str = CONFIG['USERS_DATA_FILE']):
        self.file_path = file_path
        self.users = self._load_users_data()
    
    def _save_users_data(self):
        """Zapisuje dane użytkowników do pliku JSON."""
        try:
            current_data = {user_id: self.users[user_id].points for user_id in self.users}
            with open(self.file_path, 'w') as file:
                json.dump(current_data, file, indent=4)
        except Exception as e:
            logger.error(f"Błąd przy zapisywaniu danych: {e}")
    
    def _load_users_data(self):
        """Ładuje dane użytkowników z pliku JSON."""
        try:
            with open(self.file_path, 'r') as file:
                data = json.load(file)
                users = {user_id: User(user_id, points) for user_id, points in data.items()}
                return users
        except FileNotFoundError:
            logger.info("Plik z danymi użytkowników nie istnieje, tworzę nowy")
            return {}
        except Exception as e:
            logger.error(f"Błąd przy ładowaniu danych: {e}")
            return {}
    
    def add_user(self, user_id: str):
        """Dodaje nowego użytkownika jeśli nie istnieje."""
        if user_id not in self.users:
            self.users[user_id] = User(user_id)
            self._save_users_data()
    
    def add_points(self, user_id: str, points: int):
        """Dodaje punkty użytkownikowi."""
        self.add_user(user_id)
        self.users[user_id].points += points
        self._save_users_data()
    
    def sub_points(self, user_id: str, points: int):
        """Odejmuje punkty użytkownikowi (z zabezpieczeniem przed ujemnymi punktami)."""
        self.add_user(user_id)
        new_points = max(0, self.users[user_id].points - points)
        self.users[user_id].points = new_points
        self._save_users_data()
    
    def get_points(self, user_id: str) -> int:
        """Zwraca liczbę punktów użytkownika."""
        self.add_user(user_id)
        return self.users[user_id].points

# Główna klasa klienta
class MusicBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.voice_states = True
        super().__init__(intents=intents)

        self.tree = app_commands.CommandTree(self)
        
        self.synced = False
        self.playlist_manager = PlaylistManager(CONFIG['MUSIC_FOLDER'])
        self.point_system = PointSystem()
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
            channel = self.get_channel(CONFIG['VOICE_CHANNEL_ID'])
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
                file for file in os.listdir(CONFIG['CAT_IMAGES_FOLDER']) 
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))
            ]
            if cat_images:
                return os.path.join(CONFIG['CAT_IMAGES_FOLDER'], random.choice(cat_images))
        except FileNotFoundError:
            logger.error(f"Folder {CONFIG['CAT_IMAGES_FOLDER']} nie istnieje")
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
            if time_diff < CONFIG['SPAM_COOLDOWN']:
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

# Inicjalizacja bota
client = MusicBot()

# Komendy slash
@client.tree.command(name="points", description="Pokazuje liczbę Twoich punktów")
async def points_command(interaction: discord.Interaction):
    user_points = client.point_system.get_points(str(interaction.user.id))
    await interaction.response.send_message(
        f"💎 {interaction.user.mention} masz **{user_points}** punktów!"
    )

@client.tree.command(name="add", description="[ADMIN] Dodaje punkty użytkownikowi")
@app_commands.describe(member="Użytkownik do którego dodać punkty", points="Liczba punktów do dodania")
async def add_points_command(interaction: discord.Interaction, member: discord.Member, points: int):
    # Sprawdź uprawnienia
    if not any(role.name in ['Matt', 'Admin'] for role in interaction.user.roles):
        await interaction.response.send_message("❌ Nie masz uprawnień do tej komendy!", ephemeral=True)
        return
    
    if points <= 0:
        await interaction.response.send_message("❌ Liczba punktów musi być dodatnia!", ephemeral=True)
        return
    
    client.point_system.add_points(str(member.id), points)
    await interaction.response.send_message(f"✅ Dodano **{points}** punktów dla {member.display_name}!")

@client.tree.command(name="sub", description="[ADMIN] Odejmuje punkty użytkownikowi")
@app_commands.describe(member="Użytkownik od którego odjąć punkty", points="Liczba punktów do odjęcia")
async def sub_points_command(interaction: discord.Interaction, member: discord.Member, points: int):
    # Sprawdź uprawnienia
    if not any(role.name in ['Matt', 'Admin'] for role in interaction.user.roles):
        await interaction.response.send_message("❌ Nie masz uprawnień do tej komendy!", ephemeral=True)
        return
    
    if points <= 0:
        await interaction.response.send_message("❌ Liczba punktów musi być dodatnia!", ephemeral=True)
        return
    
    client.point_system.sub_points(str(member.id), points)
    await interaction.response.send_message(f"✅ Odjęto **{points}** punktów od {member.display_name}!")

@client.tree.command(name="reality", description="...")
async def reality_command(interaction: discord.Interaction):
    await interaction.response.send_message("🤔 Czy naprawdę możesz jeszcze cieszyć się rzeczywistością?")

@client.tree.command(name="sprytek", description="Wysyła losowe zdjęcie Sprytka!")
async def sprytek_command(interaction: discord.Interaction):
    # 1. Natychmiast odraczamy odpowiedź, aby uniknąć timeoutu.
    await interaction.response.defer() 

    
    cat_image = client._get_random_cat_image()
    
    if cat_image:
        try:
            with open(cat_image, 'rb') as file:
                discord_file = discord.File(file, filename=os.path.basename(cat_image))
                # 2. Używamy interaction.followup.send do wysłania właściwej odpowiedzi.
                await interaction.followup.send("🐱 Oto Sprytek!", file=discord_file)
        except Exception as e:
            logger.error(f"Błąd wysyłania zdjęcia: {e}")
            # Tutaj również używamy followup, na wypadek błędu po odroczeniu.
            await interaction.followup.send("❌ Wystąpił błąd przy wysyłaniu zdjęcia.", ephemeral=True)
    else:
        await interaction.followup.send("😿 Nie znaleziono zdjęć Sprytka.", ephemeral=True)

@client.tree.command(name="leaderboard", description="Pokazuje ranking punktów")
async def leaderboard_command(interaction: discord.Interaction):
    users_data = [(user_id, user.points) for user_id, user in client.point_system.users.items()]
    users_data.sort(key=lambda x: x[1], reverse=True)
    
    embed = discord.Embed(title="🏆 Ranking Punktów", color=0xFFD700)
    
    for i, (user_id, points) in enumerate(users_data[:10], 1):
        try:
            user = await client.fetch_user(int(user_id))
            name = user.display_name if hasattr(user, 'display_name') else user.name
        except:
            name = f"Użytkownik {user_id}"
        
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        embed.add_field(
            name=f"{medal} {name}",
            value=f"**{points}** punktów",
            inline=False
        )
    
    await interaction.response.send_message(embed=embed)

# Uruchomienie bota
if __name__ == "__main__":
    # Tutaj wstaw swój token bota
    TOKEN = ""  # Wstaw tutaj token bota
    
    if not TOKEN:
        logger.error("Brak tokenu bota! Ustaw token w zmiennej TOKEN")
    else:
        try:
            client.run(TOKEN)
        except Exception as e:
            logger.error(f"Błąd uruchamiania bota: {e}")