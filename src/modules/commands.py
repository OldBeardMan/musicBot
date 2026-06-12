import discord
import os
import logging
import random
from typing import Optional

logger = logging.getLogger(__name__)


def _get_random_cat_image(config) -> Optional[str]:
    """Returns a random cat image."""
    try:
        cat_images = [
            file for file in os.listdir(config['CAT_IMAGES_FOLDER'])
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))
        ]
        if cat_images:
            return os.path.join(config['CAT_IMAGES_FOLDER'], random.choice(cat_images))
    except FileNotFoundError:
        logger.error(f"Folder {config['CAT_IMAGES_FOLDER']} does not exist")
    return None


def setup_commands(client, config):
    """Configures the bot's slash commands."""

    @client.tree.command(name="sprytek", description="Sends a random picture of Sprytek!")
    async def sprytek_command(interaction: discord.Interaction):
        await interaction.response.defer()

        cat_image = _get_random_cat_image(config)

        if cat_image:
            try:
                with open(cat_image, 'rb') as file:
                    discord_file = discord.File(file, filename=os.path.basename(cat_image))
                    await interaction.followup.send("It's me: ", file=discord_file)
            except Exception as e:
                logger.error(f"Error sending image: {e}")
                await interaction.followup.send("An error occurred while sending the image.", ephemeral=True)
        else:
            await interaction.followup.send("No pictures of Sprytek found.", ephemeral=True)

    @client.tree.command(name="mattinfo", description="Information about Matt Krupa")
    async def mattinfo_command(interaction: discord.Interaction):
        embed = discord.Embed(
            title="Matt Krupa",
            description="Musician and composer",
            color=0x7289DA,
            url="https://mattkrupa.net/"
        )
        embed.add_field(
            name="Music",
            value="Ambient, electronic and acoustic music. Sometimes a vocalist too.",
            inline=False
        )
        embed.add_field(
            name="Instruments",
            value="Guitar, bass, piano and more",
            inline=False
        )
        embed.add_field(
            name="Website",
            value="[mattkrupa.net](https://mattkrupa.net/)",
            inline=False
        )
        await interaction.response.send_message(embed=embed)

    @client.tree.command(name="sprytekinfo", description="Information about Sprytek")
    async def sprytekinfo_command(interaction: discord.Interaction):
        embed = discord.Embed(
            title="Sprytek (2012-2026)",
            description="Matt Krupa's beloved cat, a faithful companion and emotional support.",
            color=0x808080
        )
        embed.add_field(
            name="Dates",
            value="26.03.2012 - 23.01.2026",
            inline=True
        )
        embed.add_field(
            name="Appearance",
            value="White-grey-black, short-haired",
            inline=True
        )
        embed.add_field(
            name="Origin",
            value="Mother from Croatia, father unknown",
            inline=False
        )
        embed.add_field(
            name="Personality",
            value="Sprytek was a wonderful cat and a faithful friend. "
                  "He served as emotional support for Matt and many other people. "
                  "He loved cuddles, warming others with his warmth "
                  "and his soothing purring for those who needed it.",
            inline=False
        )
        embed.set_footer(text="Forever in our hearts")
        await interaction.response.send_message(embed=embed)
