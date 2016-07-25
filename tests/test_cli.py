import os

from click.testing import CliRunner
import logging
import pytest
from click import UsageError
import rasterio
import json

from rasterio.rio.options import creation_options
from rio_toa.scripts.cli import radiance, reflectance, parsemtl


def test_cli_radiance_default(tmpdir):
    output = str(tmpdir.join('toa_radiance.tif'))
    runner = CliRunner()
    result = runner.invoke(radiance, 
        ['tests/data/LC81060712016134LGN00_B3.TIF',
         'tests/data/LC81060712016134LGN00_MTL.json',
         output])
    assert result.exit_code == 0
    assert os.path.exists(output)
    with rasterio.open(output) as out:
        assert out.count == 1
        assert out.dtypes[0] == rasterio.float32

def test_cli_radiance_good(tmpdir):
    output = str(tmpdir.join('toa_radiance.tif'))
    runner = CliRunner()
    result = runner.invoke(radiance, 
        ['tests/data/tiny_LC80100202015018LGN00_B1.TIF',
         'tests/data/LC80100202015018LGN00_MTL.json',
         output, '--readtemplate', '.*/tiny_LC8.*\_B{b}.TIF'])
    assert result.exit_code == 0
    assert os.path.exists(output)
    with rasterio.open(output) as out:
        assert out.count == 1
        assert out.dtypes[0] == rasterio.float32

def test_cli_radiance_fail(tmpdir):
    output = str(tmpdir.join('toa_radiance.tif'))
    runner = CliRunner()
    result = runner.invoke(radiance, 
        ['tests/data/tiny_LC80100202015018LGN00_B1.TIF',
         'tests/data/LC80100202015018LGN00_MTL.json',
         output, '.*/Fail_LC8.*\_B{b}.TIF'])
    assert result.exit_code != 0


def test_cli_reflectance_default(tmpdir):
    output = str(tmpdir.join('toa_reflectance.tif'))
    runner = CliRunner()
    result = runner.invoke(reflectance, 
        ['tests/data/LC81060712016134LGN00_B3.TIF',
         'tests/data/LC81060712016134LGN00_MTL.json',
         output])
    assert result.exit_code == 0
    with rasterio.open(output) as out:
        assert out.count == 1
        assert out.dtypes[0] == rasterio.float32


def test_cli_reflectance_good(tmpdir):
    output = str(tmpdir.join('toa_reflectance_readtemplate.TIF'))
    runner = CliRunner()
    result = runner.invoke(reflectance, 
        ['tests/data/tiny_LC81390452014295LGN00_B5.TIF',
         'tests/data/LC81390452014295LGN00_MTL.json',
         output, '--readtemplate', '.*/tiny_LC8.*\_B{b}.TIF'])
    assert result.exit_code == 0
    with rasterio.open(output) as out:
        assert out.count == 1
        assert out.dtypes[0] == rasterio.float32


def test_cli_reflectance_l8_bidx(tmpdir):
    output = str(tmpdir.join('toa_reflectance.tif'))
    runner = CliRunner()
    result = runner.invoke(reflectance, 
        ['tests/data/tiny_LC81390452014295LGN00_B5.TIF',
         'tests/data/LC81390452014295LGN00_MTL.json',
         output, '--l8-bidx', 'notint'])
    assert result.exit_code != 0
    assert 'Error: Invalid value for "--l8-bidx":' \
           ' notint is not a valid integer\n' in result.output


def test_cli_reflectance_fail(tmpdir):
    output = str(tmpdir.join('toa_reflectance_readtemplate.TIF'))
    runner = CliRunner()
    result = runner.invoke(reflectance, 
        ['tests/data/tiny_LC81390452014295LGN00_B5.TIF',
         'tests/data/LC81390452014295LGN00_MTL.json',
         output])
    assert result.exit_code != 0


def test_cli_reflectance_fail2(tmpdir):
    output = str(tmpdir.join('toa_reflectance_readtemplate.TIF'))
    runner = CliRunner()
    result = runner.invoke(reflectance, 
        ['tests/data/tiny_LC81390452014295LGN00_B5.TIF',
         'tests/data/LC81390452014295LGN00_MTL.json',
         output, '.*/Fail_LC8.*\_B{b}.TIF'])
    assert result.exit_code != 0


def test_cli_reflectance_multiband_stack(tmpdir):
    output = str(tmpdir.join('toa_reflectance_multiband_stack.TIF'))
    runner = CliRunner()
    result = runner.invoke(reflectance,
        ['tests/data/tiny_LC80460282016177LGN00_B2.TIF',
         'tests/data/tiny_LC80460282016177LGN00_B3.TIF',
         'tests/data/tiny_LC80460282016177LGN00_B4.TIF',
         'tests/data/LC80460282016177LGN00_MTL.json',
          output, '-t', '.*/tiny_LC8.*\_B{b}.TIF', '--dst-dtype', 'uint16'])
    assert len(os.listdir(str(tmpdir))) == 1
    assert result.exit_code == 0
    with rasterio.open(output) as out:
        assert out.count == 3
        assert out.dtypes[0] == rasterio.uint16


def test_cli_parsemtl_good(tmpdir):
    runner = CliRunner()
    result = runner.invoke(parsemtl,
        ['tests/data/mtltest_LC80100202015018LGN00_MTL.txt'])
    assert result.exit_code == 0
    assert json.loads(result.output) == dict({"L1_METADATA_FILE": {"METADATA_FILE_INFO":
                    {"ORIGIN": "Image courtesy of the U.S. Geological Survey",
                    "LANDSAT_SCENE_ID": "LC80100202015018LGN00",
                    "PROCESSING_SOFTWARE_VERSION": "LPGS_2.4.0",
                    "REQUEST_ID": "0501501184561_00001"},
                    "PRODUCT_METADATA": {"SCENE_CENTER_TIME":
                    "15:10:22.4142571Z", "DATE_ACQUIRED": "2015-01-18",
                    "DATA_TYPE": "L1T"}}})


def test_cli_parsemtl_fail(tmpdir):
    runner = CliRunner()
    result = runner.invoke(parsemtl,
        ['tests/data/tiny_mtltest_LC80100202015018LGN00_MTL.txt'])
    assert result.exit_code != 0

