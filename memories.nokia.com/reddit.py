import requests


def main():
    after = None
    while True:
        url = 'https://www.reddit.com/domain/memories.nokia.com/new/.json?limit=100'
        if after:
            url += '&after=' + after
        
        response = requests.get(url)
        doc = response.json()
        
        for child in doc['data']['children']:
            print(child['data']['url'])
        
        if 'after' in doc:
            after = doc['data']['after']
        else:
            break
    
    after = None
    while True:
        url = 'https://www.reddit.com/domain/media.memories.nokia.com/new/.json?limit=100'
        if after:
            url += '&after=' + after
        
        response = requests.get(url)
        doc = response.json()
        
        for child in doc['data']['children']:
            print(child['data']['url'])
        
        if 'after' in doc:
            after = doc['data']['after']
        else:
            break


if __name__ == '__main__':
    main()
