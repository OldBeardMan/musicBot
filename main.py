import sys
import os

# Add the src directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import logging
from modules.config import DISCORD_TOKEN
from modules.bot import SprytekBot

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the bot
client = SprytekBot()

# Run the bot
if __name__ == "__main__":
    if not DISCORD_TOKEN:
        logger.error("Missing bot token! Set DISCORD_TOKEN in the .env file")
        exit(1)
    else:
        try:
            client.run(DISCORD_TOKEN)
        except Exception as e:
            logger.error(f"Error starting the bot: {e}")
            exit(1)