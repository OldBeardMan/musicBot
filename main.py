import discord
from discord.ext import tasks
from discord import app_commands
import asyncio
import os
import forPlaylist
import random
from pointSystem import PointSystem       


playlist = forPlaylist.create('music')

cat_images_folder = 'cat_images'

last_message_times = {}

point_system = PointSystem()

def get_random_cat_image():
    cat_images = [file for file in os.listdir(cat_images_folder) if file.endswith(('.png', '.jpg', '.jpeg'))]

    if cat_images:
        random_cat_image = random.choice(cat_images)
        return os.path.join(cat_images_folder, random_cat_image)
    else:
        return None

class aclient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.all())
        self.synced = False

    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:
            await tree.sync()
            self.synced = True
        print(f'Logged in as {self.user}')
        await self.change_presence(activity=discord.Game(name='Matt Krupa'))
        channel_id = 1173158666174742538
        channel = self.get_channel(channel_id)
        await channel.connect()
        print("Bot is ready.")
        background_music.start()
        
client = aclient()
tree = app_commands.CommandTree(client) 


async def play_music():
    while playlist:
        file_path = playlist.pop(0)
        if os.path.isfile(file_path):
            channel = client.voice_clients[0].channel
            voice_channel = discord.utils.get(client.voice_clients, guild=channel.guild)

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
    if not client.voice_clients:
        print("Bot is not in a voice channel.")
        return

    print("Checking for music...")
    await play_music()



#CHATBOT AND LEVELING UP
@client.event
async def on_message(message):
    input_points = point_system.get_points(str(message.author.id))
    meme = False
    channel = message.channel
    current_time = message.created_at.timestamp()

    role = discord.utils.find(lambda r: r.name == 'Bots', message.guild.roles)
    if role in message.author.roles:
        return

    image_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    if any(attachment.filename.lower().endswith(tuple(image_extensions)) for attachment in message.attachments):
        meme = True

    if message.author.id in last_message_times:
        time_difference = current_time - last_message_times[message.author.id]

        if time_difference < 1:
            await message.respond(f"{message.author.mention}, DO NOT SPAM!")
            return

    last_message_times[message.author.id] = current_time

    if channel.name == 'memes' and meme:
        point_system.add_points(str(message.author.id), 5)
    else:
        point_system.add_points(str(message.author.id), 1)


    keyword_responses = {
        "kuna": "kuna",
        "matt": "If you want to know more about Matt check out: https://mattkrupa.net/",
        "sprytek": "It's me!",
        "sus": "amogus"
    }

    for keyword, response in keyword_responses.items():
        if keyword.lower() in message.content.lower():
            await message.respond(response)
            break
    
    lvl1 = discord.utils.get(message.guild.roles, name="printer")
    lvl2 = discord.utils.get(message.guild.roles, name="Autumn Wanderer")
    lvl3 = discord.utils.get(message.guild.roles, name="Do-Not-Listener")
    lvl4 = discord.utils.get(message.guild.roles, name="Winter Gifter")
    lvl5 = discord.utils.get(message.guild.roles, name="Nordic Mountaineer")
    lvl6 = discord.utils.get(message.guild.roles, name="Icelandic Fugitive")
    lvl7 = discord.utils.get(message.guild.roles, name="The Matt Devotee")

    if point_system.get_points(str(message.author.id)) >= 10 and input_points < 10:
        await message.author.add_roles(lvl1)
        await message.channel.send(f"{message.author.mention} have achived level 1 role: printer!")
    elif point_system.get_points(str(message.author.id)) >= 100 and input_points < 100:
        await message.author.add_roles(lvl2)
        await message.channel.send(f"{message.author.mention} have achived level 2 role: Autumn Wanderer!")
    elif point_system.get_points(str(message.author.id)) >= 500 and input_points < 500:
        await message.author.add_roles(lvl3)
        await message.channel.send(f"{message.author.mention} have achived level 3 role: Do-Not-Listener!")
    elif point_system.get_points(str(message.author.id)) >= 2500 and input_points < 2500:
        await message.author.add_roles(lvl4)
        await message.channel.send(f"{message.author.mention} have achived level 4 role: Winter Gifter!")
    elif point_system.get_points(str(message.author.id)) >= 10000 and input_points < 10000:
        await message.author.add_roles(lvl5)
        await message.channel.send(f"{message.author.mention} have achived level 5 role: Nordic Mountaineer!")
    elif point_system.get_points(str(message.author.id)) >= 100000 and input_points < 100000:
        await message.author.add_roles(lvl6)
        await message.channel.send(f"{message.author.mention} have achived level 6 role: Icelandic Fugitive!")
    elif point_system.get_points(str(message.author.id)) >= 1000000 and input_points < 1000000:
        await message.author.add_roles(lvl7)
        await message.channel.send(f"{message.author.mention} have achived the hightest level role: The Matt Devotee!")
        await message.channel.send(f"{message.author.mention} just sent theirs millionth message!!! MAD")


@tree.command(
    name="points",
    description="Shows you how many points you have!",
)
async def points(ctx):
    await ctx.respond(f"User {ctx.author.mention} has {point_system.get_points(str(ctx.author.id))} points!")


@tree.command(
    name="add",
    description="Adding points, accesible only by the admins!",
)
async def add(ctx, member: discord.Member, p: int):
    role = discord.utils.find(lambda r: r.name == 'Matt', ctx.guild.roles) 
    if role in ctx.author.roles:
        point_system.add_points(str(member.id), p)
        await ctx.respond(f"Added {p} points to {member.display_name}!")
    else:
        await ctx.respond("NIE DLA PSA!")

@tree.command(
    name="sub",
    description="Substract points.",
)
async def sub(ctx, member: discord.Member, p: int):
    role = discord.utils.find(lambda r: r.name == 'Matt', ctx.guild.roles) 
    if role in ctx.author.roles:
        point_system.sub_points(str(member.id), p)
        await ctx.respond(f"Subtracted {p} points from {member.display_name}!")
    else:
        await ctx.respond("You do not have permissions to use this command!")


#SHITPOSTKOMENDY
@tree.command(
    name="reality",
    description="...",
)
async def reality(ctx):
    await ctx.respond("Can you really enjoy reality anymore?")

@tree.command(
    name="sprytek",
    description="Sends you a random picture of Sprytek!",
)
async def sprytek(interaction: discord.Interaction):
    cat_image = get_random_cat_image()
    
    if cat_image:
        with open(cat_image, 'rb') as file:
            await interaction.response.send_message(file=discord.File(file))
    else:
        await interaction.response.send_message("Nie znaleziono żadnych zdjęć kota.")




# Uruchom bota
client.run('')