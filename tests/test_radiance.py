import os
import json
import numpy as np
import rasterio as rio
import riomucho
import pytest
from rasterio.coords import BoundingBox

from rio_toa import toa_utils, sun_utils
from rio_toa import radiance


def test_radiance():
    band = np.array([[0, 0, 0],
                     [0, 1, 1],
                     [1, 0, 1]]).astype('float32')

    ML = 0.2
    AL = -0.1

    assert np.array_equal(radiance.radiance(band, ML, AL),
                          np.array([[0., 0., 0.],
                                    [0., 0.1, 0.1],
                                    [0.1, 0., 0.1]]).astype(np.float32))


def test_radiance_wrong_type():
    band = np.array([[9931., 9872., 9939.],
                     [0., 5000., 100.],
                     [10000.1, 0., 100002.]]).astype('float32')

    with pytest.raises(TypeError):
        radiance.radiance(band, '45sldf', -0.1, 65.0)


def test_radiance_wrong_shape():
    band = np.array([[0, 0, 0],
                     [0, 1, 1],
                     [1, 0, 1]]).astype('float32')

    # wrong ML shape
    with pytest.raises(ValueError):
        radiance.radiance(band, np.array([[1, 2, 3], [4, 5, 6]]),
                          -0.00000001)

    # wrong AL shape
    with pytest.raises(ValueError):
        radiance.radiance(band, 35.1, np.array([1, 3]))


@pytest.fixture
def test_var():
    src_path = 'tests/data/tiny_LC81390452014295LGN00_B5.TIF'
    src_mtl = 'tests/data/LC81390452014295LGN00_MTL.json'
    dst_path = 'tests/data/tiny_LC81390452014295LGN00_B5_radl.TIF'

    return src_path, src_mtl, dst_path


@pytest.fixture
def test_data(test_var):
    src_path, src_mtl, dst_path = test_var

    with rio.open(src_path, 'r') as src:
        tif = src.read(1)
        tif_meta = src.meta
        tif_shape = src.shape

    with rio.open(dst_path, 'r') as src:
        tif_output = src.read(1)
        tif_output_meta = src.meta

    with open(src_mtl, 'r') as src:
        mtl = json.loads(src.read())

    return tif, tif_meta, tif_output, tif_shape, tif_output_meta, mtl


def test_calculate_radiance(test_data):
    tif, tif_meta, tif_output, tif_shape, tif_output_meta, mtl = test_data

    M = toa_utils._load_mtl_key(mtl,
                                ['L1_METADATA_FILE',
                                 'RADIOMETRIC_RESCALING',
                                 'RADIANCE_MULT_BAND_'],
                                5)
    A = toa_utils._load_mtl_key(mtl,
                                ['L1_METADATA_FILE',
                                 'RADIOMETRIC_RESCALING',
                                 'RADIANCE_ADD_BAND_'],
                                5)

    assert isinstance(M, float)
    toa = radiance.radiance(tif, M, A)
    toa_rescaled = toa_utils.rescale(toa, float(55000.0/2**16), np.uint16)
    assert toa_rescaled.dtype == np.uint16
    assert np.min(tif_output) == np.min(toa_rescaled)
    assert int(np.max(tif_output)) == int(np.max(toa_rescaled))




def test_calculate_radiance2(test_data):
    tif, tif_meta, tif_output, tif_shape, tif_output_meta, mtl = test_data

    M = toa_utils._load_mtl_key(mtl,
                                ['L1_METADATA_FILE',
                                 'RADIOMETRIC_RESCALING',
                                 'RADIANCE_MULT_BAND_'],
                                5)
    A = toa_utils._load_mtl_key(mtl,
                                ['L1_METADATA_FILE',
                                 'RADIOMETRIC_RESCALING',
                                 'RADIANCE_ADD_BAND_'],
                                5)

    toa = toa_utils.rescale(radiance.radiance(tif, M, A),
        float(55000.0/2**16), np.uint16)
    assert toa.dtype == np.uint16
    assert np.all(toa) < 1.5
    assert np.all(toa) >= 0.0


def test_calculate_landsat_radiance(test_var, capfd):
    src_path, src_mtl = test_var[:2]
    dst_path = '/tmp/rad1.TIF'
    rescale_factor = 1.0
    creation_options = {}
    band = 5
    dst_dtype = 'uint16'
    processes = 1
    radiance.calculate_landsat_radiance(src_path, src_mtl, dst_path,
                                rescale_factor, creation_options, band,
                                dst_dtype, processes)
    out, err = capfd.readouterr()
    assert os.path.exists(dst_path)
