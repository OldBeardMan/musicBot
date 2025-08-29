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

def setup_commands(client, config, point_system):
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