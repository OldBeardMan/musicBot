import sys
import os

# Dodaj katalog src do ścieżki Python
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import logging
from modules.config import DISCORD_TOKEN
from modules.bot import MusicBot

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicjalizacja bota
client = MusicBot()

# Uruchomienie bota
if __name__ == "__main__":
    if not DISCORD_TOKEN:
        logger.error("Brak tokenu bota! Ustaw DISCORD_TOKEN w pliku .env")
        exit(1)
    else:
        try:
            client.run(DISCORD_TOKEN)
        except Exception as e:
            logger.error(f"Błąd uruchamiania bota: {e}")
            exit(1)