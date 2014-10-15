from database import DB
import urllib.parse


def main():
    db = DB()
    
    gen_users(db)
    gen_games(db)


def gen_users(db):
    for key in db.users_db.keys():
        print('http://sandbox.yoyogames.com/users/{}'.format(urllib.parse.quote(key)))


def gen_games(db):
    for key in db.games_db.keys():
        doc = db.games_db[key]
        print('http://sandbox.yoyogames.com/games/{}'.format(doc['slug']))
        print('http://sandbox.yoyogames.com/games/{}/download'.format(key))
        print('http://chfoo-d1.mooo.com:8000/?id={}'.format(key))


if __name__ == '__main__':
    main()