import pytest
import json

from rio_toa import sun_utils, toa_utils
from rasterio.coords import BoundingBox
import datetime
import numpy as np
import pytest

from rio_toa.sun_utils import (
    parse_utc_string, time_to_dec_hour, calculate_declination,
    solar_angle, sun_elevation)


def test_parse_utc_string():
    assert parse_utc_string('2014-10-22', '04:37:48.7052949Z') == \
        datetime.datetime(2014, 10, 22, 4, 37, 48)


def test_time_to_dec_hour():
    assert time_to_dec_hour(
            datetime.datetime(2014, 10, 22, 4, 37, 48)) == \
            4.630000000000001


def test_declination():
    d = 173
    lat = 21.6668
    assert np.rad2deg(calculate_declination(d)) > 0.0


@pytest.fixture
def test_data():
    mtl1 = toa_utils._load_mtl('tests/data/LC81060712016134LGN00_MTL.json')
    mtl2 = toa_utils._load_mtl('tests/data/LC80430302016140LGN00_MTL.json')
    mtl3 = toa_utils._load_mtl('tests/data/LC82290902015304LGN00_MTL.json')
    mtl4 = toa_utils._load_mtl('tests/data/LC80100202015018LGN00_MTL.json')

    return mtl1, mtl2, mtl3, mtl4


def test_sun_angle(test_data):
    # South, Summer
    mtl = test_data[0]
    mtl_sun = mtl['L1_METADATA_FILE']['IMAGE_ATTRIBUTES']['SUN_ELEVATION']
    bbox = BoundingBox(*toa_utils._get_bounds_from_metadata(
            mtl['L1_METADATA_FILE']['PRODUCT_METADATA']))

    sunangles = sun_utils.sun_elevation(
        bbox,
        (100, 100),
        mtl['L1_METADATA_FILE']['PRODUCT_METADATA']['DATE_ACQUIRED'],
        mtl['L1_METADATA_FILE']['PRODUCT_METADATA']['SCENE_CENTER_TIME'])

    assert sunangles.max() > mtl_sun
    assert sunangles.min() < mtl_sun


def test_sun_angle2(test_data):
    # North, Summer
    mtl = test_data[1]
    mtl_sun = mtl['L1_METADATA_FILE']['IMAGE_ATTRIBUTES']['SUN_ELEVATION']
    bbox = BoundingBox(*toa_utils._get_bounds_from_metadata(
            mtl['L1_METADATA_FILE']['PRODUCT_METADATA']))

    sunangles = sun_utils.sun_elevation(
        bbox,
        (100, 100),
        mtl['L1_METADATA_FILE']['PRODUCT_METADATA']['DATE_ACQUIRED'],
        mtl['L1_METADATA_FILE']['PRODUCT_METADATA']['SCENE_CENTER_TIME'])

    assert sunangles.max() > mtl_sun
    assert sunangles.min() < mtl_sun


def test_sun_angle3(test_data):
    # South, Winter
    mtl = test_data[2]
    mtl_sun = mtl['L1_METADATA_FILE']['IMAGE_ATTRIBUTES']['SUN_ELEVATION']
    bbox = BoundingBox(*toa_utils._get_bounds_from_metadata(
            mtl['L1_METADATA_FILE']['PRODUCT_METADATA']))

    sunangles = sun_utils.sun_elevation(
        bbox,
        (100, 100),
        mtl['L1_METADATA_FILE']['PRODUCT_METADATA']['DATE_ACQUIRED'],
        mtl['L1_METADATA_FILE']['PRODUCT_METADATA']['SCENE_CENTER_TIME'])

    assert sunangles[49][49] - mtl_sun < 5


def test_sun_angle4(test_data):
    # South, Winter
    mtl = test_data[3]
    mtl_sun = mtl['L1_METADATA_FILE']['IMAGE_ATTRIBUTES']['SUN_ELEVATION']
    bbox = BoundingBox(*toa_utils._get_bounds_from_metadata(
            mtl['L1_METADATA_FILE']['PRODUCT_METADATA']))

    sunangles = sun_utils.sun_elevation(
        bbox,
        (100, 100),
        mtl['L1_METADATA_FILE']['PRODUCT_METADATA']['DATE_ACQUIRED'],
        mtl['L1_METADATA_FILE']['PRODUCT_METADATA']['SCENE_CENTER_TIME'])

    assert sunangles[49][49] - mtl_sun < 5


@pytest.fixture
def sun_elev_test_data():
    with open('tests/data/path164sundata.json') as dsrc:
        return json.loads(dsrc.read())


def test_sun_elev_calc(sun_elev_test_data):
    for d in sun_elev_test_data:
        pred_sun_el = sun_utils.sun_elevation(
            BoundingBox(*d['bbox']),
            (10, 10),
            d['date_acquired'],
            d['scene_center_time']
            )
        assert pred_sun_el.max() > d['mtl_sun_elevation']
        assert pred_sun_el.min() < d['mtl_sun_elevation']
