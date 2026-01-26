import logging
from typing import List, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .points import PointSystem

logger = logging.getLogger(__name__)

ACHIEVEMENTS = {
    'first_message': {
        'name': 'Początek',
        'description': 'Wysłanie pierwszej wiadomości',
        'emoji': '📝'
    },
    'points_100': {
        'name': 'Setka',
        'description': 'Zdobycie 100 punktów',
        'emoji': '💯'
    },
    'points_1000': {
        'name': 'Tysiąc',
        'description': 'Zdobycie 1000 punktów',
        'emoji': '🏅'
    },
    'points_10000': {
        'name': 'Dziesięć tysięcy',
        'description': 'Zdobycie 10000 punktów',
        'emoji': '🏆'
    },
    'first_meme': {
        'name': 'Obrazek',
        'description': 'Wysłanie obrazka na #memes',
        'emoji': '🖼️'
    },
    'used_sprytek': {
        'name': 'Sprytek lover',
        'description': 'Użycie komendy /sprytek',
        'emoji': '🐱'
    },
    'used_currentsong': {
        'name': 'Słuchacz',
        'description': 'Użycie komendy /currentsong',
        'emoji': '🎵'
    },
    'kuna': {
        'name': 'Kuna',
        'description': 'Napisanie "kuna"',
        'emoji': '🦝'
    },
    'jp2': {
        'name': '2137',
        'description': 'Wysłanie wiadomości o 21:37',
        'emoji': '🕘'
    }
}


class AchievementSystem:
    def __init__(self, point_system: 'PointSystem'):
        self.point_system = point_system

    def check_and_award_achievements(self, user_id: str) -> List[str]:
        """
        Sprawdza i przyznaje achievementy użytkownikowi.
        Zwraca listę nowo zdobytych achievementów.
        """
        user = self.point_system.get_user(user_id)
        new_achievements = []

        # Sprawdź achievementy punktowe
        if user.points >= 1 and 'first_message' not in user.achievements:
            new_achievements.append('first_message')

        if user.points >= 100 and 'points_100' not in user.achievements:
            new_achievements.append('points_100')

        if user.points >= 1000 and 'points_1000' not in user.achievements:
            new_achievements.append('points_1000')

        if user.points >= 10000 and 'points_10000' not in user.achievements:
            new_achievements.append('points_10000')

        # Sprawdź achievementy flagowe
        if user.flags.get('first_meme') and 'first_meme' not in user.achievements:
            new_achievements.append('first_meme')

        if user.flags.get('used_sprytek') and 'used_sprytek' not in user.achievements:
            new_achievements.append('used_sprytek')

        if user.flags.get('used_currentsong') and 'used_currentsong' not in user.achievements:
            new_achievements.append('used_currentsong')

        if user.flags.get('kuna') and 'kuna' not in user.achievements:
            new_achievements.append('kuna')

        if user.flags.get('jp2') and 'jp2' not in user.achievements:
            new_achievements.append('jp2')

        # Dodaj nowe achievementy
        for achievement_id in new_achievements:
            user.achievements.append(achievement_id)

        if new_achievements:
            self.point_system._save_users_data()

        return new_achievements

    def get_user_achievements(self, user_id: str) -> List[Dict]:
        """Zwraca listę achievementów użytkownika z pełnymi danymi."""
        user = self.point_system.get_user(user_id)
        result = []

        for achievement_id in user.achievements:
            if achievement_id in ACHIEVEMENTS:
                achievement_data = ACHIEVEMENTS[achievement_id].copy()
                achievement_data['id'] = achievement_id
                result.append(achievement_data)

        return result

    def get_all_achievements(self) -> Dict:
        """Zwraca słownik wszystkich dostępnych achievementów."""
        return ACHIEVEMENTS

    def set_flag(self, user_id: str, flag_name: str, value: bool = True):
        """Ustawia flagę dla użytkownika."""
        user = self.point_system.get_user(user_id)
        user.flags[flag_name] = value
        self.point_system._save_users_data()

    def get_flag(self, user_id: str, flag_name: str) -> bool:
        """Pobiera wartość flagi użytkownika."""
        user = self.point_system.get_user(user_id)
        return user.flags.get(flag_name, False)
