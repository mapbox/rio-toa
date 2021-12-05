import json
import re

import numpy as np


def _parse_bands_from_filename(filenames, template):
    tomatch = re.compile(template.replace('{b}', '([0-9]+?)'))
    bands = []
    for f in filenames:
        if not tomatch.match(f):
            raise ValueError('%s is not a valid template for %s'
                             % (template, ', '.join(filenames)))
        bands.append(int(tomatch.findall(f)[0]))

    return bands


def _load_mtl_key(mtl, keys, band=None):
    """
    Loads requested metadata from a Landsat MTL dict

    Parameters
    -----------
    mtl: dict
        parsed Landsat 8 MTL metadata
    keys: iterable
        a list containing arbitrary keys to load from the MTL
    band: int
        band number to join to last key value
        (ignored if not int)

    Returns
    --------
    output: any value
        the value corresponding to the provided key in the MTL
    """
    keys = list(keys)

    if isinstance(band, int):
        keys[-1] = '%s%s' % (keys[-1], band)

    # for each key, the mtl is windowed down by each key hash
    for k in keys:
        mtl = mtl[k]

    return mtl


def _load_mtl(src_mtl):
    with open(src_mtl) as src:
        if src_mtl.split('.')[-1] == 'json':
            return json.loads(src.read())
        else:
            return _parse_mtl_txt(src.read())


def _parse_mtl_txt(mtltxt):
    group = re.findall('.*\n', mtltxt)

    is_group = re.compile(r'GROUP\s\=\s.*')
    is_end = re.compile(r'END_GROUP\s\=\s.*')
    get_group = re.compile('\=\s([A-Z0-9\_]+)')

    output = [{
            'key': 'all',
            'data': {}
        }]

    for g in map(str.lstrip, group):
        if is_group.match(g):
            output.append({
                    'key': get_group.findall(g)[0],
                    'data': {}
                })

        elif is_end.match(g):
            endk = output.pop()
            k = u'{}'.format(endk['key'])
            output[-1]['data'][k] = endk['data']

        else:
            k, d = _parse_data(g)
            if k:
                k = u'{}'.format(k)
                output[-1]['data'][k] = d

    return output[0]['data']


def _cast_to_best_type(kd):
    key, data = kd[0]
    try:
        return key, int(data)
    except ValueError:
        try:
            return key, float(data)
        except ValueError:
            return key, u'{}'.format(data.strip('"'))


def _parse_data(line):
    kd = re.findall(r'(.*)\s\=\s(.*)', line)

    if len(kd) == 0:
        return False, False
    else:
        return _cast_to_best_type(kd)


def _get_bounds_from_metadata(product_metadata):
    corners = ['LL', 'LR', 'UR', 'UL']
    lats = [product_metadata["CORNER_{}_LAT_PRODUCT".format(i)]
            for i in corners]
    lngs = [product_metadata["CORNER_{}_LON_PRODUCT".format(i)]
            for i in corners]

    return [min(lngs), min(lats), max(lngs), max(lats)]


def rescale(arr, rescale_factor, dtype, clip=True):
    """Convert an array from 0..1 to dtype, scaling up linearly
    """
    arr = arr.copy()  # avoid mutating the original data
    if clip:
        arr[arr < 0.0] = 0.0
        arr[arr > 1.0] = 1.0
    arr *= rescale_factor

    # check overflow if destination is int/uint and not clipped
    if not clip and np.issubdtype(dtype, np.integer):
        if arr.max() > np.iinfo(dtype).max or \
           arr.min() < np.iinfo(dtype).min:
            raise ValueError(
                "Cannot safely cast to {} without losing data"
                "; Reduce the --rescaling-factor or use --clip".format(dtype))

    return arr.astype(dtype)


def temp_rescale(arr, temp_scale):
    if temp_scale == 'K':
        return arr

    elif temp_scale == 'F':
        return arr * (9 / 5.0) - 459.67

    elif temp_scale == 'C':
        return arr - 273.15

    else:
        raise ValueError('%s is not a valid temperature scale'
                         % (temp_scale))


def normalize_scale(rescale_factor, dtype):
    default_scales = {
        'uint8': 255,
        'uint16': 65535,
        'float32': 1.0}

    if not rescale_factor:
        try:
            rescale_factor = default_scales[dtype]
        except KeyError:
            rescale_factor = 1.0

    return rescale_factor


# Parse MTL data keys and values for calculations

def _get_all_keys(nested_dict: dict, search_key: str):
    """
    Function iterates through a given dictionary and compares all keys within it to the search_key string,
        if search_key is within a key then function returns this key and its value. It could return multiple pairs.

    Parameters
    ----------
    nested_dict: dict
        parsed mtl file dict
    search_key: specific key to find within a dict

    Returns: dict
    -------

    """

    for key, value in nested_dict.items():
        if type(value) is dict:
            yield from _get_all_keys(value, search_key)
        else:
            if search_key in key:
                yield (key, value)


def get_date_acquired(mtl_dict: dict) -> list:
    date_acquired_str = 'DATE_ACQUIRED'
    date_acquired = [[key, value] for key, value in _get_all_keys(mtl_dict, date_acquired_str)]
    return date_acquired[0]


def get_k1_thermal_c(mtl_dict: dict) -> list:
    k1_const_str = 'K1_CONSTANT_BAND_'
    k1_consts = [[key, value] for key, value in _get_all_keys(mtl_dict, k1_const_str)]
    return k1_consts


def get_k2_thermal_c(mtl_dict: dict) -> list:
    k2_const_str = 'K2_CONSTANT_BAND_'
    k2_consts = [[key, value] for key, value in _get_all_keys(mtl_dict, k2_const_str)]
    return k2_consts


def get_radiance_add_factors(mtl_dict: dict) -> list:
    radiance_add_str = 'RADIANCE_ADD_BAND_'
    radiance_add_factors = [[key, value] for key, value in _get_all_keys(mtl_dict, radiance_add_str)]
    return radiance_add_factors


def get_radiance_mult_factors(mtl_dict: dict) -> list:
    radiance_mult_str = 'RADIANCE_MULT_BAND_'
    radiance_mult_factors = [[key, value] for key, value in _get_all_keys(mtl_dict, radiance_mult_str)]
    return radiance_mult_factors


def get_reflectance_add_factors(mtl_dict: dict) -> list:
    reflectance_add_str = 'REFLECTANCE_ADD_BAND_'
    reflectance_add_factors = [[key, value] for key, value in _get_all_keys(mtl_dict, reflectance_add_str)]
    return reflectance_add_factors


def get_reflectance_mult_factors(mtl_dict: dict) -> list:
    reflectance_mult_str = 'REFLECTANCE_MULT_BAND_'
    reflectance_mult_factors = [[key, value] for key, value in _get_all_keys(mtl_dict, reflectance_mult_str)]
    return reflectance_mult_factors


def get_scene_center_time(mtl_dict: dict) -> list:
    scene_time_str = 'SCENE_CENTER_TIME'
    scene_time = [[key, value] for key, value in _get_all_keys(mtl_dict, scene_time_str)]
    return scene_time[0]


def get_sun_elevation(mtl_dict: dict) -> list:
    sun_elevation_str = 'SUN_ELEVATION'
    sun_elevation = [[key, value] for key, value in _get_all_keys(mtl_dict, sun_elevation_str)]
    return sun_elevation[0]


def get_metadata_parameters(
        mtl_dict: dict,
        date_acquired=True,
        k1_thermal_constants=True,
        k2_thermal_constants=True,
        radiance_add_factors=True,
        radiance_mult_factors=True,
        reflectance_add_factors=True,
        reflectance_mult_factors=True,
        scene_center_time=True,
        sun_elevation=True) -> dict:

    d = {}

    if date_acquired:
        k, v = get_date_acquired(mtl_dict)
        d[k] = v

    if k1_thermal_constants:
        consts = get_k1_thermal_c(mtl_dict)
        for c in consts:
            d[c[0]] = c[1]

    if k2_thermal_constants:
        consts = get_k2_thermal_c(mtl_dict)
        for c in consts:
            d[c[0]] = c[1]

    if radiance_add_factors:
        factors = get_radiance_add_factors(mtl_dict)
        for f in factors:
            d[f[0]] = f[1]

    if radiance_mult_factors:
        factors = get_radiance_mult_factors(mtl_dict)
        for f in factors:
            d[f[0]] = f[1]

    if reflectance_add_factors:
        factors = get_reflectance_add_factors(mtl_dict)
        for f in factors:
            d[f[0]] = f[1]

    if reflectance_mult_factors:
        factors = get_reflectance_mult_factors(mtl_dict)
        for f in factors:
            d[f[0]] = f[1]

    if scene_center_time:
        k, v = get_scene_center_time(mtl_dict)
        d[k] = v

    if sun_elevation:
        k, v = get_sun_elevation(mtl_dict)
        d[k] = v

    return d
