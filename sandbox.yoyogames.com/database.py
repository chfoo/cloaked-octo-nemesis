'''Database helper'''
import dbm.gnu
import json
import shelve


class DB(object):
    def __init__(self):
        self.games_db = shelve.Shelf(
            dbm.gnu.open('games.db', 'cf'), writeback=True
        )
        self.users_db = shelve.Shelf(
            dbm.gnu.open('users.db', 'cf'), writeback=True
        )

    def add_user(self, username):
        if username not in self.users_db:
            self.users_db[username] = {}

    def add_game(self, game_id, title, slug):
        if game_id not in self.games_db:
            self.games_db[game_id] = {
                'title': title,
                'slug': slug,
            }

    def sync(self):
        self.games_db.sync()
        self.users_db.sync()


if __name__ == '__main__':
    db = DB()

    for key in db.games_db.keys():
        doc = dict(db.games_db[key])
        doc['id'] = key

        print(json.dumps(doc))

    for key in db.users_db.keys():
        doc = dict(db.users_db[key])
        doc['id'] = key

        print(json.dumps(doc))
