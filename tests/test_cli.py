import os

import click.testing import CliRunner
import logging
import pytest
import rasterio

from rasterio.rio.options import creation_options
from rio_toa.scripts.cli import radiance, reflectance, parsemtl


def test_cli(tmpdir):
	output = str(tmpdir.joins('toa_radiance.tif'))
	runner = CliRunner()
	result = runner.invoke(radiance, 
		['tests/data/tiny_LC80100202015018LGN00_B1.TIF',
		 'tests/data/LC80100202015018LGN00_MTL.json',
		 output])
	assert result.exit_code == 0
	assert os.path.exists(output)

def test_cli2(tmpdir):
	output = str(tmpdir.joins('toa_radiance.tif'))
	runner = CliRunner()
	result = runner.invoke(radiance, 
		['tests/data/tiny_LC81390452014295LGN00_B5.TIF',
		 'tests/data/LC81390452014295LGN00_MTL.json ',
		 output])
	assert result.exit_code == 0
    with rasterio.open(output) as out:
    	assert out.count == 1
    	assert out.dtype == "float32"


# WIP