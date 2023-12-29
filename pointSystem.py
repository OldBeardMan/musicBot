import json

class User:
    def __init__(self, user_id, points=0):
        self.user_id = user_id
        self.points = points

class PointSystem:
    def __init__(self, file_path="users_data.json"):
        self.file_path = file_path
        self.users = self.load_users_data()

    def load_users_data(self):
        try:
            with open(self.file_path, 'r') as file:
                data = json.load(file)
                users = {user_id: User(user_id, data[user_id]['points']) for user_id in data}
                return users
        except FileNotFoundError:
            return {}

    def save_users_data(self):
        data = {user_id: {'points': self.users[user_id].points} for user_id in self.users}
        with open(self.file_path, 'w') as file:
            json.dump(data, file, indent=4)

    def add_user(self, user_id):
        if user_id not in self.users:
            self.users[user_id] = User(user_id)
            self.save_users_data()

    def add_points(self, user_id, points):
        self.add_user(user_id)
        if user_id in self.users:
            self.users[user_id].points += points
            self.save_users_data()

    def get_points(self, user_id):
        self.add_user(user_id)
        if user_id in self.users:
            return self.users[user_id].points