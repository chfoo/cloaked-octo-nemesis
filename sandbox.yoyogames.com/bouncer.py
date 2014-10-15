from http.server import HTTPServer, BaseHTTPRequestHandler
import http.client
import re
import requests
import urllib.parse
import logging


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path, delim, query_string = self.path.partition('?')
        
        if path != '/':
            self.send_error(404)
            return
        
        query = urllib.parse.parse_qs(query_string)
        
        if 'id' in query and query['id']:
            self.process_game(query['id'][0])
        else:
            self.send_error(404)
    
    def process_game(self, game_id):
        try:
            game_id = int(game_id)
        except ValueError:
            self.send_error(500)
            return
        
        url = 'http://sandbox.yoyogames.com/games/{}/download'
        
        response = requests.get(url.format(game_id),
            headers={'Accept-Encoding': 'gzip'})
        
        logging.info('Fetch %s', url.format(game_id))
        
        if response.status_code != 200:
            logging.info('Failed fetch %s %s', response.status_code, response.reason)
            self.send_error(500, 
                explain='Got {} {}'.format(response.status_code, response.reason))
            
        match = re.search(r'<a href="(/games/[\w_-]+/send_download\?code=[\w]+)">', response.text)
        
        download_link = 'http://sandbox.yoyogames.com{}'.format(match.group(1))
        
        logging.info('Got URL %s', download_link)
        
        self.send_response(http.client.TEMPORARY_REDIRECT)
        self.send_header('Location', download_link)
        self.send_header('Content-Length', '0')
        self.end_headers()


def run():
    logging.basicConfig(level=logging.INFO)
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, Handler)
    httpd.serve_forever()


if __name__ == '__main__':
    run()