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

### `parsemtl`

Takes a file or stdin MTL in txt format, and outputs a json-formatted MTL to stdout

```
Usage: rio toa parsemtl [OPTIONS] [MTL]

  Converts a Landsat 8 text MTL to JSON

Options:
  --help  Show this message and exit.
```
From a local `*_MTL.txt`:
```
rio toa parsemtl tests/data/LC81060712016134LGN00_MTL.txt
```
From stdin:
```
cat tests/data/LC81060712016134LGN00_MTL.txt | rio toa parsemtl
```
From stdin on `s3`:
```
aws s3 cp s3://landsat-pds/L8/106/071/LC81060712016134LGN00/LC81060712016134LGN00_MTL.txt - | rio toa parsemtl
```
