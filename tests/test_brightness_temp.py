import json
import os

from affine import Affine
import click
from hypothesis import given
import hypothesis.strategies as st
from hypothesis.extra.numpy import arrays
import numpy as np
import pytest
import rasterio as rio
from rasterio.warp import reproject, Resampling

from rio_toa import brightness_temp
from rio_toa import toa_utils


def affaux(up):
    return Affine(1, 0, 0, 0, -1, 0), Affine(up, 0, 0, 0, -up, 0)


def upsample_array(bidx, up, fr, to):
    upBidx = np.empty(
        (bidx.shape[0] * up, bidx.shape[1] * up), dtype=bidx.dtype)

    reproject(
        bidx, upBidx,
        src_transform=fr,
        dst_transform=to,
        src_crs="EPSG:3857",
        dst_crs="EPSG:3857",
        resampling=Resampling.bilinear)

    return upBidx


def flex_compare(r1, r2, thresh=10):
    upsample = 4
    r1 = r1[::upsample]
    r2 = r2[::upsample]
    toAff, frAff = affaux(upsample)
    r1 = upsample_array(r1, upsample, frAff, toAff)
    r2 = upsample_array(r2, upsample, frAff, toAff)
    tdiff = np.abs(r1.astype(np.float64) - r2.astype(np.float64))
    click.echo('{0} values exceed the threshold difference '
               'with a max variance of {1}'.format(
                  np.sum(tdiff > thresh), tdiff.max()), err=True)
    return not np.any(tdiff > thresh)


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
       st.text(min_size=1),
       st.floats(min_value=0.1, max_value=1.0),
       st.floats(),
       st.floats())
def test_brightness_temp_wrong_type(img, ML, AL, K1, K2):
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


def test_brightness_temperature2(test_data):
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
    BT = brightness_temp.brightness_temp(tif, M, A, K1, K2, src_nodata=0)
    assert BT.dtype == np.float32
    assert flex_compare(tif_output, BT)


def test_calculate_landsat_brightness_temperature(test_var, test_data, capfd):
    src_path, src_mtl, tif_output_stack = \
        test_var[0], test_var[1], test_data[-3]
    dst_path = '/tmp/bt.tif'
    expected_path = 'tests/expected/bt.tif'
    temp_scale = 'F'
    creation_options = {}
    thermal_bidx = 11
    dst_dtype = 'float32'
    processes = 1

    brightness_temp.calculate_landsat_brightness_temperature(src_path, src_mtl,
                                              dst_path, temp_scale,
                                              creation_options, thermal_bidx,
                                              dst_dtype, processes)

    out, err = capfd.readouterr()
    assert os.path.exists(dst_path)

    with rio.open(dst_path) as created:
        with rio.open(expected_path) as expected:
            assert flex_compare(created.read(), expected.read())


def test_calculate_brightness_dst_dtype(test_var, capfd):
    src_path, src_mtl = test_var[0], test_var[1]
    dst_path = '/tmp/test_uint16.tif'
    temp_scale = 'K'
    creation_options = {}
    thermal_bidx = 11
    dst_dtype = 'uint16'
    processes = 1

    brightness_temp.calculate_landsat_brightness_temperature(
        src_path, src_mtl, dst_path, temp_scale, creation_options,
        thermal_bidx, dst_dtype, processes)

    assert os.path.exists(dst_path)

    with rio.open(dst_path) as created:
        assert created.meta['dtype'] == 'uint16'
