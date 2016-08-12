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
    except ValueError as err:
        try:
            return key, float(data)
        except ValueError as err:
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


def rescale(arr, rescale_factor, dtype):
    """Convert an array from 0..1 to dtype, scaling up linearly
    """

    if dtype not in [np.uint8, np.uint16]:
        raise ValueError('Rescaling converts to uint{8,16} only')

    arr *= rescale_factor * np.iinfo(dtype).max
    return np.clip(arr, 1, np.iinfo(dtype).max).astype(dtype)


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
