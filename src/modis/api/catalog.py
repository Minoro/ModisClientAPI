import datetime
from ...http.Http import HttpClient, url_join, url_json_file

BASE_URL = 'https://ladsweb.modaps.eosdis.nasa.gov/archive/allData/'

class Catalog(dict):
    """Represents a response data from the API
    Every API response is represented by a Catalog. 
    The topper Catalog level is the Collection and the lowerst is the ProductDay.
    The Catalog data can by accessed as a dictionary.
    """

    def __init__(self, info={}, parent=None, token=''):
        """Instantiate the Catalog with the 'info' data

        Args:
            info (dict, optional): Catalog data. A response from the API call. Defaults to {}.
            parent (Catalog, optional): The parent Catalog. Defaults to None.
            token (str, optional): Modis API token used in the requests. Defaults to ''.
        """
        
        if type(info) == str:
            info = {'name' : info}

        super(Catalog, self).__init__(info or {})

        self._http_client = HttpClient()
        if token != '':
            self._http_client.set_headers({'Authorization': 'Bearer ' + token})
        
        self._token = token
        self._data = []    
        self._parent = parent
        self.get_url()

    def set_api_token(self, token : str):
        """Set the API token used in the API requests

        Args:
            token (str): API token
        """
        self._http_client.set_headers({'Authorization': 'Bearer ' + token})
        self._token = token

    @property
    def name(self):
        return self['name']

    @property
    def updated_at(self):
        return self['last-modified']

    @property
    def size(self):
        return self['size']

    @property
    def url(self):
        if 'url' in self and self['url'] is not None:
            return self['url']

        return self.get_url()
    
    def get_url(self) -> str:
        """Build the Catalog API. 
        Every level from the API is based in the parent API and the name of the current Catalog.
        The first level Catalog (a Collection) use the BASE_URL and the collection name.
        Returns:
            [str]: Catalog url
        """
        if 'url' in self and self['url'] is not None:
            return self['url']

        if self._parent is None:
            self['url'] = url_join(BASE_URL, self['name'])
        else:    
            self['url'] = url_join(self._parent.url, self['name'])

        return self['url']

    @property
    def data(self):
        if len(self._data) > 0:
            return self._data

        return self.get_data_available()

    def get_data_available(self):
        """Do a HTTP GET request to the current Catalog URL

        Returns:
            [list]: Response data
        """
        self._data = self._http_client.get(url_json_file(self.url))
        return self._data


class Collection(Catalog):
    """Represents an available Collection from MODIS.
    All collections are listed in the BASE_URL.
    Each Collection is indentified by a unique name and many MODIS products. 
    """

    def __init__(self, data={}, token=''):
        
        if type(data) == str:
            data = {'name' : data}

        super(Collection, self).__init__(data, token=token)
        
        self._token = token
        self._products = {}


    @property
    def products(self):
        if len(self._products) > 0:
            return self._products.values()

        return self.get_products()
       
    def get_products(self) -> list:
        """Get the MODIS products available in the collection.
        Retrieve the data through a HTTP GET request to the collection URL

        Returns:
            list : Products available
        """
        self._products = {}
        products = build_products_collection(self.get_data_available(), self, self._token)
        
        for product in products:
            self._products[product['name']] = product
        
        return list(self._products.values())

    def product(self, product_name : str):
        """Select a Product by name

        Args:
            product_name (str): product name

        Returns:
            Product: Product from collection
        """
        if len(self._products) == 0:
            self.get_products()

        return self._products[product_name]

    def has_product(self, product_name : str) -> bool:
        """Check if the collection has the product

        Args:
            product_name (str): Product name

        Returns:
            bool: True if the collection has the product
        """
        if len(self._products) == 0:
            self.get_products()

        return product_name in self._products

    def get_url(self) -> str:
        """Get the collection URL based on its name

        Returns:
            str: URL to the Collection
        """
        if 'name' not in self:
            return ''

        self['url'] = url_join(BASE_URL, self['name'])
        return self['url']

class Product(Catalog):
    """Represents a Product from MODIS. A collection can have many Products.
    A Product has a unique name and it's collected through many years (ProductYear).
   This class can be used to obtain images collected on different dates.
    """
    
    def __init__(self, data={}, collection=None, token=''):
        
        if type(data) == str:
            data = {'name' : data}

        super(Product, self).__init__(data or {}, token=token)

        if type(collection) == str:
            collection = Collection(collection, token=token)

        self.token = token
        self._collection = collection
        self['collection_name'] = collection['name']
        self._years = {}
    
    @property
    def years(self):
        if len(self._years) > 0:
            return list(self._years.values())

        return self.get_years()

    def get_years(self) -> list:
        """Get a list of ProductYear available for the product

        Returns:
            list: list of ProductYear available
        """
        years = self.get_data_available()
        years = build_product_years(years, self, token=self.token)

        for year in years:
            self._years[year['name']] = year

        return years
    
    def year(self, year_name):
        """Get a year from the product

        Args:
            year_name (str): Year of the images

        Returns:
            list: ProductYear of the desired year
        """
        if len(self._years) == 0:
            self.get_years()

        year_name = str(year_name)
        return self._years[year_name]
    

    def get_days_date_range(self, start_date, end_date) -> list:
        """Get the ProductDay available for the product.
        One Product can have many days available.

        Args:
            start_date (str|datetime): first date from product
            end_date (str|datetime): last date from product

        Returns:
            list : List of available product
        """
        
        if type(start_date) == str:
            start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')

        if type(end_date) == str:
            end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')

        delta_date = end_date - start_date
        total_days = delta_date.days + 1
        
        days = []

        for i in range(total_days):

            day = start_date + datetime.timedelta(days=i)
            year = day.year
            day_of_year = day.timetuple().tm_yday

            product = self.year(year).day_of_year(day_of_year)
            if product is not None:
                days.append(product)

        return days


    def get_date(self, date):
        """Get a specific date collected from the Product

        Args:
            date (str|datetime): date of image collection

        Returns:
            ProductDay: the images available
        """
        if type(date) == str:
            date = datetime.datetime.strptime(date, '%Y-%m-%d')

        return self.year(date.year).day_of_year(date.timetuple().tm_yday)

class ProductYear(Catalog):
    """A Product collected in a specific year.
    Every year has many days of images
    """

    def __init__(self, data={}, product=None, token=''):
        
        if type(data) == str:
            data = {'name' : data}  

        super(ProductYear, self).__init__(data or {}, token=token)

        self._token = token
        self._product = product
        self['product_name'] = product['name']
        self._days = {}

        self.parse_year_from_url()

    def parse_year_from_url(self):
        """Resolve the year from API's URL
        """
        self._year = self['url'].split('/')[-1]

    @property
    def days(self):
        if len(self._days) > 0:
            return list(self._days.values())

        return self.get_days()

    def get_days(self):
        """Get the days available in the year for the product

        Returns:
            list : List of days available
        """
        days = self.get_data_available()
        days = build_product_days(days, self, token=self._token)

        for day in days:
            self._days[day['name']] = day

        return days

    def get_days_range(self, day_of_year_start, day_of_year_end) -> list:
        """Get a range of available ProductDay from the ProductYear
        The days are based in the day from start of the year

        Args:
            day_of_year_start (int|str): start of the range, based on the day of year
            day_of_year_end ([type]): end of range, based on the day of year

        Raises:
            ValueError: If the start day is greater than the end

        Returns:
            list: list of availabe days in the range
        """
        day_of_year_start = int(day_of_year_start)
        day_of_year_end = int(day_of_year_end)
        
        if day_of_year_start > day_of_year_end:
            raise ValueError('The end day must be greater than the start day')
        
        days = []
        for day in range(day_of_year_start, day_of_year_end + 1):
            
            if self.has_day_of_year(day):
                product_day = self.day_of_year(day)
                days.append(product_day)

        return days

    def day_of_year(self, day_of_year):
        """Get a specific day of the year

        Args:
            day_of_year (int|str): day of the year

        Returns:
            ProductDay: A specific ProductDay of image collect
        """
        if len(self._days) == 0:
            self.get_days()
        
        day_of_year = str(day_of_year)
        if self.has_day_of_year(day_of_year):
            return self._days[day_of_year]

        return None

    def has_day_of_year(self, day_of_year) -> bool:
        """Check if the product has the day of year collected

        Args:
            day_of_year (int|str): day of year

        Returns:
            bool: True if the Product has the day
        """
        if len(self._days) == 0:
            self.get_days()
        
        day_of_year = str(day_of_year)
        return day_of_year in self._days

class ProductDay(Catalog):
    """ A day of images collected for a product
    """

    def __init__(self, data={}, product_year=None, token=''):
        
        if type(data) == str:
            data = {'name' : data}

        super(ProductDay, self).__init__(data or {}, token=token)

        self._token = token
        self._product_year = product_year
        self['product_name'] = product_year['product_name']
        self['product_year'] = product_year['name']
        
        self._images = {}

        self.parse_url()

    def parse_url(self):
        """ Parse the url to get the Year and the day of year
        """
        url_parts =  self['url'].split('/')
        self._year = url_parts[-2]
        self._day_of_year = url_parts[-1]

        self._datetime = self.year_and_day_of_year_to_datetime(self._year, self._day_of_year)

    @property
    def images(self):
        if len(self._images) > 0:
            return list(self._images.values())
        
        return self.get_images()

    def get_images(self) -> list:
        """ Load all images collected in the day 

        Returns:
            list: List of images available
        """
        self._images = {}
        images = self.get_data_available()
        for image in images:
            image['url'] = url_join(self['url'], image['name'])
            
            image_data = self.parse_image_properties_from_name(image['name'])

            self._images[image['name']] = {**image_data, **image}

        return list(self._images.values())


    def image(self, image_name : str):
        """ Get a specific image data by name

        Args:
            image_name (str): Image name

        Returns:
            dict : image data 
        """

        if len(self._images) == 0:
            self.get_images()

        return self._images[image_name]

    def parse_image_properties_from_name(self, image_name : str):
        """Parse information from the image name.
        Image name has its product, collection, date and year of acquisition.
        Some images has the postion in a grid

        Args:
            image_name (str): image name

        Returns:
            dict: data extracted from image
        """
        image_properties = image_name.split('.')

        year_acquisition = image_properties[1][1:5]
        day_acquisition = image_properties[1][5:]

        image_data = {
            'product': image_properties[0],
            'year_day_acquisition' : image_properties[1],
            'year_acquisition' : year_acquisition,
            'day_acquisition' : day_acquisition,
            'datetime_acquisition' : self.year_and_day_of_year_to_datetime(year_acquisition, day_acquisition),
            'collection_number' : image_properties[3],
            'production_date_and_time' : image_properties[4],
        }

        if 'h' in image_name and 'v' in image_name:
            tile_position = image_properties[2]
            horizontal_position = image_properties[2][1:3]
            vertical_position = image_properties[2][4:]

            image_data['tile_position'] = image_properties[2],
            image_data['horizontal_position'] = int( horizontal_position )
            image_data['vertical_position'] = int( vertical_position )

        return image_data

    def year_and_day_of_year_to_datetime(self, year, day_of_year):
        """Convert a year and a day of year to datetime 

        Args:
            year (str|int): Year to be converted
            day_of_year (str|int): day of year to be converted

        Returns:
            datetime: datetime from the year
        """
        start_of_year = datetime.datetime( int(year), 1, 1)
        days_from_start = datetime.timedelta( int(day_of_year) - 1)

        return start_of_year + days_from_start


    def download_tile_by_position(self, position: tuple, output : str):
        """Download a specific tile from the collected day
        Its download the tile to the output folder.

        Args:
            position (tuple): horizontal and vertical position
            output (str): directory to save the image
        """
        image = self.get_image_tile(position)

        self.download(image, output)

    def get_image_tile(self, position: tuple):
        """ Get a image tile by its position

        Args:
            position (tuple): horizontal and vertical position

        Raises:
            ValueError: Raised if the postion not exists

        Returns:
            dict: Image data
        """
        horizontal_position = position[0]
        if horizontal_position < 0 or horizontal_position > 35:
            raise ValueError('Horizontal position must be between 0 and 35')

        vertical_position = position[1]
        if vertical_position < 0 or vertical_position > 17:
            raise ValueError('Vertical position must be between 0 and 17')

        for image in self.images:
            if 'tile_position' not in image:
                continue
            
            if image['horizontal_position'] == horizontal_position \
                and image['vertical_position'] == vertical_position:
                
                return image

        raise ValueError('Image not found')


    def download(self, image, output : str):
        """Download a specifc image by its url or dict-data to the output directory  

        Args:
            image (str|dict): Image to be downloaded
            output (str): output directory
        """
        
        url = image
        if type(image) == dict:
            url = image['url']
        
        elif type(image) == str and image in self._images:
            url = self.image(image)['url']

        self._http_client.download(url, output)


    def get_date(self):
        """ Get ProductDay datetime

        Returns:
            datetime: ProductDay datetime
        """
        return self._datetime

def build_collection(collection_data, token : str = '') -> Collection:
    """Convert the response from the API to Collection
    If a token is informed it will be used in the requests

    Args:
        collection_data (dict): response from the API
        token (str, optional): API token. Defaults to ''.

    Returns:
        Collection: A Collection built from the API response
    """
    return Collection(collection_data, token=token)

def build_products_collection(products_data : list, collection : Collection, token : str = '') -> list:
    """Convert the products from the API response to a list of Products objects.
    The collection parameter will be used as a "parent" level of the Productts.
    If a token is informed it will be used in the requests.

    Args:
        products_data (list): The response from the API as a list
        collection (Collection): Collection that has the products
        token (str, optional): API token. Defaults to ''.

    Returns:
        list: Products from the collection converted as objects
    """
    products = []
    for product in products_data:
        product['url'] = url_join(collection['url'], product['name'])
        
        products.append(Product(product, collection, token=token))

    return products


def build_product_years(product_years_data : list, product : Product, token: str = '') -> list:
    """Convert the years available in the API to the Product to a list of ProductYear.
    If a token is informed it will be used in the requests.

    Args:
        product_years_data (list): Response API with the years available to a Product
        product (Product): Product that has the years
        token (str, optional): API token. Defaults to ''.

    Returns:
        list: ProductYears available to a Product
    """
    product_years = []
    for year in product_years_data:
        year['url'] = url_join(product['url'], year['name'])

        product_years.append(ProductYear(year, product=product, token=token))

    return product_years


def build_product_days(product_days : list, product_year : ProductYear, token: str = '') -> list:
    """Convert the response API from the ProductYear to a list of ProductDay

    Args:
        product_days (list): Response API with the days available to a ProductYear
        product_year (ProductYear): ProcutYear that has the days
        token (str, optional): API token. Defaults to ''.

    Returns:
        list: [description]
    """
    products = []
    for day in product_days:
        day['url'] = url_join(product_year['url'], day['name'])

        products.append(ProductDay(day, product_year=product_year, token=token))

    return products
