import requests
import numpy as np
from skimage import io
from shapely.geometry import shape

class BrowseImage(object):
    """
      Image class for fetching and spatially indexing an image's browse image (low res previews)

      Args:
          catalog_id (str): the catalog id for the browse image
          bbox (list): the bounding box in WGS84 coords for spatial indexing
      Returns:
          BrowseImage (object)
    """    
    def __init__(self, catalog_id, bbox=None):
        
        self.catalog_id = catalog_id
        self._get_image()
        self.metadata = self._get_metadata()
        self.shape = self.image.shape
        self.geom = self._get_geometry()
        self.xmin, self.ymin, self.xmax, self.ymax = self.geom.bounds
        self.cell_width = (self.xmax - self.xmin)/self.shape[1]
        self.cell_height = (self.ymax - self.ymin)/self.shape[0]
        self.bbox = bbox

        if self.bbox is not None:
            # find which cells intersect the bbox
            bbox_xmin, bbox_ymin, bbox_xmax, bbox_ymax = self.bbox
            window_xmin = int(np.floor((bbox_xmin - self.xmin)/self.cell_width))
            window_xmax = int(np.ceil((bbox_xmax - self.xmin)/self.cell_width))
            window_ymax = self.shape[0]-int(np.floor((bbox_ymin - self.ymin)/self.cell_height))
            window_ymin = self.shape[0]-int(np.ceil((bbox_ymax - self.ymin)/self.cell_height))
            self.window = ((window_ymin, window_ymax), (window_xmin, window_xmax))
        else:
            self.window = None

            
    def _get_image(self):
        url = 'https://api.discover.digitalglobe.com/show?id={}'.format(self.catalog_id)
        self.image = io.imread(url)
            
    def rgb(self):
        return self.read()
    
    def _get_metadata(self):
        url = 'https://geobigdata.io/thumbnails/v1/metadata/{}.json'.format(self.catalog_id)
        response = requests.get(url)
        return response.json()
        
    def _get_geometry(self):
        if 'bbox' in self.metadata.keys():
            geom = shape(self.metadata['bbox'])
        elif 'geometry' in self.metadata.keys():
            geom = shape(self.metadata['geometry'])
        else:
            raise ValueError("Invalid metadata returned by metadata service. Cannot create BrowseImage")
        return geom
        
    def read(self):
        if self.window is None:
            return self.image
        else:
            (miny, maxy), (minx, maxx) = self.window
            return self.image[miny:maxy,minx:maxx,:]
        
    def plot(self, w=10, h=10, title='', fontsize=24):
        plt.figure(figsize=(w, h))
        sp = plt.subplot(1, 1, 1)
        plt.axis('off')
        sp.set_title(title, fontsize=fontsize)
        plt.imshow(self.rgb())