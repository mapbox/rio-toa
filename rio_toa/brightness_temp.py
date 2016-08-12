import json
import numpy as np
import rasterio as rio
import collections
from rasterio.coords import BoundingBox
import riomucho
from rasterio import warp

from rio_toa import radiance
from rio_toa import toa_utils
from rio_toa import sun_utils


def brightness_temp(img, ML, AL, K1, K2, src_nodata=0):
    """Calculate brightness temperature of Landsat 8
    as outlined here: http://landsat.usgs.gov/Landsat8_Using_Product.php

    T = K2 / np.log((K1 / L)  + 1)

    and

    L = ML * Q + AL

    where:
        T  = At-satellite brightness temperature (degrees kelvin)
        L  = TOA spectral radiance (Watts / (m2 * srad * mm))
        ML = Band-specific multiplicative rescaling factor from the metadata
             (RADIANCE_MULT_BAND_x, where x is the band number)
        AL = Band-specific additive rescaling factor from the metadata
             (RADIANCE_ADD_BAND_x, where x is the band number)
        Q  = Quantized and calibrated standard product pixel values (DN)
             (ndarray img)
        K1 = Band-specific thermal conversion constant from the metadata
             (K1_CONSTANT_BAND_x, where x is the thermal band number)
        K2 = Band-specific thermal conversion constant from the metadata
             (K1_CONSTANT_BAND_x, where x is the thermal band number)


    Parameters
    -----------
    img: ndarray
        array of input pixels
    ML: float
        multiplicative rescaling factor from scene metadata
    AL: float
        additive rescaling factor from scene metadata
    K1: float
        thermal conversion constant from scene metadata
    K2: float
        thermal conversion constant from scene metadata

    Returns
    --------
    ndarray:
        float32 ndarray with shape == input shape
    """
    L = radiance.radiance(img, ML, AL, src_nodata=0)
    L[img == src_nodata] = np.NaN

    T = K2 / np.log((K1 / L) + 1)

    return T


def _brightness_temp_worker(data, window, ij, g_args):
    """rio mucho worker for brightness temperature. It reads input
    files and perform reflectance calculations on each window.

    Parameters
    ------------
    open_files: list of rasterio open files
    window: tuples
    g_args: dictionary

    Returns
    ---------
    out: None
        Output is written to dst_path
    """

    output = toa_utils.temp_rescale(
                    brightness_temp(
                        data[0],
                        g_args['M'],
                        g_args['A'],
                        g_args['K1'],
                        g_args['K2'],
                        g_args['src_nodata']),
                    g_args['temp_scale'])

    return output


def calculate_landsat_brightness_temperature(
        src_path, src_mtl, dst_path, temp_scale,
        creation_options, band, dst_dtype, processes):

    """Parameters
    ------------
    src_path: list
              list of src_paths(strings)
    src_mtl: string
             mtl file path
    dst_path: string
              destination file path
    rescale_factor: float [default] float(55000.0/2**16)
                    rescale post-TOA tifs to 55,000 or to full 16-bit
    creation_options: dictionary
                      rio.options.creation_options
    band: list
          list of integers
    dst_dtype: strings [default] uint16
               destination data dtype

    Returns
    ---------
    out: None
        Output is written to dst_path
    """
    mtl = toa_utils._load_mtl(src_mtl)

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

    dst_dtype = np.__dict__[dst_dtype]

    with rio.open(src_path) as src:
        dst_profile = src.profile.copy()

        src_nodata = src.nodata

        for co in creation_options:
            dst_profile[co] = creation_options[co]

        dst_profile['dtype'] = dst_dtype

    global_args = {
        'M': M,
        'A': A,
        'K1': K1,
        'K2': K2,
        'src_nodata': 0,
        'temp_scale': temp_scale,
        'dst_dtype': dst_dtype
        }

    with riomucho.RioMucho([src_path],
                           dst_path,
                           _brightness_temp_worker,
                           options=dst_profile,
                           global_args=global_args) as rm:

        rm.run(processes)
