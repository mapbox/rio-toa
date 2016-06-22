
import logging

import click, json
from rasterio.rio.options import creation_options
from rio_toa.radiance import calculate_landsat_radiance
from rio_toa.reflectance import calculate_landsat_reflectance
from rio_toa.toa_utils import _parse_bands_from_filename, _parse_mtl_txt

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
@click.option('--dst-dtype', type=click.Choice(['float64']), default='float64')
@click.option('--workers', '-j', type=int, default=4)
@click.option('--l8-bidx', default=0,
    help="L8 Band that the src_path represents (Default is parsed from file name)")
@click.option('--verbose', '-v', is_flag=True, default=False)
@click.pass_context
@creation_options
def radiance(ctx, src_path, src_mtl, dst_path,
         verbose, creation_options, l8_bidx, dst_dtype, workers):
    """Calculates Landsat8 Surface Radiance
    """
    if verbose:
        logger.setLevel(logging.DEBUG)

    if l8_bidx == 0:
        template = '.*\LC8.*_B{b}.TIF'
        l8_bidx = _parse_bands_from_filename([src_path], template)[0]
    elif not isinstance(l8_bidx, int):
        raise ValueError("%s is not a valid integer" % l8_bidx)

    calculate_landsat_radiance(src_path, src_mtl, dst_path, creation_options, l8_bidx, dst_dtype, workers)

@click.command('reflectance')
@click.argument('src_path', type=click.Path(exists=True))
@click.argument('src_mtl', type=click.Path(exists=True))
@click.argument('dst_path', type=click.Path(exists=False))
@click.option('--dst-dtype', type=click.Choice(['float32']), default='float32')
@click.option('--workers', '-j', type=int, default=4)
@click.option('--l8-bidx', default=0,
    help="L8 Band that the src_path represents (Default is parsed from file name)")
@click.option('--verbose', '-v', is_flag=True, default=False)
@click.pass_context
@creation_options
def reflectance(ctx, src_path, src_mtl, dst_path,
         verbose, creation_options, l8_bidx, dst_dtype, workers):
    """Calculates Landsat8 Surface Reflectance
    """
    if verbose:
        logger.setLevel(logging.DEBUG)

    if l8_bidx == 0:
        template =  '.*\LC8.*_B{b}.TIF'
        l8_bidx = _parse_bands_from_filename([src_path], template)[0]
    elif not isinstance(l8_bidx, int):
        raise ValueError("%s is not a valid integer" % l8_bidx)

    calculate_landsat_reflectance(src_path, src_mtl, dst_path, creation_options, l8_bidx, dst_dtype, workers)

@click.command('parsemtl')
@click.argument('mtl', default='-', required=False)
def parsemtl(mtl):
    """Converts a Landsat 8 text MTL
    to JSON
    """
    try:
        mtl = str(click.open_file(mtl).read())
    except IOError:
        mtl = str('\n'.join([inputtiles]))

    click.echo(json.dumps(_parse_mtl_txt(mtl)))


toa.add_command(radiance)
toa.add_command(reflectance)
toa.add_command(parsemtl)