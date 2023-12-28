import discord
from discord.ext import commands, tasks
import asyncio
import os
import forPlaylist
import random
from pointSystem import pointSystem

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='>', intents=intents)

playlist = forPlaylist.create('music')

cat_images_folder = 'cat_images'

point_system = pointSystem()

def get_random_cat_image():
    cat_images = [file for file in os.listdir(cat_images_folder) if file.endswith(('.png', '.jpg', '.jpeg'))]

    if cat_images:
        random_cat_image = random.choice(cat_images)
        return os.path.join(cat_images_folder, random_cat_image)
    else:
        return None



#RADIO
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

            voice_channel.play(discord.FFmpegPCMAudio(file_path), after=lambda e: print('done', e))

            while voice_channel.is_playing():
                await asyncio.sleep(1)

            playlist.append(file_path)

            await asyncio.sleep(5)
        else:
            print(f"File not found: {file_path}")
            await asyncio.sleep(1)
            playlist.append(file_path)

@tasks.loop(seconds=5)
async def background_music():
    if not bot.voice_clients:
        print("Bot is not in a voice channel.")
        return

    print("Checking for music...")
    await play_music()



#CHATBOT
@bot.event
async def on_message(message):
    await bot.process_commands(message)
    if message.author == bot.user:
        return
    
    keyword_responses = {
        "kuna": "kuna",
        "matt": "If you want to know more about Matt check out: https://mattkrupa.net/",
        "sprytek": "It's me!"
    }

    for keyword, response in keyword_responses.items():
        if keyword in message.content:
            await message.channel.send(response)
            break


#SHITPOSTKOMENDY
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





# Uruchom bota
bot.run('')