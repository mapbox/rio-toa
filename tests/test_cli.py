import os

from click.testing import CliRunner
import logging
import pytest
import rasterio

from rasterio.rio.options import creation_options
from rio_toa.scripts.cli import radiance, reflectance, parsemtl


def test_cli_radiance(tmpdir):
    output = str(tmpdir.join('toa_radiance.tif'))
    runner = CliRunner()
    result = runner.invoke(radiance, 
        ['tests/data/tiny_LC80100202015018LGN00_B1.TIF',
         'tests/data/LC80100202015018LGN00_MTL.json',
         output])
    assert result.exit_code == 0
    assert os.path.exists(output)


def test_cli_reflectance(tmpdir):
    output = str(tmpdir.join('toa_reflectance.tif'))
    runner = CliRunner()
    result = runner.invoke(reflectance, 
        ['tests/data/tiny_LC81390452014295LGN00_B5.TIF',
         'tests/data/LC81390452014295LGN00_MTL.json',
         output])
    assert result.exit_code == 0
    with rasterio.open(output) as out:
        assert out.count == 1
        assert out.dtypes[0] == rasterio.float32


def test_cli_parsemtl(tmpdir):
    runner = CliRunner()
    result = runner.invoke(parsemtl,
        ['tests/data/testmtl_LC80100202015018LGN00_MTL.txt'])
    assert result.exit_code == 0
    assert result.output == '{"L1_METADATA_FILE": {"METADATA_FILE_INFO": '\
                    '{"ORIGIN": "Image courtesy of the U.S. Geological Survey", '\
                    '"LANDSAT_SCENE_ID": "LC80100202015018LGN00", '\
                    '"PROCESSING_SOFTWARE_VERSION": "LPGS_2.4.0", '\
                    '"REQUEST_ID": "0501501184561_00001"}, '\
                    '"PRODUCT_METADATA": {"SCENE_CENTER_TIME": '\
                    '"15:10:22.4142571Z", "DATE_ACQUIRED": "2015-01-18", '\
                    '"DATA_TYPE": "L1T"}}}\n'