'''Grab Visibli hex shortcodes'''
# Copyright 2013 Christopher Foo <chris.foo@gmail.com>
# Licensed under GPLv3. See COPYING.txt for details.
import argparse
import base64
import collections
import gzip
import html.parser
import http.client
import logging
import logging.handlers
import math
import os
import queue
import random
import re
import sqlite3
import threading
import time


_logger = logging.getLogger(__name__)


class UnexpectedResult(ValueError):
    pass


class UserAgent(object):
    def __init__(self, filename):
        self.strings = []

        with open(filename, 'rt') as f:
            while True:
                line = f.readline().strip()

                if not line:
                    break

                self.strings.append(line)

        self.strings = tuple(self.strings)
        _logger.info('Initialized with %d user agents', len(self.strings))


class AbsSineyRateFunc(object):
    def __init__(self, avg_rate=1.0):
        self._avg_rate = avg_rate
        self._amplitude = 1.0 / self._avg_rate * 5.6
        self._x = 1.0

    def get(self):
        y = abs(self._amplitude * math.sin(self._x) * math.sin(self._x ** 2)
            / self._x)
        self._x += 0.05

        if self._x > 2 * math.pi:
            self._x = 1.0

        return y


class HTTPClientProcessor(threading.Thread):
    def __init__(self, request_queue, response_queue, host, port):
        threading.Thread.__init__(self)
        self.daemon = True
        self._request_queue = request_queue
        self._response_queue = response_queue
        self._http_client = http.client.HTTPConnection(host, port)

        self.start()

    def run(self):
        while True:
            path, headers, shortcode = self._request_queue.get()

            try:
                _logger.debug('Get %s %s', path, headers)
                self._http_client.request('GET', path, headers=headers)
                response = self._http_client.getresponse()
            except http.client.HTTPException:
                _logger.exception('Got an http error.')
                self._http_client.close()
                time.sleep(120)
            else:
                _logger.debug('Got response %s %s',
                    response.status, response.reason)
                data = response.read()
                self._response_queue.put((response, data, shortcode))


class VisibliHexURLGrab(object):
    def __init__(self, sequential=False, reverse_sequential=False,
    avg_items_per_sec=0.5, database_dir='', user_agent_filename=None,
    http_client_threads=2):
        self.db = sqlite3.connect(os.path.join(database_dir, 'visibli.db'))
        self.db.execute('PRAGMA journal_mode=WAL')

        with self.db:
            self.db.execute('''CREATE TABLE IF NOT EXISTS visibli_hex
            (shortcode BLOB PRIMARY KEY, url TEXT, not_exist INTEGER)
            ''')

        self.host = 'localhost'
        self.port = 8123
        self.request_queue = queue.Queue(maxsize=1)
        self.response_queue = queue.Queue(maxsize=10)
        self.http_clients = self.new_clients(http_client_threads)
        self.throttle_time = 1
        self.sequential = sequential
        self.reverse_sequential = reverse_sequential
        self.seq_num = 0xffffff if self.reverse_sequential else 0
        self.session_count = 0
        self.total_count = self.get_count() or 0
        self.user_agent = UserAgent(user_agent_filename)
        self.headers = {
            'Accept-Encoding': 'gzip',
            'Host': 'links.sharedby.co',
        }
        self.average_deque = collections.deque(maxlen=100)
        self.rate_func = AbsSineyRateFunc(avg_items_per_sec)
        self.miss_count = 0

    def new_clients(self, http_client_threads=2):
        return [HTTPClientProcessor(self.request_queue, self.response_queue,
            self.host, self.port)
            for dummy in range(http_client_threads)]

    def new_shortcode(self):
        while True:
            if self.sequential or self.reverse_sequential:
                s = '{:06x}'.format(self.seq_num)
                shortcode = base64.b16decode(s.encode(), casefold=True)

                if self.reverse_sequential:
                    self.seq_num -= 1

                    if self.seq_num < 0:
                        raise Exception('No more short codes')
                else:
                    self.seq_num += 1

                    if self.seq_num > 0xffffff:
                        raise Exception('No more short codes')
            else:
                shortcode = os.urandom(3)

            rows = self.db.execute('SELECT 1 FROM visibli_hex WHERE '
                'shortcode = ? LIMIT 1', [shortcode])

            if not len(list(rows)):
                return shortcode

    def run(self):
        self.check_proxy_tor()

        while True:
            self.read_responses()

            shortcode = self.new_shortcode()
            shortcode_str = base64.b16encode(shortcode).lower().decode()
            path = 'http://links.sharedby.co/links/{}'.format(shortcode_str)
            headers = self.get_headers()

            while True:
                try:
                    self.request_queue.put_nowait((path, headers, shortcode))
                except queue.Full:
                    self.read_responses()
                else:
                    break

            if self.session_count % 10 == 0:
                _logger.info('Session={}, total={}, {:.3f} u/s'.format(
                    self.session_count, self.session_count + self.total_count,
                    self.calc_avg()))

            t = self.rate_func.get()

            _logger.debug('Sleep {:.3f}'.format(t))
            time.sleep(t)

    def get_headers(self):
        d = dict(self.headers)
        d['User-Agent'] = random.choice(self.user_agent.strings)
        return d

    def read_responses(self):
        while True:
            try:
                response, data, shortcode = self.response_queue.get(block=True,
                    timeout=0.1)
            except queue.Empty:
                break

            self.session_count += 1

            try:
                url = self.read_response(response, data)
            except UnexpectedResult as e:
                _logger.warn('Unexpected result %s', e)
                self.throttle(None, force=True)
                continue

            if not url:
                self.add_no_url(shortcode)
                self.miss_count += 1
            else:
                self.add_url(shortcode, url)
                self.miss_count = 0

            shortcode_str = base64.b16encode(shortcode).lower().decode()

            _logger.info('%s->%s...', shortcode_str,
                url[:30] if url else '(none)')

            self.throttle(response.status)

    def read_response(self, response, data):
        if response.getheader('Content-Encoding') == 'gzip':
            _logger.debug('Got gzip data')
            data = gzip.decompress(data)

        if response.status == 301:
            url = response.getheader('Location')
            return url
        elif response.status == 200:
            match = re.search(br'<iframe id="[^"]+" src="([^"]+)">', data)

            if not match:
                raise UnexpectedResult('No iframe found')

            url = match.group(1).decode()
            url = html.parser.HTMLParser().unescape(url)

            return url
        elif response.status == 302:
            location = response.getheader('Location')

#            if location and 'sharedby' not in location \
#            and 'visibli' not in location:
            if location and location.startswith('http://yahoo.com'):
                raise UnexpectedResult(
                    'Weird 302 redirect to {}'.format(location))
            elif not location:
                raise UnexpectedResult('No redirect location')

            return
        else:
            raise UnexpectedResult('Unexpected status {}'.format(
                response.status))

    def throttle(self, status_code, force=False):
        if force or 400 <= status_code <= 499 or 500 <= status_code <= 999 \
        or self.miss_count > 2:
            _logger.info('Throttle %d seconds', self.throttle_time)
            time.sleep(self.throttle_time)

            self.throttle_time *= 2
            self.throttle_time = min(3600, self.throttle_time)
        else:
            self.throttle_time /= 2
            self.throttle_time = min(600, self.throttle_time)
            self.throttle_time = max(1, self.throttle_time)

    def add_url(self, shortcode, url):
        _logger.debug('Insert %s %s', shortcode, url)
        with self.db:
            self.db.execute('INSERT INTO visibli_hex VALUES (?, ?, ?)',
                [shortcode, url, None])

    def add_no_url(self, shortcode):
        _logger.debug('Mark no url %s', shortcode)
        with self.db:
            self.db.execute('INSERT INTO visibli_hex VALUES (?, ?, ?)',
                [shortcode, None, 1])

    def get_count(self):
        for row in self.db.execute('SELECT COUNT(ROWID) FROM visibli_hex '
        'LIMIT 1'):
            return int(row[0])

    def calc_avg(self):
        self.average_deque.append((self.session_count, time.time()))

        try:
            avg = ((self.session_count - self.average_deque[0][0])
                / (time.time() - self.average_deque[0][1]))
        except ArithmeticError:
            avg = 0

        return avg

    def check_proxy_tor(self):
        http_client = http.client.HTTPConnection(self.host, self.port)
        http_client.request('GET', 'http://check.torproject.org/',
            headers={'Host': 'check.torproject.org'})

        response = http_client.getresponse()
        data = response.read()
        _logger.debug('Check proxy got data=%s', data.decode())

        if response.status != 200:
            raise UnexpectedResult('Check tor page returned %d',
                response.status)

        if b'Congratulations. Your browser is configured to use Tor.' \
        not in data:
            raise UnexpectedResult('Not configured to use tor')

        _logger.info('Using tor proxy')

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--sequential', action='store_true')
    arg_parser.add_argument('--reverse-sequential', action='store_true')
    arg_parser.add_argument('--average-rate', type=float, default=1.0)
    arg_parser.add_argument('--quiet', action='store_true')
    arg_parser.add_argument('--database-dir', default=os.getcwd())
    arg_parser.add_argument('--log-dir', default=os.getcwd())
    arg_parser.add_argument('--user-agent-file',
        default=os.path.join(os.getcwd(), 'user-agents.txt'))
    arg_parser.add_argument('--threads', type=int, default=2)
    args = arg_parser.parse_args()

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    if not args.quiet:
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        console.setFormatter(
            logging.Formatter('%(levelname)s %(message)s'))
        root_logger.addHandler(console)

    log_filename = os.path.join(args.log_dir, 'visibli_url_grab.log')
    file_log = logging.handlers.RotatingFileHandler(log_filename,
        maxBytes=1048576, backupCount=9)
    file_log.setLevel(logging.DEBUG)
    file_log.setFormatter(logging.Formatter(
        '%(asctime)s %(name)s:%(lineno)d %(levelname)s %(message)s'))
    root_logger.addHandler(file_log)

    o = VisibliHexURLGrab(sequential=args.sequential,
        reverse_sequential=args.reverse_sequential,
        database_dir=args.database_dir,
        avg_items_per_sec=args.average_rate,
        user_agent_filename=args.user_agent_file,
        http_client_threads=args.threads)
    o.run()
