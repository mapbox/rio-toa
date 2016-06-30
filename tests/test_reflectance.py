import os
import json
import numpy as np
import rasterio as rio
import riomucho
import pytest
from rasterio.coords import BoundingBox

from rio_toa import toa_utils, sun_utils
from rio_toa import reflectance


def test_reflectance():
    band = np.array([[0, 0, 0],
                     [0, 1, 1],
                     [1, 0, 1]]).astype('float32')

    MR = 0.2
    AR = -0.1
    E = 90.0

    assert np.array_equal(reflectance.reflectance(band, MR, AR, E),
                          np.array([[0., 0., 0.],
                                    [0., 5500., 5500.],
                                    [5500., 0., 5500.]]).astype(np.float32))


def test_reflectance_zero():
    band = np.array([[10508., 10272., 9869.],
                     [0., 101., 101],
                     [102., 0, 102]]).astype('float32')

    # with pytest.raises(ValueError):
    #     reflectance.reflectance(band, 0.2, -0.1, 0.0)


def test_reflectance_wrong_type():
    band = np.array([[9931., 9872., 9939.],
                     [0., 5000., 100.],
                     [10000.1, 0., 100002.]]).astype('float32')

    with pytest.raises(TypeError):
        reflectance.reflectance(band, '45sldf', -0.1, 65.0)


def test_reflectance_wrong_shape():
    band = np.array([[0, 0, 0],
                     [0, 1, 1],
                     [1, 0, 1]]).astype('float32')

    # wrong sun elevation shape
    with pytest.raises(ValueError):
        reflectance.reflectance(band, 0.2, -0.00000001,
                                np.array([[1, 2, 3], [4, 5, 6]]))

    with pytest.raises(ValueError):
        reflectance.reflectance(band, 35.1, np.array([1, 3]), 90.0)


@pytest.fixture
def test_data():
    with rio.open('tests/data/tiny_LC81390452014295LGN00_B5.TIF',
                  'r') as src:
        tif = src.read(1)
        tif_meta = src.meta
        tif_shape = src.shape

    with rio.open('tests/data/tiny_LC81390452014295LGN00_B5_refl2.TIF',
                  'r') as src:
        tif_output = src.read(1)
        tif_output_meta = src.meta

    with open('tests/data/LC81390452014295LGN00_MTL.json', 'r') as src:
        mtl = json.loads(src.read())

    return tif, tif_meta, tif_output, tif_shape, tif_output_meta, mtl


def test_calculate_reflectance(test_data):
    tif, tif_meta, tif_output, tif_shape, tif_output_meta, mtl = test_data

    M = toa_utils._load_mtl_key(mtl,
                                ['L1_METADATA_FILE',
                                 'RADIOMETRIC_RESCALING',
                                 'REFLECTANCE_MULT_BAND_'],
                                5)
    A = toa_utils._load_mtl_key(mtl,
                                ['L1_METADATA_FILE',
                                 'RADIOMETRIC_RESCALING',
                                 'REFLECTANCE_ADD_BAND_'],
                                5)
    E = toa_utils._load_mtl_key(mtl,
                                ['L1_METADATA_FILE',
                                 'IMAGE_ATTRIBUTES',
                                 'SUN_ELEVATION'])

    assert (np.sin(np.radians(E)) <= 1) & (-1 <= np.sin(np.radians(E)))
    assert isinstance(M, float)
    toa = reflectance.reflectance(tif, M, A, E)
    assert toa.dtype == np.float32
    # assert np.array_equal(toa, tif_output)

def test_calculate_reflectance2(test_data):
    tif, tif_meta, tif_output, tif_shape, tif_output_meta, mtl = test_data

    M = toa_utils._load_mtl_key(mtl,
                                ['L1_METADATA_FILE',
                                 'RADIOMETRIC_RESCALING',
                                 'REFLECTANCE_MULT_BAND_'],
                                5)
    A = toa_utils._load_mtl_key(mtl,
                                ['L1_METADATA_FILE',
                                 'RADIOMETRIC_RESCALING',
                                 'REFLECTANCE_ADD_BAND_'],
                                5)
    date_collected = toa_utils._load_mtl_key(mtl,
                    ['L1_METADATA_FILE', 'PRODUCT_METADATA', 'DATE_ACQUIRED'])
    time_collected_utc = toa_utils._load_mtl_key(mtl,
                    ['L1_METADATA_FILE', 'PRODUCT_METADATA', 'SCENE_CENTER_TIME'])
    bounds = BoundingBox(*toa_utils._get_bounds_from_metadata(mtl['L1_METADATA_FILE']['PRODUCT_METADATA']))
    E = sun_utils.sun_elevation(bounds, tif_shape, date_collected, time_collected_utc)
    toa = reflectance.reflectance(tif, M, A, E)
    assert toa.dtype == np.float32

def test_calculate_landsat_reflectance():
    src_path = 'tests/data/tiny_LC81390452014295LGN00_B5.TIF'
    src_mtl = 'tests/data/LC81390452014295LGN00_MTL.json'
    dst_path = '/tmp/reflectance.TIF'
    creation_options ={}
    band = 5
    dst_dtype = 'float32'
    processes = 1
    pixel_sunangle = True
    reflectance.calculate_landsat_reflectance(src_path, src_mtl, dst_path, \
                                creation_options, band, dst_dtype, \
                                processes, pixel_sunangle)
    assert os.path.exists(dst_path)


