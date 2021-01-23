import rasterio as rio
import numpy as np
import numpy.ma as ma
import re

class ModisSurfaceReflectanceImage:

    def __init__(self, image_path):

        self.image_path = image_path
        self.dataset = None
        self._meta = None
        self.crs = None
        self.subdataset = []
        self.bands = {}

    def __enter__(self):
        
        self.dataset = rio.open(self.image_path)
        # self.meta = self.dataset.meta
        self.crs = self.dataset.crs
        
        # filter the reflectance bands using regex
        self.subdataset = [ name for name in self.dataset.subdatasets if re.search("b0.\_1$", name) ]
        
        return self

    def __exit__(self, ex_type, ex_instance, traceback): 
        self.dataset.close()
        self.reset()


    @property
    def metatada(self):
        if self._meta is None:
            self.read()
        
        return self._meta


    def read(self, band = None):

        if type(band) == str:
            return self.read_by_name(band)
        elif type(band) == int:
            return self.read_band_number(band)
        elif type(band) == tuple:
            bands = [ self.read_band_number(b) for b in band ]
            return np.stack(bands)
        elif band is None:
            bands = [ self.read_band_number(i + 1) for i in range(len(self.subdataset)) ]
            return np.stack(bands)
            
        raise 'The band must be a str, int or tuple of ints'

    def read_band_number(self, band_number : int):
        return self.read_by_name( self.subdataset[band_number - 1] )

    def read_by_name(self, name : str):
        
        if name in self.bands:
            return self.bands[name]

        with rio.open(name) as subdataset:
            self.bands[name] = subdataset.read(1) 
            self._meta = subdataset.profile
            return self.bands[name]

    def save_as_tif(self, path, mask_nodata=True):

        if not path.lower().endswith('.tif') and not path.lower().endswith('.tiff'):
            raise 'The output image must has a tif or tiff extension'
        
        meta = self.metatada
        meta['driver'] = 'GTiff'
        meta['count'] = len(self.bands)

        # load bands if needed
        if len(self.bands) == 0:
            self.read()
            
        bands = []
        for name in self.bands:
            bands.append( self.bands[name] )

        bands = np.stack(bands)

        if mask_nodata:
            bands = ma.masked_where(bands == meta["nodata"], bands)

        with rio.open(path, "w", **meta) as dest:
            dest.write(bands)



    def reset(self):
        self.image_path = None
        self.dataset = None
        self._meta = None
        self.crs = None
        self.subdataset = []
        self.bands = {}
