import os
from dotenv import load_dotenv

load_dotenv()


def _int(name: str, default: int = 0) -> int:
    v = os.getenv(name, "")
    return int(v) if v.strip().isdigit() else default


CONFIG = {
    'CAT_IMAGES_FOLDER': os.getenv('CAT_IMAGES_FOLDER', 'cat_images'),
    # SQLite file for pets and what the bot remembers about Long Kitten Nation
    'DATA_DB': os.getenv('DATA_DB', 'sprytek.sqlite'),

    # Long Kitten Nation (mc.mattkrupa.net). Leave LKN_BOT_SECRET empty to switch this off.
    'LKN_URL': os.getenv('LKN_URL', 'http://127.0.0.1:3100'),
    'LKN_BOT_SECRET': os.getenv('LKN_BOT_SECRET', ''),
    'LKN_GUILD_ID': _int('LKN_GUILD_ID'),
    # role for approved players
    'LKN_ROLE_ID': _int('LKN_ROLE_ID'),
    # channel for "welcome to Long Kitten Nation"
    'LKN_CHANNEL_ID': _int('LKN_CHANNEL_ID'),
    'LKN_SYNC_SECONDS': _int('LKN_SYNC_SECONDS', 60),
}

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
