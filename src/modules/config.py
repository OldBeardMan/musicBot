import os
from dotenv import load_dotenv

load_dotenv()

CONFIG = {
    'CAT_IMAGES_FOLDER': os.getenv('CAT_IMAGES_FOLDER', 'cat_images'),
}

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
