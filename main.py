import discord
from discord.ext import commands, tasks
import asyncio
import os
import forPlaylist
import random

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='>', intents=intents)

playlist = forPlaylist.create('music')

cat_images_folder = 'cat_images'

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    await bot.change_presence(activity=discord.Game(name='Matt Krupa'))
    channel_id = 1173158666174742538
    channel = bot.get_channel(channel_id)
    await channel.connect()
    print("Bot is ready.")
    background_music.start()

async def play_music():
    while playlist:
        file_path = playlist.pop(0)
        if os.path.isfile(file_path):
            channel = bot.voice_clients[0].channel
            voice_channel = discord.utils.get(bot.voice_clients, guild=channel.guild)

            print(f"Attempting to play: {file_path}")

            # Odtwarzaj utwór
            voice_channel.play(discord.FFmpegPCMAudio(file_path), after=lambda e: print('done', e))

            # Poczekaj do zakończenia odtwarzania aktualnego utworu
            while voice_channel.is_playing():
                await asyncio.sleep(1)

            # Po zakończeniu utworu, dodaj go z powrotem do playlisty
            playlist.append(file_path)

            # Odczekaj chwilę przed sprawdzeniem następnego utworu
            await asyncio.sleep(5)
        else:
            print(f"File not found: {file_path}")
            await asyncio.sleep(1)
            playlist.append(file_path)

@tasks.loop(seconds=5)
async def background_music():
    # Sprawdź, czy bot jest w kanałach głosowych
    if not bot.voice_clients:
        print("Bot is not in a voice channel.")
        return

    print("Checking for music...")
    # Odtwarzaj muzykę
    await play_music()

@bot.command(name='reality')
async def reality(ctx):
    await ctx.send("Can you really enjoy reality anymore?")

@bot.command(name='sprytek')
async def sprytek(ctx):
    cat_image = get_random_cat_image()
    
    if cat_image:
        with open(cat_image, 'rb') as file:
            await ctx.send(file=discord.File(file))
    else:
        await ctx.send("Nie znaleziono żadnych zdjęć kota.")

def get_random_cat_image():
    cat_images = [file for file in os.listdir(cat_images_folder) if file.endswith(('.png', '.jpg', '.jpeg'))]

    if cat_images:
        random_cat_image = random.choice(cat_images)
        return os.path.join(cat_images_folder, random_cat_image)
    else:
        return None

# Uruchom bota
bot.run('')