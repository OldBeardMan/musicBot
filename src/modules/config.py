import os
from dotenv import load_dotenv

load_dotenv()

CONFIG = {
    'VOICE_CHANNEL_ID': int(os.getenv('VOICE_CHANNEL_ID', '0')),
    'CAT_IMAGES_FOLDER': os.getenv('CAT_IMAGES_FOLDER', 'cat_images'),
    'MUSIC_FOLDER': os.getenv('MUSIC_FOLDER', 'music'),
    'USERS_DATA_FILE': os.getenv('USERS_DATA_FILE', 'users_data.json'),
    'SPAM_COOLDOWN': int(os.getenv('SPAM_COOLDOWN', '3')),
    'MUSIC_BREAK': int(os.getenv('MUSIC_BREAK', '5')),
}

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')