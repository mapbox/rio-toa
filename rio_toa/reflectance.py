import json
import numpy as np
import rasterio as rio
import collections
from rasterio.coords import BoundingBox
import riomucho
from rasterio import warp

from rio_toa import toa_utils
from rio_toa import sun_utils


def reflectance(img, MR, AR, E, src_nodata=0):
    """Calculate surface reflectance of Landsat 8
    as outlined here: http://landsat.usgs.gov/Landsat8_Using_Product.php

    R_raw = MR * Q + AR

    R = R_raw / cos(Z) = R_raw / sin(E)

    Z = 90 - E (in degrees)

    where:

        R_raw = TOA planetary reflectance, without correction for solar angle.
        R = TOA reflectance with a correction for the sun angle.
        MR = Band-specific multiplicative rescaling factor from the metadata
            (REFLECTANCE_MULT_BAND_x, where x is the band number)
        AR = Band-specific additive rescaling factor from the metadata
            (REFLECTANCE_ADD_BAND_x, where x is the band number)
        Q = Quantized and calibrated standard product pixel values (DN)
        E = Local sun elevation angle. The scene center sun elevation angle
            in degrees is provided in the metadata (SUN_ELEVATION).
        Z = Local solar zenith angle (same angle as E, but measured from the
            zenith instead of from the horizon).

    Parameters
    -----------
    img: ndarray
        array of input pixels of shape (rows, cols) or (rows, cols, depth)
    MR: float or list of floats
        multiplicative rescaling factor from scene metadata
    AR: float or list of floats
        additive rescaling factor from scene metadata
    E: float or numpy array of floats
        local sun elevation angle in degrees

    Returns
    --------
    ndarray:
        float32 ndarray with shape == input shape

    """

    if np.any(E < 0.0):
        raise ValueError("Sun elevation must be nonnegative "
                         "(sun must be above horizon for entire scene)")

    input_shape = img.shape

    if len(input_shape) > 2:
        img = np.rollaxis(img, 0, len(input_shape))

    rf = ((MR * img.astype(np.float32)) + AR) / np.sin(np.deg2rad(E))
    rf[img == src_nodata] = 0.0

    if len(input_shape) > 2:
        if np.rollaxis(rf, len(input_shape) - 1, 0).shape != input_shape:
            raise ValueError(
                "Output shape %s is not equal to input shape %s"
                % (rf.shape, input_shape))
        else:
            return np.rollaxis(rf, len(input_shape) - 1, 0)
    else:
        return rf


def _reflectance_worker(open_files, window, ij, g_args):
    """rio mucho worker for reflectance. It reads input
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
    data = riomucho.utils.array_stack([
      src.read(window=window).astype(np.float32)
      for src in open_files
    ])

    depth, rows, cols = data.shape

    if g_args['pixel_sunangle']:
        bbox = BoundingBox(
                    *warp.transform_bounds(
                        g_args['src_crs'],
                        {'init': u'epsg:4326'},
                        *open_files[0].window_bounds(window)))

        E = sun_utils.sun_elevation(
                        bbox,
                        (rows, cols),
                        g_args['date_collected'],
                        g_args['time_collected_utc']).reshape(rows, cols, 1)

    else:
        # We're doing whole-scene (instead of per-pixel) sunangle:
        E = np.array([g_args['E'] for i in range(depth)])

    output = toa_utils.rescale(reflectance(
                    data,
                    g_args['M'],
                    g_args['A'],
                    E,
                    g_args['src_nodata']),
                g_args['rescale_factor'], g_args['dst_dtype'])

    return output


def calculate_landsat_reflectance(src_paths, src_mtl, dst_path, rescale_factor,
                                  creation_options, bands, dst_dtype,
                                  processes, pixel_sunangle):
    """
    Parameters
    ------------
    src_path: string
    src_mtl: string

    Returns
    ---------
    out: None
        Output is written to dst_path
    """
    mtl = toa_utils._load_mtl(src_mtl)
    metadata = mtl['L1_METADATA_FILE']

    M = [metadata['RADIOMETRIC_RESCALING']
         ['REFLECTANCE_MULT_BAND_{}'.format(b)]
         for b in bands]
    A = [metadata['RADIOMETRIC_RESCALING']
         ['REFLECTANCE_ADD_BAND_{}'.format(b)]
         for b in bands]

    E = metadata['IMAGE_ATTRIBUTES']['SUN_ELEVATION']
    date_collected = metadata['PRODUCT_METADATA']['DATE_ACQUIRED']
    time_collected_utc = metadata['PRODUCT_METADATA']['SCENE_CENTER_TIME']

    dst_dtype = np.__dict__[dst_dtype]

    for src_path in src_paths:
        with rio.open(src_path) as src:
            dst_profile = src.profile.copy()
            src_nodata = src.nodata

            for co in creation_options:
                dst_profile[co] = creation_options[co]

            dst_profile['dtype'] = dst_dtype

    global_args = {
        'A': A,
        'M': M,
        'E': E,
        'src_nodata': 0,
        'src_crs': dst_profile['crs'],
        'dst_dtype': dst_dtype,
        'rescale_factor': rescale_factor,
        'pixel_sunangle': pixel_sunangle,
        'date_collected': date_collected,
        'time_collected_utc': time_collected_utc,
        'bands': len(bands)
    }

    dst_profile.update(count=len(bands))

    if len(bands) == 3:
        dst_profile.update(photometric='rgb')
    else:
        dst_profile.update(photometric='minisblack')

    with riomucho.RioMucho(list(src_paths),
                           dst_path,
                           _reflectance_worker,
                           options=dst_profile,
                           global_args=global_args,
                           mode='manual_read') as rm:

        rm.run(processes)
