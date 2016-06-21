# rio-toa
Top Of Atmosphere (TOA) calculations for Landsat 8

## `CLI`

### `radiance`

```
Usage: rio toa radiance [OPTIONS] SRC_PATH SRC_MTL DST_PATH

  Calculates Landsat8 Surface Radiance

Options:
  --dst-dtype [float32]
  -j, --workers INTEGER
  --l8-bidx INTEGER      L8 Band that the src_path represents (Default is
                         parsed from file name)
  -v, --verbose
  --co NAME=VALUE        Driver specific creation options.See the
                         documentation for the selected output driver for more
                         information.
  --help                 Show this message and exit.
```

### `reflectance`

```
Usage: rio toa reflectance [OPTIONS] SRC_PATH SRC_MTL DST_PATH

  Calculates Landsat8 Surface Reflectance

Options:
  --dst-dtype [float32]  datatype
  -j, --workers INTEGER  number of processes
  --l8-bidx INTEGER      L8 Band that the src_path represents (Default is
                         parsed from file name)
  -v, --verbose          Debugging mode
  --co NAME=VALUE        Driver specific creation options.See the
                         documentation for the selected output driver for more
                         information.
  --help                 Show this message and exit.
  ```