import json
import logging
from typing import Dict

logger = logging.getLogger(__name__)

class User:
    def __init__(self, user_id: str, points: int = 0):
        self.user_id = user_id
        self.points = points

class PointSystem:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.users = self._load_users_data()
    
    def _save_users_data(self):
        """Zapisuje dane użytkowników do pliku JSON."""
        try:
            current_data = {user_id: self.users[user_id].points for user_id in self.users}
            with open(self.file_path, 'w') as file:
                json.dump(current_data, file, indent=4)
        except Exception as e:
            logger.error(f"Błąd przy zapisywaniu danych: {e}")
    
    def _load_users_data(self) -> Dict[str, User]:
        """Ładuje dane użytkowników z pliku JSON."""
        try:
            with open(self.file_path, 'r') as file:
                data = json.load(file)
                users = {user_id: User(user_id, points) for user_id, points in data.items()}
                return users
        except FileNotFoundError:
            logger.info("Plik z danymi użytkowników nie istnieje, tworzę nowy")
            return {}
        except Exception as e:
            logger.error(f"Błąd przy ładowaniu danych: {e}")
            return {}
    
    def add_user(self, user_id: str):
        """Dodaje nowego użytkownika jeśli nie istnieje."""
        if user_id not in self.users:
            self.users[user_id] = User(user_id)
            self._save_users_data()
    
    def add_points(self, user_id: str, points: int):
        """Dodaje punkty użytkownikowi."""
        self.add_user(user_id)
        self.users[user_id].points += points
        self._save_users_data()
    
    def sub_points(self, user_id: str, points: int):
        """Odejmuje punkty użytkownikowi (z zabezpieczeniem przed ujemnymi punktami)."""
        self.add_user(user_id)
        new_points = max(0, self.users[user_id].points - points)
        self.users[user_id].points = new_points
        self._save_users_data()
    
    def get_points(self, user_id: str) -> int:
        """Zwraca liczbę punktów użytkownika."""
        self.add_user(user_id)
        return self.users[user_id].points
    
    def get_leaderboard(self, limit: int = 10):
        """Zwraca ranking użytkowników."""
        users_data = [(user_id, user.points) for user_id, user in self.users.items()]
        users_data.sort(key=lambda x: x[1], reverse=True)
        return users_data[:limit]