import re, json, itertools

def _parse_band_from_filename(filename):
    band = re.findall('.*\L\_[0-9]+.(tif|TIF)', filename)

    return band

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