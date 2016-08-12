import os
import json
import numpy as np
import click
import rasterio as rio
import riomucho
import pytest
from rasterio.coords import BoundingBox
from raster_tester.compare import affaux, upsample_array



from rio_toa import toa_utils, sun_utils
from rio_toa import reflectance

def flex_compare(r1, r2, thresh=10):
    upsample = 4
    r1 = r1[::upsample]
    r2 = r2[::upsample]
    toAff, frAff = affaux(upsample)
    r1 = upsample_array(r1, upsample, frAff, toAff)
    r2 = upsample_array(r2, upsample, frAff, toAff)
    tdiff = np.abs(r1.astype(np.float64) - r2.astype(np.float64))
    click.echo('{0} values exceed the threshold difference with a max variance of {1}'.format(
        np.sum(tdiff > thresh), tdiff.max()), err=True)
    return not np.any(tdiff > thresh)


def test_reflectance():
    band = np.array([[0, 0, 0],
                     [0, 1, 1],
                     [1, 0, 1]]).astype('float32')

    MR = 0.2
    AR = -0.1
    E = 90.0

    assert np.array_equal(reflectance.reflectance(band, MR, AR, E),
                          np.array([[0., 0., 0.],
                                    [0., 0.1, 0.1],
                                    [0.1, 0., 0.1]]).astype(np.float32))


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


def test_reflectance_negative_elevation():
    band = np.array([[0, 0, 0],
                     [0, 2, 1],
                     [2, 0, 1.00008]]).astype('float32')
    MR = 0.2
    AR = -0.1
    E = -90.0

    with pytest.raises(ValueError):
        reflectance.reflectance(band, MR, AR, E)



@pytest.fixture
def test_var():
    src_path_b = 'tests/data/tiny_LC80460282016177LGN00_B2.TIF'
    src_path_g = 'tests/data/tiny_LC80460282016177LGN00_B3.TIF'
    src_path_r = 'tests/data/tiny_LC80460282016177LGN00_B4.TIF'
    src_mtl = 'tests/data/LC80460282016177LGN00_MTL.json'
    dst_path_single = 'tests/data/tiny_LC80460282016177LGN00_B2_refl.TIF'
    dst_path_stack = 'tests/data/tiny_LC80460282016177LGN00_rgb_refl.TIF'

    return src_path_b, src_path_g, src_path_r, \
        src_mtl, dst_path_single, dst_path_stack


@pytest.fixture
def test_data(test_var):
    src_path_b, src_path_g, src_path_r, \
        src_mtl, dst_path_single, dst_path_stack = test_var

    with rio.open(src_path_b, 'r') as src:
        tif_b = src.read(1)
        tif_meta = src.meta
        tif_shape = src.shape

    with rio.open(src_path_g, 'r') as src:
        tif_g = src.read(1)

    with rio.open(src_path_r, 'r') as src:
        tif_r = src.read(1)

    with rio.open(dst_path_single, 'r') as src:
        tif_output_single = src.read(1)
        tif_output_single_meta = src.meta

    with rio.open(dst_path_stack, 'r') as src:
        tif_output_stack = src.read(1)
        tif_output_stack_meta = src.meta

    with open(src_mtl, 'r') as src:
        mtl = json.loads(src.read())

    return tif_b, tif_g, tif_r, tif_meta, tif_shape, \
        tif_output_single, tif_output_single_meta, \
        tif_output_stack, tif_output_stack_meta, mtl


def test_calculate_reflectance(test_data):
    tif_b, tif_output_single, mtl = test_data[0], test_data[5], test_data[-1]

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
    toa = reflectance.reflectance(tif_b, M, A, E)
    toa_rescaled = toa_utils.rescale(toa, float(55000.0/2**16), np.float32)
    assert toa_rescaled.dtype == np.float32
    assert np.min(tif_output_single) == np.min(toa_rescaled)
    assert int(np.max(tif_output_single)) == int(np.max(toa_rescaled))


def test_calculate_reflectance2(test_data):
    tif_b, tif_shape, mtl = test_data[0], test_data[4], test_data[-1]

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
                                             ['L1_METADATA_FILE',
                                              'PRODUCT_METADATA',
                                              'DATE_ACQUIRED'])
    time_collected_utc = toa_utils._load_mtl_key(mtl,
                                                 ['L1_METADATA_FILE',
                                                  'PRODUCT_METADATA',
                                                  'SCENE_CENTER_TIME'])
    bounds = BoundingBox(*toa_utils._get_bounds_from_metadata(
                mtl['L1_METADATA_FILE']['PRODUCT_METADATA']))
    E = sun_utils.sun_elevation(bounds,
                                tif_shape,
                                date_collected,
                                time_collected_utc)
    toa = reflectance.reflectance(tif_b, M, A, E)
    assert toa.dtype == np.float32
    assert np.all(toa) < 1.5
    assert np.all(toa) >= 0.0


def test_calculate_landsat_reflectance(test_var, capfd):
    src_path, src_mtl = test_var[0], test_var[3]
    dst_path = '/tmp/ref1.TIF'
    rescale_factor = 1.0
    creation_options = {}
    band = 5
    dst_dtype = 'float32'
    processes = 1
    pixel_sunangle = False
    reflectance.calculate_landsat_reflectance([src_path], src_mtl, dst_path,
                                              rescale_factor, creation_options,
                                              [band], dst_dtype, processes,
                                              pixel_sunangle)
    out, err = capfd.readouterr()
    assert os.path.exists(dst_path)


def test_calculate_landsat_reflectance_single_pixel(test_var, capfd):
    src_path, src_mtl = test_var[0], test_var[3]
    dst_path = '/tmp/ref1.tif'
    expected_path = 'tests/expected/ref1.tif'
    rescale_factor = 1.0
    creation_options = {}
    band = 5
    dst_dtype = 'uint16'
    processes = 1
    pixel_sunangle = True

    reflectance.calculate_landsat_reflectance([src_path], src_mtl, dst_path,
                                              rescale_factor, creation_options,
                                              [band], dst_dtype, processes,
                                              pixel_sunangle)
    out, err = capfd.readouterr()
    
    with rio.open(dst_path) as created:
        with rio.open(expected_path) as expected:
            assert flex_compare(created.read(), expected.read())


def test_calculate_landsat_reflectance_stack_pixel(test_var, test_data, capfd):
    src_path, src_mtl, tif_output_stack = \
        test_var[:3], test_var[3], test_data[-3]
    dst_path = '/tmp/ref2.tif'
    expected_path = 'tests/expected/ref2.tif'
    rescale_factor = float(55000.0/2**16)
    creation_options = {}
    dst_dtype = 'uint16'
    processes = 1
    pixel_sunangle = True

    reflectance.calculate_landsat_reflectance(list(src_path), src_mtl,
                                              dst_path, rescale_factor,
                                              creation_options, [4, 3, 2],
                                              dst_dtype, processes,
                                              pixel_sunangle)

    out, err = capfd.readouterr()
    assert os.path.exists(dst_path)

    with rio.open(dst_path) as created:
        with rio.open(expected_path) as expected:
            assert flex_compare(created.read(), expected.read())
