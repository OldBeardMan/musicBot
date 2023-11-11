import discord
from discord.ext import commands
import youtube_dl

intents = discord.Intents.all()  # To ustawienie obejmuje wszystkie intencje, ale możesz dostosować je do swoich potrzeb

bot = commands.Bot(command_prefix='>', intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

@bot.command(name='play')
async def play_music(ctx, url):
    # Sprawdź, czy bot jest podłączony do kanału głosowego
    if not ctx.message.author.voice:
        await ctx.send("Nie jesteś połączony z kanałem głosowym.")
        return

    channel = ctx.message.author.voice.channel
    voice_channel = await channel.connect()

    # Ustawienia dla youtube_dl
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }],
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        url2 = info['formats'][0]['url']
        voice_channel.play(discord.FFmpegPCMAudio(url2), after=lambda e: print('done', e))
    
    await ctx.send(f'Odtwarzam muzykę z: {url}')

@bot.command(name='stop')
async def stop_music(ctx):
    # Wyjdź z kanału głosowego
    await discord.VoiceClient.disconnect(ctx.voice_client)

# Uruchom bota
bot.run('token')