'''Grab bre.ad shortcodes'''
# Copyright 2013 Christopher Foo <chris.foo@gmail.com>
# Licensed under GPLv3. See COPYING.txt for details.
import argparse
import atexit
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
import urllib.parse


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
        connection_time = time.time()
        expire_time = connection_time + 1800

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
                _logger.debug('Read %s bytes', len(data))
                self._response_queue.put((response, data, shortcode))

            current_time = time.time()

            if expire_time < current_time:
                connection_time = current_time
                expire_time = current_time + 1800
                _logger.debug('Close connection.')
                self._http_client.close()
            else:
                _logger.debug(
                    'Conn time {}, expire time {}, now time {}'.format(
                    connection_time, expire_time, current_time))


class InsertQueue(threading.Thread):
    def __init__(self, db_path):
        threading.Thread.__init__(self)
        self.daemon = True
        self._queue = queue.Queue(maxsize=1000)
        self._event = threading.Event()
        self._running = True
        self._db_path = db_path

        self.start()

    def run(self):
        self._db = sqlite3.connect(self._db_path)

        while self._running:
            self._process()
            self._event.wait(timeout=10)

    def _process(self):
        with self._db:
            while True:
                try:
                    statement, values = self._queue.get_nowait()
                except queue.Empty:
                    break

                _logger.debug('Executing statement')
                self._db.execute(statement, values)

    def stop(self):
        self._running = False
        self._event.set()

    def add(self, statement, values):
        self._queue.put((statement, values))


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


class BreadURLGrab(object):
    def __init__(self, sequential=False, reverse_sequential=False,
    avg_items_per_sec=0.5, database_dir='', user_agent_filename=None,
    http_client_threads=2, save_reports=False):
        db_path = os.path.join(database_dir, 'bread.db')
        self.database_dir = database_dir
        self.db = sqlite3.connect(db_path)
        self.db.execute('PRAGMA journal_mode=WAL')

        with self.db:
            self.db.execute('''CREATE TABLE IF NOT EXISTS bread
            (shortcode INTEGER PRIMARY KEY ASC, url TEXT, not_exist INTEGER)
            ''')

        self.host = 'bre.ad'
        self.port = 80
        self.tor_host = 'localhost'
        self.tor_port = 8118
        self.save_reports = save_reports
        self.request_queue = queue.Queue(maxsize=2)
        self.tor_request_queue = queue.Queue(maxsize=2)
        self.response_queue = queue.Queue(maxsize=25)

        # Adjust for tor if needed
        self.http_clients = self.new_clients(http_client_threads)
        self.http_tor_clients = self.new_tor_clients(0)

        self.throttle_time = 1
        self.sequential = sequential
        self.reverse_sequential = reverse_sequential
        self.max_seq_num = base36_decode('1zzzzz')
        self.seq_num = self.max_seq_num if self.reverse_sequential else 0
        self.session_count = 0
        #self.total_count = self.get_count() or 0
        self.total_count = 0
        self.user_agent = UserAgent(user_agent_filename)
        self.headers = {
            'Accept-Encoding': 'gzip',
        }
        self.average_deque = collections.deque(maxlen=100)
        self.rate_func = AbsSineyRateFunc(avg_items_per_sec)
        self.miss_count = 0
        self.hit_count = 0
        self.insert_queue = InsertQueue(db_path)

        self.do_first_queue = queue.Queue()
        self.load_do_first()

        atexit.register(self.insert_queue.stop)

    def load_do_first(self):
        with open('do_first.txt', 'tr') as f:
            for line in f:
                line = line.strip()

                if line:
                    self.do_first_queue.put(line)

    def new_clients(self, http_client_threads=2):
        return [HTTPClientProcessor(self.request_queue, self.response_queue,
            self.host, self.port)
            for dummy in range(http_client_threads)]

    def new_tor_clients(self, http_client_threads=2):
        return [HTTPClientProcessor(
            self.tor_request_queue,
            self.response_queue,
            self.tor_host,
            self.tor_port)
            for dummy in range(http_client_threads)]

    def shortcode_to_int(self, shortcode):
        return base36_decode(shortcode.lstrip('0'))

    def new_shortcode(self):
        while True:
            try:
                do_first_shortcode = self.do_first_queue.get_nowait()
            except queue.Empty:
                do_first_shortcode = None

            if do_first_shortcode:
                shortcode = do_first_shortcode
            elif self.sequential or self.reverse_sequential:
                shortcode = base36_encode(self.seq_num).zfill(6)
                assert len(shortcode) == 6

                if self.reverse_sequential:
                    self.seq_num -= 1

                    if self.seq_num < 0:
                        return None
                else:
                    self.seq_num += 1

                    if self.seq_num > self.max_seq_num:
                        return None
            else:
                shortcode = base36_encode(
                    random.randint(0, self.max_seq_num)).zfill(6)

            rows = self.db.execute('SELECT 1 FROM bread WHERE '
                'shortcode = ? LIMIT 1', [self.shortcode_to_int(shortcode)])

            if not len(list(rows)):
                return shortcode

    def run(self):
        # Adjust for tor if needed
#         self.check_proxy_tor()

        while True:
            if not self.insert_queue.is_alive():
                raise Exception('Insert queue died!')

            shortcode = self.new_shortcode()

            if shortcode is None:
                break

            url = 'http://bre.ad/{}/go/{}'.format(shortcode,
                random.randint(10000, 1000000))
            headers = self.get_headers()

            # Adjust for tor if needed
            if False:  # random.randint(1, 4) == 1:
                request_queue = self.tor_request_queue
                path = url
            else:
                request_queue = self.request_queue
                path = urllib.parse.urlparse(url).path

            while True:
                try:
                    request_queue.put_nowait((path, headers, shortcode))
                except queue.Full:
                    self.read_responses()
                else:
                    break

            if self.session_count % 10 == 0:
                _logger.info('Session={}, hit={}, total={}, {:.3f} u/s'.format(
                    self.session_count, self.hit_count,
                    self.session_count + self.total_count,
                    self.calc_avg()))

            t = self.rate_func.get()

            _logger.debug('Sleep {:.3f}'.format(t))
            time.sleep(t)

            self.read_responses()

        _logger.info('Shutting down...')
        time.sleep(30)
        self.read_responses()
        self.insert_queue.stop()
        self.insert_queue.join()

    def get_headers(self):
        d = dict(self.headers)
        d['User-Agent'] = random.choice(self.user_agent.strings)
        return d

    def read_responses(self):
        while True:
            try:
                response, data, shortcode = self.response_queue.get(block=True,
                    timeout=0.001)
            except queue.Empty:
                break

            self.session_count += 1

            try:
                url = self.read_response(response, data)
            except UnexpectedResult as e:
                _logger.warn('Unexpected result %s', e)

                if self.save_reports:
                    try:
                        self.write_report(e, shortcode, response, data)
                    except:
                        _logger.exception('Error writing report')

                self.throttle(None, force=True)
                continue

            if not url:
                self.add_no_url(shortcode)
                self.miss_count += 1
            else:
                self.add_url(shortcode, url)
                self.miss_count = 0
                self.hit_count += 1

            _logger.info('%s->%s...', shortcode,
                url[:30] if url else '(none)')

            self.throttle(response.status)

    def read_response(self, response, data):
        if response.getheader('Content-Encoding') == 'gzip':
            _logger.debug('Got gzip data')
            data = gzip.decompress(data)

        if response.status == 302:
            url = response.getheader('Location')
            return url
        elif response.status in (204, 404):
            return
        else:
            raise UnexpectedResult('Unexpected status {}'.format(
                response.status))

    def throttle(self, status_code, force=False):
        if force or (400 <= status_code <= 499 and status_code != 404) \
        or 500 <= status_code <= 999 \
        or self.miss_count > 10000000:
            _logger.info('Throttle %d seconds', self.throttle_time)
            time.sleep(self.throttle_time)

            self.throttle_time *= 1.2
            self.throttle_time = min(3600, self.throttle_time)
        else:
            self.throttle_time /= 2
            self.throttle_time = min(600, self.throttle_time)
            self.throttle_time = max(1, self.throttle_time)

    def add_url(self, shortcode, url):
        _logger.debug('Insert %s %s', shortcode, url)
        self.insert_queue.add('INSERT OR IGNORE INTO bread VALUES (?, ?, ?)',
            [self.shortcode_to_int(shortcode), url, None])

    def add_no_url(self, shortcode):
        _logger.debug('Mark no url %s', shortcode)
        self.insert_queue.add('INSERT OR IGNORE INTO bread VALUES (?, ?, ?)',
            [self.shortcode_to_int(shortcode), None, 1])

    def get_count(self):
        for row in self.db.execute('SELECT COUNT(ROWID) FROM bread '
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
        http_client = http.client.HTTPConnection(self.tor_host, self.tor_port)
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

    def write_report(self, error, shortcode_str, response, data):
        path = os.path.join(self.database_dir,
            'report_{:.04f}'.format(time.time()))
        _logger.debug('Writing report to %s', path)

        with open(path, 'wt') as f:
            f.write('Error ')
            f.write(str(error))
            f.write('\n')
            f.write('Code ')
            f.write(shortcode_str)
            f.write('\n')
            f.write(str(response.status))
            f.write(response.reason)
            f.write('\n')
            f.write(str(response.getheaders()))
            f.write('\n\nData\n\n')
            f.write(str(data))
            f.write('\n\nEnd Report\n')


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--sequential', action='store_true')
    arg_parser.add_argument('--reverse-sequential', action='store_true')
    arg_parser.add_argument('--save-reports', action='store_true')
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

    log_filename = os.path.join(args.log_dir, 'bread_url_grab.log')
    file_log = logging.handlers.RotatingFileHandler(log_filename,
        maxBytes=1048576, backupCount=9)
    file_log.setLevel(logging.DEBUG)
    file_log.setFormatter(logging.Formatter(
        '%(asctime)s %(name)s:%(lineno)d %(levelname)s %(message)s'))
    root_logger.addHandler(file_log)

    o = BreadURLGrab(sequential=args.sequential,
        reverse_sequential=args.reverse_sequential,
        database_dir=args.database_dir,
        avg_items_per_sec=args.average_rate,
        user_agent_filename=args.user_agent_file,
        http_client_threads=args.threads,
        save_reports=args.save_reports,)
    o.run()
