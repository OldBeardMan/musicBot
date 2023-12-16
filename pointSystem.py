class User:
    def __init__(self, user_id):
        self.user_id = user_id
        self.points = 0

class pointSystem:
    def __init__(self):
        self.users = {}

    def add_user(self, user_id):
        if user_id not in self.users:
            self.users[user_id] = User(user_id)

    def add_points(self, user_id, points):
        if user_id in self.users:
            self.users[user_id].points += points

    def get_points(self, user_id):
        if user_id in self.users:
            return self.users[user_id].points
        else:
            return 0