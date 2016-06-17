import re

def _parse_band_from_filename(filename):
    band = re.findall('.*\L\_[0-9]+.(tif|TIF)', filename)

    return band

def _parse_mtl(keys, band):
    pass