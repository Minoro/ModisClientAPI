import datetime
from ...http.Http import HttpClient, url_join, url_json_file

BASE_URL = 'https://ladsweb.modaps.eosdis.nasa.gov/archive/allData/'

class Catalog(dict):

    def __init__(self, info={}, parent=None, token=''):
        
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
    
    def get_url(self):
        if 'url' in self and self['url'] is not None:
            return self['url']

        if self._parent is None:
            self['url'] = url_join(BASE_URL, self['name'])
        else:    
            self['url'] = url_join(self._parent.url, self['name'])

        return self['url']

    @property
    def data(self):
        if self._data is not None:
            return self._data

        return self.get_data_available()

    def get_data_available(self):
        self._data = self._http_client.get(url_json_file(self.url))
        return self._data


class Collection(Catalog):

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
       
    def get_products(self):
        self._products = {}
        products = build_products_collection(self.get_data_available(), self, self._token)
        
        for product in products:
            self._products[product['name']] = product
        
        return list(self._products.values())

    def product(self, product_name : str):
        if len(self._products) == 0:
            self.get_products()

        return self._products[product_name]

    def has_product(self, product_name : str):
        if len(self._products) == 0:
            self.get_products()

        return product_name in self._products

    def get_url(self):
        if 'name' not in self:
            return

        self['url'] = url_join(BASE_URL, self['name'])
        return self['url']

class Product(Catalog):
    
    def __init__(self, data={}, collection=None, token=''):
        
        if type(data) == str:
            data = {'name' : data}

        super(Product, self).__init__(data or {}, token='')

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

    def get_years(self):
        years = self.get_data_available()
        years = build_product_years(years, self, token=self.token)

        for year in years:
            self._years[year['name']] = year

        return years
    
    def year(self, year_name):
        if len(self._years) == 0:
            self.get_years()

        year_name = str(year_name)
        return self._years[year_name]
    

    def get_days_date_range(self, start_date, end_date):
        
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

            days.append(product)

        return days


    def get_date(self, date):
        if type(date) == str:
            date = datetime.datetime.strptime(date, '%Y-%m-%d')

        return self.year(date.year).day_of_year(date.timetuple().tm_yday)

class ProductYear(Catalog):

    def __init__(self, data={}, product=None, token=''):
        
        if type(data) == str:
            data = {'name' : data}  

        super(ProductYear, self).__init__(data or {}, token='')

        self._token = token
        self._product = product
        self['product_name'] = product['name']
        self._days = {}

        self.parse_year_from_url()

    def parse_year_from_url(self):
        self._year = self['url'].split('/')[-1]

    @property
    def days(self):
        if len(self._days) > 0:
            return list(self._days.values())

        return self.get_days()

    def get_days(self):
        days = self.get_data_available()
        days = build_product_days(days, self, token=self._token)

        for day in days:
            self._days[day['name']] = day

        return days

    def get_days_range(self, day_of_year_start, day_of_year_end) -> list:
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
        if len(self._days) == 0:
            self.get_days()
        
        day_of_year = str(day_of_year)
        return self._days[day_of_year]
    
    def has_day_of_year(self, day_of_year):
        if len(self._days) == 0:
            self.get_days()
        
        day_of_year = str(day_of_year)
        return day_of_year in self._days

class ProductDay(Catalog):

    def __init__(self, data={}, product_year=None, token=''):
        
        if type(data) == str:
            data = {'name' : data}

        super(ProductDay, self).__init__(data or {}, token='')

        self._token = token
        self._product_year = product_year
        self['product_name'] = product_year['product_name']
        self['product_year'] = product_year['name']
        
        self._images = {}

        self.parse_url()

    def parse_url(self):
        url_parts =  self['url'].split('/')
        self._year = url_parts[-2]
        self._day_of_year = url_parts[-1]

        self._datetime = self.year_and_day_of_year_to_datetime(self._year, self._day_of_year)

    @property
    def images(self):
        if len(self._images) > 0:
            return list(self._images.values())
        
        return self.get_images()

    def get_images(self):
        self._images = {}
        images = self.get_data_available()
        for image in images:
            image['url'] = url_join(self['url'], image['name'])
            
            image_data = self.parse_image_properties_from_name(image['name'])

            self._images[image['name']] = {**image_data, **image}

        return list(self._images.values())


    def image(self, image_name):

        if len(self._images) == 0:
            self.get_images()

        return self._images[image_name]

    def parse_image_properties_from_name(self, image_name):
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
        start_of_year = datetime.datetime( int(year), 1, 1)
        days_from_start = datetime.timedelta( int(day_of_year) - 1)

        return start_of_year + days_from_start


    def download_tile_by_position(self, position: tuple, output : str):
        image = self.get_image_tile(position)

        return self.download(image, output)

    def get_image_tile(self, position: tuple):
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


    def download(self, image, output):
        
        url = image
        if type(image) == dict:
            url = image['url']
        
        elif type(image) == str and image in self._images:
            url = self.image(image)['url']

        self._http_client.download(url, output)


    def get_date(self):
        return self._datetime

def build_collection(collection_data, token : str = '') -> Collection:
    return Collection(collection_data, token=token)

def build_products_collection(products_data, collection : Collection, token : str ='') -> list:
    products = []
    for product in products_data:
        product['url'] = url_join(collection['url'], product['name'])
        
        products.append(Product(product, collection, token=token))

    return products


def build_product_years(product_years_data, product : Product, token: str = '') -> list:
    product_years = []
    for year in product_years_data:
        year['url'] = url_join(product['url'], year['name'])

        product_years.append(ProductYear(year, product=product, token=token))

    return product_years


def build_product_days(product_days, product_year : ProductYear, token: str = ''):
    products = []
    for day in product_days:
        day['url'] = url_join(product_year['url'], day['name'])

        products.append(ProductDay(day, product_year=product_year, token=token))

    return products
