import requests
import json
import os

DEFAULT_DOWNLOAD_CHUNK_SIZE = 8192

def url_join(base_url: str, *args):

    url_sufix =  '/'.join(args).replace('//', '/')

    if base_url.endswith('/'):
        return base_url + url_sufix

    return base_url + '/' + url_sufix


def url_json_file(url: str):
    if url.endswith('/'):
        url = url[:-1]
    
    return url + '.json'

class HttpClient:

    def __init__(self):
        self._headers = dict()
        self._download_chunk_size = DEFAULT_DOWNLOAD_CHUNK_SIZE

    def set_headers(self, headers):
        self._headers = headers

    def has_header(self, header_key):
        return header_key in self._headers

    def get(self, url, params={}):
        with requests.get(url, params=params, headers=self._headers) as r:
            if r.headers.get('content-type') == 'application/json':
                return r.json()

            return r.text

    def download(self, url, output):
        if os.path.isdir(output):
            os.makedirs(output, exist_ok=True)
            
            # add the file name if not exists
            file_name = url.split('/')[-1]
            output = os.path.join(output, file_name)

        with requests.get(url, stream=True, headers=self._headers) as r:
            r.raise_for_status()
            with open(output, 'wb') as f:
                for chunk in r.iter_content(chunk_size=self._download_chunk_size): 
                    f.write(chunk)
        
