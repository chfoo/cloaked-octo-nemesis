'''Scrapes recent urls from Twitter.

The API limits to only 7 days so it is not useful for a
historic scrape.
'''

import ConfigParser
import argparse
import time
import tweepy
import logging

_logger = logging.getLogger(__name__)


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('config')
    arg_parser.add_argument('query')
    arg_parser.add_argument('--max-id', default=2 ** 64, type=int)
    args = arg_parser.parse_args()

    config = ConfigParser.ConfigParser()
    config.read(args.config)

    consumer_token = config.get('twitter', 'consumer_token')
    consumer_secret = config.get('twitter', 'consumer_secret')
    access_token = config.get('twitter', 'access_token')
    access_token_secret = config.get('twitter', 'access_token_secret')

    auth = tweepy.OAuthHandler(consumer_token, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    api = tweepy.API(auth)

#     results = tweepy.Cursor(
#         api.search, args.query, result_type='recent', count=100).items()

    max_id = args.max_id

    while True:
        results = api.search(args.query, result_type='recent', count=100,
            max_id=max_id)

        for result in results:
            _logger.debug('ID {}, Date {}'.format(result.id,
                result.created_at))

            max_id = min(result.id, max_id)

            for url_obj in result.entities['urls']:

                url = url_obj['expanded_url']
                _logger.debug('URL: {}'.format(url))

                print url

        max_id -= 1
        _logger.debug('Sleep, max_id = {}'.format(max_id))
        time.sleep(5)

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    main()
