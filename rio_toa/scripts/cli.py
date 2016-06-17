import logging

import click
from rasterio.rio.options import creation_options
from rio_toa.radiance import calculate_landsat_radiance
from rio_toa.toa_utils import _parse_band_from_filename

logger = logging.getLogger('rio_toa')


@click.group('toa')
def toa():
    """Top of Atmosphere (TOA) correction for landsat 8
    """
    pass

@click.command('radiance')
@click.argument('src_path', type=click.Path(exists=True))
@click.argument('src_mtl', type=click.Path(exists=True))
@click.argument('dst_path', type=click.Path(exists=False))
@click.option('--l8-bidx', default=0,
    help="L8 Band that the src_path represents (Default is parsed from file name)")
@click.option('--verbose', '-v', is_flag=True, default=False)
@click.pass_context
@creation_options
def radiance(ctx, src_path, src_mtl, dst_path,
         verbose, creation_options, l8_bidx):
    """Calculates Landsat8 Surface Radiance
    """
    if verbose:
        logger.setLevel(logging.DEBUG)

    if l8_bidx == 0:
        l8_bidx = _parse_band_from_filename(src_path)
    elif not isinstance(l8_bidx, int):
        raise ValueError("%s is not a valid integer" % l8_bidx)

    calculate_landsat_radiance(src_path, src_mtl, dst_path, creation_options)


toa.add_command(radiance)
