import re, json, itertools

def _parse_band_from_filename(filename):
    band = re.findall('.*\L\_[0-9]+.(tif|TIF)', filename)

    return band

def _load_mtl_key(mtl, keys, band, join_last_with_band=True):
    keys = list(keys)
    if join_last_with_band:
        keys[-1] = '%s%s' % (keys[-1], band)
    base = mtl
    for k in keys:
        base = base[k]

    return base

def _load_mtl(src_mtl):
    with open(src_mtl) as src:
        return json.loads(src.read())