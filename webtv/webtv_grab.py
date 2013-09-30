#!/usr/bin/python
import subprocess
import time
import urllib
import os

if __name__ == '__main__':
    instance_time = int(time.time())
    with open('urls.txt', 'r') as f:
        for url in f:
            if os.path.exists('STOP'):
                print 'STOP'
                break
        
            cur_time = int(time.time())
            url = url.strip()
            
            if not url:
                continue
            
            escaped_url = urllib.quote(url, '')
            print 'Fetch', url
            return_code = subprocess.call([
                'wget', 
                '-U', "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/29.0.1547.66 Safari/537.36",
                '-o', 'log/{}-{}.log'.format(cur_time, escaped_url),
                '--no-check-certificate', 
                '--output-document', '/tmp/{}-wget.tmp'.format(instance_time),
                '-e', 'robots=off',
                '--timeout', '60', '--tries', '5', '--waitretry', '5', '--level', '25',
                '--recursive',
                '-H', '-D', 'webtv.net',
                '--page-requisites',
                '--random-wait', '--wait', '0.1',
                '--warc-file', "warc/{}-{}.warc.gz".format(cur_time, escaped_url),
                '--warc-header', 'operator: Archive Team',
                '--verbose', 
                url])
            
            if return_code not in (0, 4, 6, 8):
                raise Exception('Wget error {}'.format(return_code))
            
            time.sleep(1)
