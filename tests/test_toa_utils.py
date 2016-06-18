import re, json, itertools
import pytest

from rio_toa.toa_utils import (
	_parse_band_from_filename, _load_mtl_key, _load_mtl)

def test_parse_band_from_filename():
	b = _parse_band_from_filename("LC80380312015230LGN00_B1.tif")
    with pytest.raises(AttributeError):
        date("foofoo")

def test_load_mtl():
	src_mtl = 'tests/data/LC80100202015018LGN00_MTL.json'
	mtl = _load_mtl(src_mtl)
	assert type(mtl) == dict

def test_load_mtl_key():
	mtl_test = {u'L1_METADATA_FILE': {u'IMAGE_ATTRIBUTES': 
				 {u'CLOUD_COVER': 19.74,
				  u'SUN_AZIMUTH': 164.19023018},
			    u'TIRS_THERMAL_CONSTANTS':
				 {u'K1_CONSTANT_BAND_10': 774.89, 
				  u'K1_CONSTANT_BAND_11': 480.89},
			    u'RADIOMETRIC_RESCALING':
				 {u'RADIANCE_ADD_BAND_1': -64.85281,
				  u'RADIANCE_MULT_BAND_1': 0.012971}}}

	keys = ['L1_METADATA_FILE', 'TIRS_THERMAL_CONSTANTS','K1_CONSTANT_BAND_11',
			11]
	K11 = _load_mtl_key(mtl, keys, band=None)
	assert K11 == 480.89
	keys2 = ['L1_METADATA_FILE', 'IMAGE_ATTRIBUTES', 'CLOUD_COVER']
	clouds = _load_mtl_key(mtl, keys2, band=None)
	assert clouds == 19.74


