import warnings
from ...http.Http import HttpClient, url_join, url_json_file
from .catalog import *


class ModisClient:

    def __init__(self, token=''):
        self._token = token
        self._http_client = HttpClient()

        self._token = token
        if token != '':
            self._http_client.set_headers({'Authorization': 'Bearer ' + token})
        else:
            warnings.warn("API token is missing")

        self._collections = {}
        self._products = {}

    @property
    def collections(self):
        if len(self._collections) > 0:
            return list(self._collections.values())

        return self.get_collections()

    def get_collections(self):
        collections = self._http_client.get(url_json_file(BASE_URL))
        
        for c in collections:
            collection = build_collection(c, token=self._token)
            self._collections[c['name']] =  collection

        return list(self._collections.values())


    def get_products_from_collection(self, collection_name):
        
        if collection_name in self._products.keys() and self._products[collection_name] is not None:
            return self._products[collection_name]

        collection = self.get_collection(collection_name)

        products = self._http_client.get(url_json_file(collection['url']))

        self._products[collection_name] = build_products_collection(products, collection, token=self._token)

        for product in self._products[collection_name]:
            product['url'] = url_join(collection['url'], product['name'])

        return self._products[collection_name]


    def collection(self, collection_name):

        if len(self._collections) == 0:
            self.get_collections()

        if collection_name not in self._collections:
            raise ValueError('Collection not found')
        
        return self._collections[collection_name]


