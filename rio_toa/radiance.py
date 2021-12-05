import numpy as np
import rasterio
import riomucho

from rio_toa import toa_utils
from rio_toa.toa_utils import get_metadata_parameters


def radiance(img, ML, AL, src_nodata=0):
    """Calculate top of atmosphere radiance of Landsat 8
    as outlined here: http://landsat.usgs.gov/Landsat8_Using_Product.php

    L = ML * Q + AL

    where:
        L  = TOA spectral radiance (Watts / (m2 * srad * mm))
        ML = Band-specific multiplicative rescaling factor from the metadata
             (RADIANCE_MULT_BAND_x, where x is the band number)
        AL = Band-specific additive rescaling factor from the metadata
             (RADIANCE_ADD_BAND_x, where x is the band number)
        Q  = Quantized and calibrated standard product pixel values (DN)
             (ndarray img)

    Parameters
    -----------
    img: ndarray
        array of input pixels
    ML: float
        multiplicative rescaling factor from scene metadata
    AL: float
        additive rescaling factor from scene metadata

    Returns
    --------
    ndarray:
        float32 ndarray with shape == input shape
    """

    rs = ML * img.astype(np.float32) + AL
    if src_nodata is not None:
        rs[img == src_nodata] = 0.0

    return rs


def _radiance_worker(data, window, ij, g_args):
    """
    rio mucho worker for radiance
    TODO: integrate rescaling functionality for
    different output datatypes
    """
    output = toa_utils.rescale(
        radiance(
            data[0],
            g_args['M'],
            g_args['A'],
            g_args['src_nodata']),
        g_args['rescale_factor'],
        g_args['dst_dtype'],
        clip=g_args['clip'])

    return output


def calculate_landsat_radiance(src_path, src_mtl, dst_path, rescale_factor,
                               creation_options, band, dst_dtype, processes,
                               clip=True):
    """
    Parameters
    ------------
    src_path: strings
    src_mtl: string
    dst_path: string
    rescale_factor: float
    creation_options: dict
    bands: list
    dst_dtype: string
    processes: integer
    pixel_sunangle: boolean
    clip: boolean

    Returns
    ---------
    None
        Output is written to dst_path
    """
    mtl = toa_utils._load_mtl(src_mtl)

    meta_params = get_metadata_parameters(mtl)

    M = meta_params['RADIANCE_MULT_BAND_{}'.format(band)]
    A = meta_params['RADIANCE_ADD_BAND_{}'.format(band)]

    rescale_factor = toa_utils.normalize_scale(rescale_factor, dst_dtype)

    dst_dtype = np.__dict__[dst_dtype]

    with rasterio.open(src_path) as src:
        dst_profile = src.profile.copy()

        src_nodata = src.nodata

        for co in creation_options:
            dst_profile[co] = creation_options[co]

        dst_profile['dtype'] = dst_dtype

    global_args = {
        'A': A,
        'M': M,
        'src_nodata': src_nodata,
        'rescale_factor': rescale_factor,
        'clip': clip,
        'dst_dtype': dst_dtype
        }

    with riomucho.RioMucho([src_path],
                           dst_path,
                           _radiance_worker,
                           options=dst_profile,
                           global_args=global_args) as rm:

        rm.run(processes)
