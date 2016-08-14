# simple-raster-processing
A research project into creating a web request raster processing pipeline using open source python tools.

### Get started
Start Vagrant by providing it with an `ENV` which points to a directory on your host that contains geographic rasters:
```bash
DATA_DIR=~/my/shapes vagrant up
```

Next, ssh into vagrant, build the Docker container and start it to expose the analysis API:
```bash
$ vagrant ssh
$ docker-compose build
$ docker-compose up
```
The API is now exposed to your host on `:8080`

### Request a count

Request a frequency count of cell values in center city Philadelphia:
```bash
curl -X POST \
    -H "Content-Type: application/json" \
    -d '{"type":"MultiPolygon","coordinates":[[[[-75.1626205444336,39.95580659996906],[-75.25531768798828,39.94514735903112],[-75.22785186767578,39.89446035777916],[-75.1461410522461,39.88761144548104],[-75.09309768676758,39.91078961774283],[-75.09464263916016,39.93817189499188],[-75.12039184570312,39.94435771955196],[-75.1626205444336,39.95580659996906]]]]}' \
    "http://localhost:8080/counts?filename=nlcd/nlcd_2011_landcover_2011_edition_2014_10_10.img"
```

where `nlcd/nlcd_2011...10_10.img` can be any EPSG:5070 raster in the `DATA_DIR` directory.

Returns:
```json
{
  "cellCount": 86438,
  "counts": {
    "11": 7657,
    "21": 5623,
    "22": 6559,
    "23": 25122,
    "24": 39262,
    "31": 24,
    "41": 710,
    "43": 22,
    "52": 24,
    "71": 129,
    "81": 292,
    "82": 44,
    "90": 617,
    "95": 353
  },
  "time": 0.041381
}
```
#### Sample Rasters
The 2011 NLCD is a 30m conterminous raster that is in an equal area projection (EPSG:5070).  It can be downloaded for free:

[http://www.landfire.gov/bulk/downloadfile.php?TYPE=nlcd2011&FNAME=nlcd_2011_landcover_2011_edition_2014_10_10.zip](http://www.landfire.gov/bulk/downloadfile.php?TYPE=nlcd2011&FNAME=nlcd_2011_landcover_2011_edition_2014_10_10.zip)
The zip file is approximately 1.1GB.

Unzipped, the raster content is approximately 18GB and in the IMG format, which rasterio can read natively.
