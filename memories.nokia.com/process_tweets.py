import sys
import json

import requests


def main():
    counter = 0
    
    for line in sys.stdin:
        if not line:
            break
        
        doc = json.loads(line)
        counter += 1
        if counter % 100 == 0:
            print(counter, file=sys.stderr)

        for short_url, expanded_url in doc['urls']:
            if expanded_url and 'memories.nokia.com' in expanded_url:
                print(expanded_url)
            elif expanded_url:
                print('Fetch', expanded_url, file=sys.stderr)
                try:
                    response = requests.head(expanded_url)
                except requests.exceptions.ConnectionError as error:
                    print(error, file=sys.stderr)
                    continue
                try:
                    new_url = response.headers['location']
                except KeyError:
                    pass
                else:
                    if 'memories.nokia.com' in new_url:
                        print(new_url)


if __name__ == '__main__':
    main()
