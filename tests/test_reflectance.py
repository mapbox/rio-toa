import json
import numpy as np
import rasterio as rio
import riomucho
import pytest

from rio_toa import toa_utils
from rio_toa import reflectance


@pytest.fixture
def test_data():
    with rio.open('tests/data/tiny_LC81390452014295LGN00_B5.TIF', 'r') as src:
        tif = src.read(1)
        tif_meta = src.meta

    with rio.open('tests/data/tiny_LC81390452014295LGN00_B5_refl.TIF', 'r') as src:
        tif_output = src.read(1)
        tif_output_meta = src.meta

    with open('tests/data/LC81390452014295LGN00_MTL.json', 'r') as src:
        mtl = json.loads(src.read())

    return tif, tif_meta, tif_output, tif_output_meta, mtl


def test_reflectance():
    band = np.array([[0, 0, 0],
                [0, 1, 1],
                [1, 0, 1]]).astype('float32')

    MR = 0.2
    AR = -0.1
    E = 90

    assert np.array_equal(reflectance.reflectance(band, MR, AR, E),
        np.array([[ 0., 0. , 0. ],
                    [ 0. , 0.1, 0.1],
                    [0.1, 0., 0.1]]).astype(np.float32))

    with pytest.raises(TypeError):
        reflectance.reflectance(band, '45sldf', AR, E)


def test_calculate_reflectance(test_data):
    tif, tif_meta, tif_output, tif_output_meta, mtl = test_data

    M = toa_utils._load_mtl_key(mtl,
        ['L1_METADATA_FILE', 'RADIOMETRIC_RESCALING', 'REFLECTANCE_MULT_BAND_'],
        5)
    A = toa_utils._load_mtl_key(mtl,
        ['L1_METADATA_FILE', 'RADIOMETRIC_RESCALING', 'REFLECTANCE_ADD_BAND_'],
        5)
    E = toa_utils._load_mtl_key(mtl, 
        ['L1_METADATA_FILE', 'IMAGE_ATTRIBUTES','SUN_ELEVATION'])

    toa = reflectance.reflectance(tif, M, A, E)

    assert toa.dtype == np.float32
    assert np.array_equal(toa, tif_output)











