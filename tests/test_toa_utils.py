import pytest
import numpy as np

from rio_toa.toa_utils import (
	_parse_bands_from_filename,
	_load_mtl_key, _load_mtl, rescale)


def test_parse_band_from_filename_good():
	assert _parse_bands_from_filename(['LC81070352015122LGN00_B3.tif'], 'LC8.*_B{b}.tif') == [3]


def test_parse_band_from_filename_bad():
	with pytest.raises(ValueError):
		_parse_bands_from_filename(['LC81070352015122LGN00_B3.tif'], 'LC8NOGOOD.*_B{b}.tif')


def test_load_mtl():
	src_mtl = 'tests/data/LC80100202015018LGN00_MTL.json'
	mtl = _load_mtl(src_mtl)
	assert isinstance(mtl, dict)

def test_load_txt_mtl_1():
	txtmtl = _load_mtl('tests/data/LC81060712016134LGN00_MTL.txt')
	jsonmtl = _load_mtl('tests/data/LC81060712016134LGN00_MTL.json')

	for k in jsonmtl['L1_METADATA_FILE'].keys():
		assert k in txtmtl['L1_METADATA_FILE']
		assert jsonmtl['L1_METADATA_FILE'][k] == txtmtl['L1_METADATA_FILE'][k]


def test_load_txt_mtl_2():
	txtmtl = _load_mtl('tests/data/LC80100202015018LGN00_MTL.txt')
	jsonmtl = _load_mtl('tests/data/LC80100202015018LGN00_MTL.json')

	for k in jsonmtl['L1_METADATA_FILE'].keys():
		assert k in txtmtl['L1_METADATA_FILE']
		assert jsonmtl['L1_METADATA_FILE'][k] == txtmtl['L1_METADATA_FILE'][k]


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

	keys = ['L1_METADATA_FILE', 'TIRS_THERMAL_CONSTANTS','K1_CONSTANT_BAND_']
	K11 = _load_mtl_key(mtl_test, keys, band=11)
	assert K11 == 480.89

	keys2 = ['L1_METADATA_FILE', 'IMAGE_ATTRIBUTES', 'CLOUD_COVER']
	clouds = _load_mtl_key(mtl_test, keys2, band=None)
	assert clouds == 19.74

def test_rescale():
	arr = np.array(np.linspace(0.0, 1.5, num=9).reshape(3,3))
	dtype = 'uint16'
	rescale_factor = 1.0
	rescaled_arr = rescale(arr, rescale_factor, dtype)
	mask = (rescaled_arr != np.iinfo(np.uint16).max) & (rescaled_arr != 1.0)

	assert np.all(rescaled_arr) <= np.iinfo(np.uint16).max
	assert np.all(rescaled_arr) >= 0.0
	assert np.array_equal(rescaled_arr[mask], arr[mask].astype(int))

