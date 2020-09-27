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

    def search(self, search_params : dict):

        if 'collection' in search_params:
            collection = self.collection(search_params['collection'])
            collections = [ collection ]
        else:
            collections = list(self._collections.values)

        if 'product' not in search_params:
            search_params['product'] = ''

        products = []
        for collection in collections:
            products += self.get_products_from_collection(collection['name'])
            
            if collection.has_product(search_params['product']):
                products = [ collection.product(search_params['product']) ]
                break
        
        days = []
        if 'date' in search_params:
            for product in products:
                days += product.get_date(search_params['date'])
                
        elif 'year' in search_params:
            
            for product in products:
                if 'day_of_year' in search_params:
                    days += product.year(search_params['year']).day_of_year(search_params['day_of_year'])
                else:
                    days += product.year(search_params['year']).days

        elif 'start_date' in search_params and 'end_date' in search_params:
            
            for product in products:
                days += product.get_days_date_range(search_params['start_date'], search_params['end_date'])

        else:
            for product in products:
                for year in product.years:
                    days += year.days

        tiles = []
        if 'position' in search_params:
            for day in days:
                tile = day.get_image_tile(search_params['position'])
                tiles.append(tile)
        else:
            for day in days:
                tiles += day.images

        return tiles


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

    def collection(self, collection_name):

        if len(self._collections) == 0:
            self.get_collections()

        if collection_name not in self._collections:
            raise ValueError('Collection not found')
        
        return self._collections[collection_name]

    def get_products(self):
        if len(self._collections) == 0:
            self.get_collections()

        products = []
        for colleciton_name in self._collections:    
            products += self.get_products_from_collection(colleciton_name)

        return products   

    def get_products_from_collection(self, collection_name):
        
        if collection_name in self._products.keys() and self._products[collection_name] is not None:
            return self._products[collection_name]

        collection = self.collection(collection_name)

        self._products[collection_name] = collection.products

        return self._products[collection_name]





