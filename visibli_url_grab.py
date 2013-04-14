import base64
import html.parser
import http.client
import logging
import os
import random
import re
import sqlite3
import time


_logger = logging.getLogger(__name__)


class VisibliHexURLGrab(object):
    def __init__(self):
        self.db = sqlite3.connect('visibli.db')
        self.db.execute('PRAGMA journal_mode=WAL')

        with self.db:
            self.db.execute('''CREATE TABLE IF NOT EXISTS visibli_hex
            (shortcode BLOB PRIMARY KEY, url TEXT)
            ''')

        self.http_client = http.client.HTTPConnection('links.sharedby.co')
        self.throttle_time = 1

    def new_shortcode(self):
        while True:
            shortcode = os.urandom(3)

            rows = self.db.execute('SELECT 1 FROM visibli_hex WHERE '
                'shortcode = ? LIMIT 1', [shortcode])

            if not len(list(rows)):
                return shortcode

    def run(self):
        while True:
            self.fetch_url()
            time.sleep(random.uniform(0.1, 2))

    def fetch_url(self):
        shortcode = self.new_shortcode()
        shortcode_str = base64.b16encode(shortcode).lower().decode()
        path = '/links/{}'.format(shortcode_str)

        _logger.info('Begin fetch URL %s', path)

        self.http_client.request('GET', path)

        response = self.http_client.getresponse()

        url = self.read_response(response)

        if not url:
            _logger.debug('Got no url')
        else:
            self.add_url(shortcode, url)

        self.throttle(response.status)

    def read_response(self, response):
        _logger.debug('Got status %s %s', response.status, response.reason)

        data = response.read()
        assert isinstance(data, bytes)

        if response.status == 301:
            url = response.getheader('Location')
            return url
        elif response.status == 200:
            match = re.search(br'<iframe id="[^"]+" src="([^"]+)">', data)

            if not match:
                _logger.warning('No iframe found')
                return

            url = match.group(1).decode()
            url = html.parser.HTMLParser().unescape(url)

            return url

    def throttle(self, status_code):
        if 400 <= status_code <= 499 or 500 <= status_code <= 999:
            _logger.info('Throttle %d seconds', self.throttle_time)
            time.sleep(self.throttle_time)

            self.throttle_time *= 2
            self.throttle_time = min(3600, self.throttle_time)

    def add_url(self, shortcode, url):
        _logger.debug('Insert %s %s', shortcode, url)
        with self.db:
            self.db.execute('INSERT INTO visibli_hex VALUES (?, ?)',
                [shortcode, url])


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    o = VisibliHexURLGrab()
    o.run()
