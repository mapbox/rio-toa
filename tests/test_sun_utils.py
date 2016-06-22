from rio_toa import sun_utils, toa_utils
from rasterio.coords import BoundingBox
import numpy as np

def test_sun_angle():
    mtl = toa_utils._load_mtl('tests/data/LC81060712016134LGN00_MTL.json')

    mtl_sun = mtl['L1_METADATA_FILE']['IMAGE_ATTRIBUTES']['SUN_ELEVATION']

    bbox = BoundingBox(*toa_utils._get_bounds_from_metadata(mtl['L1_METADATA_FILE']['PRODUCT_METADATA']))

    sunangles = sun_utils.sun_elevation(
        bbox,
        (100, 100),
        mtl['L1_METADATA_FILE']['PRODUCT_METADATA']['DATE_ACQUIRED'],
        mtl['L1_METADATA_FILE']['PRODUCT_METADATA']['SCENE_CENTER_TIME'])

    assert sunangles.max() > mtl_sun
    assert sunangles.min() < mtl_sun