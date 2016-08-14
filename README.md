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

Request a frequency count of cell values in center city Philadelphia. POST a JSON configuration which has
- `rasters`: list of file names in `DATA_DIR`
- `query_polygon`: GeoJSON polygon area of interest

```bash
curl -X POST -H "Content-Type: application/json" -d '{
    "rasters": ["nlcd/nlcd_2011_landcover_2011_edition_2014_10_10.img"],
    "queryPolygon": 
    {
        "type": "Polygon",
        "coordinates": [
          [
            [-75.18768310546875,39.93395994977672],[-75.18768310546875,39.97764627359865],[-75.13412475585938,39.97764627359865],[-75.13412475585938,39.93395994977672],[-75.18768310546875,39.93395994977672]
          ]
        ]
      }
}' "http://localhost:8080/counts"
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
