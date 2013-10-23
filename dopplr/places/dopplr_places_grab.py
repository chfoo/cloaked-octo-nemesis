#!/usr/bin/python
'''This script grabs only /places/XX'''
import subprocess
import time
import urllib
import os

if __name__ == '__main__':
    if not os.path.exists('log'):
        os.mkdir('log')
    
    if not os.path.exists('warc'):
        os.mkdir('warc')
    
    instance_time = int(time.time())
    with open('dopplr_places.txt', 'r') as f:
        for place in f:
            if os.path.exists('STOP'):
                print 'STOP'
                break
        
            cur_time = int(time.time())
            place = place.strip()
            
            if not place:
                continue
            
            url = 'http://www.dopplr.com/place/{}'.format(place)
            print 'Fetch', url
            return_code = subprocess.call([
                'wget-lua', 
                '-U', "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/29.0.1547.66 Safari/537.36",
                '-o', 'log/{}-{}.log'.format(cur_time, place),
                '--no-check-certificate',
                '--truncate-output',
                '--output-document', '/tmp/{}-wget.tmp'.format(instance_time),
                '-e', 'robots=off',
                '--timeout', '60', '--tries', '5', '--waitretry', '5', '--level', '25',
                '--inet4-only',
                '--recursive',
                '--include', '/place/{}'.format(place),
                '--page-requisites',
                '--random-wait', '--wait', '0.1',
                '--warc-file', "warc/{}-{}".format(cur_time, place),
                '--warc-header', 'operator: Archive Team',
                '--verbose', 
                url])
            
            if return_code not in (0, 4, 6, 8):
                raise Exception('Wget error {}'.format(return_code))
            
            time.sleep(1)
