import warnings
from ...http.Http import HttpClient, url_join, url_json_file
from .catalog import *


class ModisClient:
    """A Modis API Client to search and download Modis products and Images
    It uses an API Token to send requests and download images
    """

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

    def search(self, search_params : dict) -> list:
        """Search a Modis image. This method filter the images based on the search_params.
        Can be passed the 'collection' name to select a specific Modis Collection.
        Can be passed the 'product' name to select a specific Product of the Collection.
        If a specific 'date' datetime is informed it will be used to select all images available to that date.
        Or it can be informed a 'year' to filter the images.
        If the 'year' is informed it can be used the 'day_of_year' to select a specific day.
        If the 'start_date' and the 'end_date' is informed will be select a range of images available between these dates.
        Otherwise all dates will be used
        It can be passed a 'position' tuple with the horizontal and vertical position of the desired tile.
        Some products don't have the 'position' option.

        Args:
            search_params (dict): Options to be used to filter the images

        Returns:
            list : List of filtered tiles
        """

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
                    days += [ product.year(search_params['year']).day_of_year(search_params['day_of_year']) ]
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

    def collection(self, collection_name : str) -> Collection:
        """Select a specific collection by name.

        Args:
            collection_name (str): Collection name

        Raises:
            ValueError: If no collection are found

        Returns:
            Collection: The collection found
        """

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

    def get_products_from_collection(self, collection_name) -> list:
        """Get the products from a Collection by the collection name

        Args:
            collection_name (str): Collection name

        Returns:
            list: Products available in the Collection
        """
        
        if collection_name in self._products.keys() and self._products[collection_name] is not None:
            return self._products[collection_name]

        collection = self.collection(collection_name)

        self._products[collection_name] = collection.products

        return self._products[collection_name]

