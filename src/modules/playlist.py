import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class PlaylistManager:
    def __init__(self, folder_path: str):
        self.folder_path = folder_path
        self.playlist = self._create_playlist()
    
    def _create_playlist(self):
        """Tworzy playlistę z plików w folderze."""
        try:
            files = os.listdir(self.folder_path)
            playlist = []
            for filename in files:
                file_path = os.path.join(self.folder_path, filename)
                if os.path.isfile(file_path) and filename.lower().endswith(('.mp3', '.wav', '.ogg', '.m4a')):
                    playlist.append(file_path)
            return playlist
        except FileNotFoundError:
            logger.error(f"Folder {self.folder_path} nie został znaleziony")
            return []
    
    def get_next_song(self):
        """Zwraca następny utwór i przenosi go na koniec listy."""
        if self.playlist:
            song = self.playlist.pop(0)
            self.playlist.append(song)
            return song
        return None
    
    def refresh_playlist(self):
        """Odświeża listę utworów z folderu."""
        self.playlist = self._create_playlist()
    
    def get_playlist_length(self) -> int:
        """Zwraca liczbę utworów w playliście."""
        return len(self.playlist)
    
    def get_current_song_name(self) -> Optional[str]:
        """Zwraca nazwę aktualnego utworu (pierwszy w kolejce)."""
        if self.playlist:
            return os.path.basename(self.playlist[0])
        return None