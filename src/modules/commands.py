import discord
from discord import app_commands
import os
import logging
import random
from typing import Optional

logger = logging.getLogger(__name__)

class CommandsMixin:
    """Mixin zawierający komendy slash bota."""
    
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

def setup_commands(client, config, point_system, achievement_system, playlist_manager):
    """Konfiguruje komendy slash dla bota."""
    
    @client.tree.command(name="points", description="Pokazuje liczbę Twoich punktów")
    async def points_command(interaction: discord.Interaction):
        user_points = point_system.get_points(str(interaction.user.id))
        await interaction.response.send_message(
            f"💎 {interaction.user.mention} masz **{user_points}** punktów!"
        )

    @client.tree.command(name="add", description="[ADMIN] Dodaje punkty użytkownikowi")
    @app_commands.describe(member="Użytkownik do którego dodać punkty", points="Liczba punktów do dodania")
    async def add_points_command(interaction: discord.Interaction, member: discord.Member, points: int):
        if not any(role.name in ['Matt', 'Admin'] for role in interaction.user.roles):
            await interaction.response.send_message("❌ Nie masz uprawnień do tej komendy!", ephemeral=True)
            return
        
        if points <= 0:
            await interaction.response.send_message("❌ Liczba punktów musi być dodatnia!", ephemeral=True)
            return
        
        point_system.add_points(str(member.id), points)
        await interaction.response.send_message(f"✅ Dodano **{points}** punktów dla {member.display_name}!")

    @client.tree.command(name="sub", description="[ADMIN] Odejmuje punkty użytkownikowi")
    @app_commands.describe(member="Użytkownik od którego odjąć punkty", points="Liczba punktów do odjęcia")
    async def sub_points_command(interaction: discord.Interaction, member: discord.Member, points: int):
        if not any(role.name in ['Matt', 'Admin'] for role in interaction.user.roles):
            await interaction.response.send_message("❌ Nie masz uprawnień do tej komendy!", ephemeral=True)
            return
        
        if points <= 0:
            await interaction.response.send_message("❌ Liczba punktów musi być dodatnia!", ephemeral=True)
            return
        
        point_system.sub_points(str(member.id), points)
        await interaction.response.send_message(f"✅ Odjęto **{points}** punktów od {member.display_name}!")

    @client.tree.command(name="reality", description="...")
    async def reality_command(interaction: discord.Interaction):
        await interaction.response.send_message("🤔 Czy naprawdę możesz jeszcze cieszyć się rzeczywistością?")

    @client.tree.command(name="sprytek", description="Wysyła losowe zdjęcie Sprytka!")
    async def sprytek_command(interaction: discord.Interaction):
        await interaction.response.defer()

        user_id = str(interaction.user.id)

        # Ustaw flagę used_sprytek
        if not achievement_system.get_flag(user_id, 'used_sprytek'):
            achievement_system.set_flag(user_id, 'used_sprytek', True)
            new_achievements = achievement_system.check_and_award_achievements(user_id)

        cat_image = client._get_random_cat_image()

        if cat_image:
            try:
                with open(cat_image, 'rb') as file:
                    discord_file = discord.File(file, filename=os.path.basename(cat_image))
                    await interaction.followup.send("🐱 Oto Sprytek!", file=discord_file)
            except Exception as e:
                logger.error(f"Błąd wysyłania zdjęcia: {e}")
                await interaction.followup.send("❌ Wystąpił błąd przy wysyłaniu zdjęcia.", ephemeral=True)
        else:
            await interaction.followup.send("😿 Nie znaleziono zdjęć Sprytka.", ephemeral=True)

    @client.tree.command(name="leaderboard", description="Pokazuje ranking punktów")
    async def leaderboard_command(interaction: discord.Interaction):
        users_data = point_system.get_leaderboard(10)

        embed = discord.Embed(title="🏆 Ranking Punktów", color=0xFFD700)

        for i, (user_id, points) in enumerate(users_data, 1):
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

    @client.tree.command(name="mattinfo", description="Informacje o Matt Krupa")
    async def mattinfo_command(interaction: discord.Interaction):
        embed = discord.Embed(
            title="Matt Krupa",
            description="Muzyk i kompozytor",
            color=0x7289DA,
            url="https://mattkrupa.net/"
        )
        embed.add_field(
            name="Muzyka",
            value="Ambient, elektroniczna i akustyczna muzyka. Czasem też wokalista.",
            inline=False
        )
        embed.add_field(
            name="Instrumenty",
            value="Gitara, bas, pianino i inne",
            inline=False
        )
        embed.add_field(
            name="Strona",
            value="[mattkrupa.net](https://mattkrupa.net/)",
            inline=False
        )
        await interaction.response.send_message(embed=embed)

    @client.tree.command(name="sprytekinfo", description="Informacje o Sprytku")
    async def sprytekinfo_command(interaction: discord.Interaction):
        embed = discord.Embed(
            title="Sprytek (2012-2026)",
            description="Ukochany kot Matta Krupy, wierny towarzysz i pomoc emocjonalna.",
            color=0x808080
        )
        embed.add_field(
            name="Daty",
            value="26.03.2012 - 23.01.2026",
            inline=True
        )
        embed.add_field(
            name="Wygląd",
            value="Biało-szaro-czarny, krótkowłosy",
            inline=True
        )
        embed.add_field(
            name="Pochodzenie",
            value="Mama z Chorwacji, ojciec nieznany",
            inline=False
        )
        embed.add_field(
            name="Osobowość",
            value="Sprytek był wspaniałym kotem i wiernym przyjacielem. "
                  "Służył jako pomoc emocjonalna dla Matta i wielu innych osób. "
                  "Uwielbiał przytulaski, grzanie innych swoim ciepłem "
                  "i uspokajające mruczenie dla tych, którzy tego potrzebowali.",
            inline=False
        )
        embed.set_footer(text="Na zawsze w naszych sercach")
        await interaction.response.send_message(embed=embed)

    @client.tree.command(name="achievements", description="Pokazuje Twoje zdobyte achievementy")
    async def achievements_command(interaction: discord.Interaction):
        from .achievements import ACHIEVEMENTS

        user_id = str(interaction.user.id)
        user_achievements = achievement_system.get_user_achievements(user_id)

        embed = discord.Embed(
            title=f"🏅 Achievementy - {interaction.user.display_name}",
            color=0xFFD700
        )

        if user_achievements:
            for achievement in user_achievements:
                embed.add_field(
                    name=f"{achievement['emoji']} {achievement['name']}",
                    value=achievement['description'],
                    inline=False
                )
        else:
            embed.description = "Nie masz jeszcze żadnych achievementów. Zacznij działać!"

        # Pokaż też ile achievementów zostało do zdobycia
        total_achievements = len(ACHIEVEMENTS)
        unlocked_achievements = len(user_achievements)
        embed.set_footer(text=f"Odblokowane: {unlocked_achievements}/{total_achievements}")

        await interaction.response.send_message(embed=embed)

    @client.tree.command(name="currentsong", description="Pokazuje aktualnie odtwarzany utwór")
    async def currentsong_command(interaction: discord.Interaction):
        user_id = str(interaction.user.id)

        # Ustaw flagę used_currentsong
        if not achievement_system.get_flag(user_id, 'used_currentsong'):
            achievement_system.set_flag(user_id, 'used_currentsong', True)
            achievement_system.check_and_award_achievements(user_id)

        current_song = playlist_manager.get_current_song_name()

        if current_song:
            # Usuń rozszerzenie pliku dla czytelności
            song_name = os.path.splitext(current_song)[0]

            embed = discord.Embed(
                title="🎵 Aktualnie gra",
                description=f"**{song_name}**",
                color=0x1DB954
            )
            embed.set_footer(text="Matt Krupa Radio")
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("🔇 Aktualnie nic nie jest odtwarzane.", ephemeral=True)