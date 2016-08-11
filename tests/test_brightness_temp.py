import os
import json
import numpy as np
import rasterio as rio
import riomucho
import pytest
from hypothesis import given
import hypothesis.strategies as st
from hypothesis.extra.numpy import arrays
from rasterio.coords import BoundingBox

from rio_toa import brightness_temp
from rio_toa import radiance
from rio_toa import toa_utils


# Testing brightness_temp python api
@given(arrays(np.uint16, (3, 8, 8),
              elements=st.integers(
                min_value=1,
                max_value=np.iinfo('uint16').max)),
       st.floats(min_value=0.0, max_value=1.0),
       st.floats(min_value=0.1, max_value=1.0),
       st.floats(),
       st.floats())
def test_brightness_temp(img, ML, AL, K1, K2):
    L = img.astype(np.float32) * ML + AL
    src_nodata = 0.0
    L[img == src_nodata] = np.nan
    Output = K2 / np.log((K1 / L) + 1)
    Result = brightness_temp.brightness_temp(img, ML, AL, K1, K2, src_nodata=0)
    np.testing.assert_array_equal(Output, Result)


# Testing brightness_temp python api
@given(arrays(np.uint16, (3, 8, 8),
              elements=st.integers(
                min_value=1,
                max_value=np.iinfo('uint16').max)),
       st.text(),
       st.floats(min_value=0.1, max_value=1.0),
       st.floats(),
       st.floats())
def test_brightness_temp_wrong_type(img, ML, AL, K1, K2):
    assert type(ML) == unicode
    with pytest.raises(TypeError):
        brightness_temp.brightness_temp(img, ML, AL, K1, K2, src_nodata=0)


# Testing brightness_temp python api
@given(arrays(np.uint16, (3, 8, 8),
              elements=st.integers(
                min_value=1,
                max_value=np.iinfo('uint16').max)),
       st.floats(min_value=0.1, max_value=1.0),
       arrays(np.uint16, (3,),
              elements=st.integers(
                min_value=1,
                max_value=np.iinfo('uint16').max)),
       st.floats(),
       st.floats())
def test_brightness_temp_wrong_shape(img, ML, AL, K1, K2):
    with pytest.raises(ValueError):
        brightness_temp.brightness_temp(img, ML, AL, K1, K2, src_nodata=0)


@pytest.fixture
def test_var():
    src_path = 'tests/data/tiny_LC80460282016177LGN00_B11.TIF'
    src_mtl = 'tests/data/LC80460282016177LGN00_MTL.json'
    dst_path = 'tests/data/tiny_LLC80460282016177LGN00_B11_bt.TIF'

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


def test_calculate_landsat_brightness_temperature(test_data):
    tif, tif_meta, tif_output, tif_shape, tif_output_meta, mtl = test_data
    band = 11

    M = toa_utils._load_mtl_key(mtl,
                                ['L1_METADATA_FILE',
                                 'RADIOMETRIC_RESCALING',
                                 'RADIANCE_MULT_BAND_'],
                                band)
    A = toa_utils._load_mtl_key(mtl,
                                ['L1_METADATA_FILE',
                                 'RADIOMETRIC_RESCALING',
                                 'RADIANCE_ADD_BAND_'],
                                band)
    K1 = toa_utils._load_mtl_key(mtl,
                                 ['L1_METADATA_FILE',
                                  'TIRS_THERMAL_CONSTANTS',
                                  'K1_CONSTANT_BAND_'],
                                 band)
    K2 = toa_utils._load_mtl_key(mtl,
                                 ['L1_METADATA_FILE',
                                  'TIRS_THERMAL_CONSTANTS',
                                  'K2_CONSTANT_BAND_'],
                                 band)

    assert isinstance(M, float)
    assert isinstance(A, float)
    assert isinstance(K1, float)
    assert isinstance(K2, float)
    BT = brightness_temp.brightness_temp(tif, M, A, K1, K2)
    assert BT.dtype == np.float32
    np.testing.assert_array_equal(tif_output, BT)
