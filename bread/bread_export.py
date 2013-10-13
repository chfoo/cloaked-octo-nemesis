'''Export db to urlteam format'''
# Copyright 2013 Christopher Foo <chris.foo@gmail.com>
# Licensed under GPLv3. See COPYING.txt for details.
import sqlite3
import base64
import argparse


ALPHABET = '0123456789abcdefghijklmnopqrstuvwxyz'
assert len(ALPHABET) == 36


# http://stackoverflow.com/a/1119769/1524507
def base36_encode(num, alphabet=ALPHABET):
    """Encode a number in Base X

    `num`: The number to encode
    `alphabet`: The alphabet to use for encoding
    """
    if (num == 0):
        return alphabet[0]
    arr = []
    base = len(alphabet)
    while num:
        rem = num % base
        num = num // base
        arr.append(alphabet[rem])
    arr.reverse()
    return ''.join(arr)


def base36_decode(string, alphabet=ALPHABET):
    """Decode a Base X encoded string into the number

    Arguments:
    - `string`: The encoded string
    - `alphabet`: The alphabet to use for encoding
    """
    base = len(alphabet)
    strlen = len(string)
    num = 0

    idx = 0
    for char in string:
        power = (strlen - (idx + 1))
        num += alphabet.index(char) * (base ** power)
        idx += 1

    return num


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('database')
    args = arg_parser.parse_args()

    db = sqlite3.connect(args.database)

    for row in db.execute('SELECT shortcode, url FROM bread '
    'WHERE URL IS NOT NULL ORDER BY shortcode ASC'):
        shortcode, url = row
        shortcode_str = base36_encode(shortcode).zfill(6)

        if '\r' in url or '\n' in url:
            raise Exception('{} contains newline'.format(url))

        print('{}|{}'.format(shortcode_str, url))

if __name__ == '__main__':
    main()
