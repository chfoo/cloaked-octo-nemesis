'''Scrape listing of all games on sandbox.yoyogames.com.'''
import random
import requests
import time
import urllib.parse

import lxml.html

from database import DB


def main():
    db = DB()

    start_page = 1
    end_page = 3955
    url = 'http://sandbox.yoyogames.com/browse?page={0}&sort=created_at'
    scrape(db, start_page, end_page, url)

    start_page = 1
    end_page = 528
    url = 'http://sandbox.yoyogames.com/browse?beta=1&page={0}&sort=created_at'

    scrape(db, start_page, end_page, url)

    start_page = 1
    end_page = 1015
    url = 'http://sandbox.yoyogames.com/browse?incomplete=1&page={0}&sort=created_at'

    scrape(db, start_page, end_page, url)


def scrape(db, start_page, end_page, url):
    for page in range(start_page, end_page + 1):
        print('Fetching', page)
        response = requests.get(url.format(page),
            headers={'Accept-Encoding': 'gzip'})

        tree = lxml.html.fromstring(response.text)

        for element in tree.iterfind('.//li'):
            for a_element in element.iterfind('.//a'):
                link = a_element.get('href', '')

                if link.startswith('/games/'):
                    slug = link.replace('/games/', '')
                    game_id = slug.split('-', 1)[0]
                    title = a_element.get('title')

                    print(game_id, title, slug)
                    db.add_game(game_id, title, slug)

                elif link.startswith('/users/'):
                    username = urllib.parse.unquote(
                        link.replace('/users/', '')
                    )

                    print(username)
                    db.add_user(username)

#         input('pause')
        db.sync()
        time.sleep(random.uniform(0.0, 0.5))

if __name__ == '__main__':
    main()
