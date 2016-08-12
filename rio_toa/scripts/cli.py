
import logging

import click
import json
import re
from rasterio.rio.options import creation_options
from rio_toa.radiance import calculate_landsat_radiance
from rio_toa.reflectance import calculate_landsat_reflectance
from rio_toa.brightness_temp import calculate_landsat_brightness_temperature
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
@click.option('--dst-dtype',
              type=click.Choice(['uint16', 'uint8']),
              default='uint16',
              help='Output data type')
@click.option('--rescale-factor', '-r',
              type=float,
              default=float(55000.0/2**16),
              help='Rescale post-TOA tifs to 55,000 or to full 16-bit')
@click.option('--readtemplate', '-t', default=".*/LC8.*\_B{b}.TIF",
              help="File path template [Default ='.*/LC8.*\_B{b}.TIF']")
@click.option('--workers', '-j', type=int, default=4)
@click.option('--l8-bidx', default=0, type=int,
              help="L8 Band that the src_path represents"
              "(Default is parsed from file name)")
@click.option('--verbose', '-v', is_flag=True, default=False)
@click.pass_context
@creation_options
def radiance(ctx, src_path, src_mtl, dst_path, rescale_factor,
             readtemplate, verbose, creation_options, l8_bidx,
             dst_dtype, workers):
    """Calculates Landsat8 Surface Radiance
    """
    if verbose:
        logger.setLevel(logging.DEBUG)

    if l8_bidx == 0:
        l8_bidx = _parse_bands_from_filename([src_path], readtemplate)[0]

    calculate_landsat_radiance(src_path, src_mtl, dst_path,
                               rescale_factor, creation_options, l8_bidx,
                               dst_dtype, workers)


@click.command('reflectance')
@click.argument('src_paths', nargs=-1, type=click.Path(exists=True))
@click.argument('src_mtl', type=click.Path(exists=True))
@click.argument('dst_path', type=click.Path(exists=False))
@click.option('--dst-dtype',
              type=click.Choice(['uint16', 'uint8']),
              default='uint16',
              help='Output data type')
@click.option('--rescale-factor', '-r',
              type=float,
              default=float(55000.0/2**16),
              help='Rescale post-TOA tifs to 55,000 or to full 16-bit')
@click.option('--readtemplate', '-t', default=".*/LC8.*\_B{b}.TIF",
              help="File path template [Default ='.*/LC8.*\_B{b}.TIF']")
@click.option('--workers', '-j', type=int, default=4)
@click.option('--l8-bidx', default=0, type=int,
              help="L8 Band that the src_path represents"
              "(Default is parsed from file name)")
@click.option('--verbose', '-v', is_flag=True, default=False)
@click.option('--pixel-sunangle', '-p', is_flag=True, default=False,
              help="Per pixel sun elevation")
@click.pass_context
@creation_options
def reflectance(ctx, src_paths, src_mtl, dst_path, dst_dtype,
                rescale_factor, readtemplate, workers, l8_bidx,
                verbose, creation_options, pixel_sunangle):
    """Calculates Landsat8 Surface Reflectance
    """
    if verbose:
        logger.setLevel(logging.DEBUG)

    if l8_bidx == 0:
        l8_bidx = _parse_bands_from_filename(list(src_paths), readtemplate)

    calculate_landsat_reflectance(list(src_paths), src_mtl, dst_path,
                                  rescale_factor, creation_options,
                                  list(l8_bidx), dst_dtype,
                                  workers, pixel_sunangle)


@click.command('brighttemp')
@click.argument('src_path', type=click.Path(exists=True))
@click.argument('src_mtl', type=click.Path(exists=True))
@click.argument('dst_path', type=click.Path(exists=False))
@click.option('--dst-dtype', '-d',
              type=click.Choice(['float32', 'float64', 'uint16', 'uint8']),
              default='float32',
              help='Output data type')
@click.option('--temp_scale', '-s',
              type=click.Choice(['K', 'F', 'C']),
              default='K',
              help='Temperature scale [Default = K (Kelvin)]')
@click.option('--readtemplate', '-t', default=".*/LC8.*\_B{b}.TIF",
              help="File path template [Default ='.*/LC8.*\_B{b}.TIF']")
@click.option('--workers', '-j', type=int, default=4)
@click.option('--thermal-bidx', default=0, type=int,
              help="L8 thermal band that the src_path represents"
              "(Default is parsed from file name)")
@click.option('--verbose', '-v', is_flag=True, default=False)
@click.pass_context
@creation_options
def brighttemp(ctx, src_path, src_mtl, dst_path, dst_dtype,
               temp_scale, readtemplate, workers,
               thermal_bidx, verbose, creation_options):
    """Calculates Landsat8 at-satellite brightness temperature.
    TIRS band data can be converted from spectral radiance
    to brightness temperature using the thermal
    constants provided in the metadata file:
    """

    if verbose:
        logger.setLevel(logging.DEBUG)

    if thermal_bidx == 0:
        thermal_bidx = _parse_bands_from_filename([src_path], readtemplate)[0]

    calculate_landsat_brightness_temperature(
        src_path, src_mtl, dst_path, temp_scale,
        creation_options, thermal_bidx, dst_dtype, workers)


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
toa.add_command(brighttemp)
toa.add_command(parsemtl)
