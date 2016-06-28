from rio_toa import sun_utils, toa_utils
from rasterio.coords import BoundingBox
import datetime
import numpy as np

from rio_toa.sun_utils import (
    parse_utc_string, time_to_dec_hour, calculate_declination
    solar_angle, sun_elevation)

def test_parse_utc_string():
    assert parse_utc_string('2014-10-22','04:37:48.7052949Z') == \
    datetime.datetime(2014, 10, 22, 4, 37, 48)

def test_time_to_dec_hour():
    assert time_to_dec_hour(
            datetime.datetime(2014,10, 22, 4, 37, 48)) == \
            4.630000000000001

# def test_declination():
#     d = 10
#     lat = 21.666821827007748
#     assert calculate_declination(d, lat) == 

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