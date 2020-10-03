# Modis Client API

An simple client for the MODIS API to browse, search and download available images. The client can be used to explore the data available at [LAADS Archive](https://ladsweb.modaps.eosdis.nasa.gov/archive/allData/).

# Class Hierarchy

Every directory level available in [LAADS Archive](https://ladsweb.modaps.eosdis.nasa.gov/archive/allData/) is represented by a specific class. The higherest level is a ```Catalog``` and the lowerest is the ```ProductDay```:
```
- Catalog
    |-- Colletion
        |-- Product
            |-- ProductYear
                |-- ProductDay
``` 

The MODIS product (```Product```) defines how data are made available. Each ```ProductYear``` holds all data collected to a specific year. The ```ProductDay``` holds all image available to a specific day.

The ```Catalog``` extends a ```dict``` and every class other class in the hierarchy extends the ```Catalog```, because of that the response from the API url of the directory can be accessed as a ```dict```:

```

# Select a Product
product = client.collection('6').product('MOD09A1')

# Print the product name
print(product['name'])

# Pritn the product URL
print(product['url'])

# Updated at
print(product['last-modified'])

# Size
print(product['size'])

```

When you select a specific Catalog (Collection, Product, ProductYear or ProductDay) you can load the directory data it holds. By default a Catalog is lazy, so the data will be loaded only if its needed or explicit told:

```
# Select a Product
product = client.collection('6').product('MOD09A1')

# Load new data from the API
data = product.get_data_available()

# Access as a property, will load new data only if it is not already loaded
data = product.data

```


# Exploring the data

To instantiate the client and start browsing data you just need:

```
client = ModisClient()

# Or with an API token

my_api_token = ''
client = ModisClient(token=my_api_token)

```

If you don't set an API token it will raise an warning `API token is missing`. The token isn't needed to browse the data, but is required to download.

This client is lazy, so it won't load data when initialized. You can access the data available in a directory as a method or as a property. When accessed as a method it will request fresh data from the API. If you access the data as a property it will first check if it already has data in memory and will request new data only if needed. 

This client divided the data available in the directories of [LAADS Archive](https://ladsweb.modaps.eosdis.nasa.gov/archive/allData/) in diferent classes. The highest level is called ```Catalog``` and it holds the ```Collection``` available. You can see all collecitons available with:

```
# As a method
client.get_collections()

# As a property (lazy)
client.collections

```

It will return a list of ```Collection``` objects. A collection is identified by a name and hold many ```Products```. To select a specific ```Collection``` you can specify it by name through the ```ModisClient``` or instantiate it directly passing it's name in the constructor:

```
# Select the Collection 6
collection = client.collection('6')
print(collection['name'])

# Instantiate a new Collection
collection = Collection('6')
print(collection['name'])

```

A ```Product``` specify the resolution (spacial and temporal) of the images. It is collected through many days during many years. To see all products available in a collection one can use:

```
collection = client.collection('6)

# As a method
products = collection.get_products()

# As a property (lazy)
products = collection.products

# Directly from the ModisClient
products = client.get_products_from_collection('6')
```

You can select a specific product by name from the collection and see all years available, or select a range of date or a specific date:

```
# Select a the product MOD09A1 from the collection 6
product = client.collection('6').product('MOD09A1')
print(product['name'])

# See all years available - as a property
print(product.years)

# See all years available - as a method
print(product.get_years())

# Select a range of available days (list of ProductDay)
days = product.get_days_date_range('2020-08-01', '2020-08-31')

# Select a specific product day
day = product.get_date('2020-08-01')


# Select a specific year - return an ProductYear
year = product.year(2020)

# Days available to a specific product
days = year.days

# Select a specific day by the day of year
day = year.day_of_year(265)

```

After you select a specific day it will be possible access the data of images available in that date. Some images are made available as a grid system, in this case you can access a specific tile:

```
product = client.collection('6').product('MOD09A1')
year = product.year(2020)
day = year.day_of_year(265)

# Selec the images available in the day specified 
images = day.images
print(images)

# Select a image tile. It will select the tile at 15 horizontal and 0 vertical position
tile = day.get_image_tile((15, 0))

print(tile)
```

# Search Images

It is also possible to search for data using the Modis Client:
```

# Search for images in a range of dates for a specific position 
result = client.search({
        'collection' : '6', 
        'product' : 'MOD09GA', 
        'start_date' : '2020-08-01', 
        'end_date' : '2020-08-02',
        'position' : (35, 10)  # can be omited to get all images available
    })
    

print(result)

# All images to a specific date
result = client.search({
        'collection' : '6', 
        'product' : 'MOD09GA', 
        'date' : '2020-08-01', 
    })
    

print(result)

# Using the day of year
result = client.search({
        'collection' : '6', 
        'product' : 'MOD09GA', 
        'year' : '2020',
        'day_of_year': '265' # can be omited to get all days 
    })
    

print(result)

```

It will return the ```ProductDay``` that meet the criteria.


# Download Images

**Atention**: The API token is needed to download data.

After select a image (tile) you can download it, specifying the image or position:

```
# Set the API Token to the client
client = ModisClient(token=my_api_token)

# Select a day
product = client.collection('6').product('MOD09A1')
day = product.year(2020).day_of_year(265)

# Selec the images available in the day specified 
images = day.images

# Download the image
day.download(images[0], './data')

# Download the image by name
image_name = images[0]['name']
day.download(image_name, './data')

# Download a tile
day.download_tile_by_position((15,0), './data')

```

