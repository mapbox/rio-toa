import os
import sys
from setuptools import setup, find_packages
from setuptools.extension import Extension

# Parse the version from the fiona module.
with open('rio_toa/__init__.py') as f:
    for line in f:
        if line.find("__version__") >= 0:
            version = line.split("=")[1].strip()
            version = version.strip('"')
            version = version.strip("'")
            break

long_description = """"""


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(name='rio-toa',
      version=version,
      description=u"Top Of Atmosphere (TOA) calculations for Landsat 8",
      long_description=long_description,
      classifiers=[],
      keywords='',
      author=u"Damon Burgett",
      author_email='damon@mapbox.com',
      url='https://github.com/mapbox/rio-toa',
      license='BSD',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=["click", "rasterio", "rio-mucho"],
      extras_require={
          'test': ['pytest', 'hypothesis', 'pytest-cov', 'codecov']},
      entry_points="""
      [rasterio.rio_plugins]
      toa=rio_toa.scripts.cli:toa
      """
      )
