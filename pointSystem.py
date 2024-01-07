import json

class User:
    def __init__(self, user_id, points=0):
        self.user_id = user_id
        self.points = points

class PointSystem:
    def __init__(self, file_path="users_data.json"):
        self.file_path = file_path
        self.users = self.load_users_data()

    def save_users_data(self):
        current_data = {user_id: self.users[user_id].points for user_id in self.users}
        with open(self.file_path, 'w') as file:
            json.dump(current_data, file, indent=4)

    def load_users_data(self):
        try:
            with open(self.file_path, 'r') as file:
                data = json.load(file)
                users = {user_id: User(user_id, points) for user_id, points in data.items()}
                return users
        except FileNotFoundError:
            return {}

    def add_user(self, user_id):
        if user_id not in self.users:
            self.users[user_id] = User(user_id)
            self.save_users_data()

    def add_points(self, user_id, points):
        self.add_user(user_id)
        if user_id in self.users:
            self.users[user_id].points += points
            self.save_users_data()

    def sub_points(self, user_id, points):
        self.add_user(user_id)
        if user_id in self.users:
            self.users[user_id].points -= points
            self.save_users_data()

    def get_points(self, user_id):
        self.add_user(user_id)
        if user_id in self.users:
            return self.users[user_id].points