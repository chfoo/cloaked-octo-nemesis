'''Export db to urlteam format'''
# Copyright 2013 Christopher Foo <chris.foo@gmail.com>
# Licensed under GPLv3. See COPYING.txt for details.
import sqlite3
import base64
import argparse


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('database')
    args = arg_parser.parse_args()

    db = sqlite3.connect(args.database)

    for row in db.execute('SELECT shortcode, url FROM visibli_hex '
    'WHERE URL IS NOT NULL ORDER BY shortcode ASC'):
        shortcode, url = row
        shortcode_str = base64.b16encode(
            shortcode.to_bytes(3, byteorder='big', signed=False)
            ).decode().lower()

        if '\r' in url or '\n' in url:
            raise Exception('{} contains newline'.format(url))

        print('{}|{}'.format(shortcode_str, url))

if __name__ == '__main__':
    main()
