import json, re

def _parse_bands_from_filename(filenames, template):
    tomatch = re.compile(template.replace('{b}', '([0-9]+?)'))
    bands = []
    for f in filenames:
        if not tomatch.match(f):
            raise ValueError('%s is not a valid template for %s' % (template, ', '.join(filenames)))
        bands.append(int(tomatch.findall(f)[0]))

    return bands


def _load_mtl_key(mtl, keys, band=None):
    """
    Loads metadata from a Landsat MTL dict based on an arbitrary set of keys

    Parameters
    -----------
    mtl: dict
        parsed Landsat 8 MTL metadata
    keys: iterable
        an interable of arbitrary length that contains
        successive dict hashes for mtl
    band: int
        band number to join to last key value.
        ignored if None or if not int

    Returns
    --------
    output: any value or object
        the resulting value or object
        from key hash succession
    """
    keys = list(keys)

    if band != None and isinstance(band, int):
        keys[-1] = '%s%s' % (keys[-1], band)

    # for each key, the mtl is winnowed down by each key hash
    for k in keys:
        mtl = mtl[k]

    return mtl


def _load_mtl(src_mtl):
    with open(src_mtl) as src:
        return json.loads(src.read())


def _get_bounds_from_metadata(product_metadata):
    corners = ['LL', 'LR', 'UR', 'UL']
    lats = [product_metadata["CORNER_{}_LAT_PRODUCT".format(i)] for i in corners]
    lngs = [product_metadata["CORNER_{}_LON_PRODUCT".format(i)] for i in corners]

    return [min(lngs), min(lats), max(lngs), max(lats)]

