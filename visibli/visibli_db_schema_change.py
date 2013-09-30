import sqlite3


def shortcode_to_int(shortcode):
    return int.from_bytes(shortcode, byteorder='big', signed=False)


if __name__ == '__main__':
    old_db = sqlite3.connect('db/visibli.db')
    old_db.execute('PRAGMA journal_mode=WAL')

    new_db = sqlite3.connect('db/visibli_new.db')
    new_db.execute('PRAGMA journal_mode=WAL')
    new_db.execute('''CREATE TABLE IF NOT EXISTS visibli_hex
            (shortcode INTEGER PRIMARY KEY ASC, url TEXT, not_exist INTEGER)
            ''')

    rows = old_db.execute('SELECT * FROM visibli_hex')

    count = 0

    new_db.isolation_level = None
    new_db.execute('BEGIN')

    for row in rows:
        new_db.execute('INSERT INTO visibli_hex VALUES (?,?,?)',
            [shortcode_to_int(row[0]), row[1], row[2]]
        )

        if count and count % 500000 == 0:
            print('COMMIT')
            new_db.execute('COMMIT')
            new_db.execute('BEGIN')

        if count % 10000 == 0:
            print(count, row[0], shortcode_to_int(row[0]))

        count += 1

    new_db.execute('COMMIT')
