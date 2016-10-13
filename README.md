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

Tests can be run directly from the VM:
```bash
$ docker-compose exec geop python tests.py
```

### Examples
#### Request a count

Request a frequency count of cell values around Philadelphia, PA. POST a JSON configuration which has
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
            [ -75.26870727539062, 39.876546372401194 ],
            [ -75.26870727539062, 40.05127080263306 ],
            [ -75.03868103027344, 40.05127080263306 ],
            [ -75.03868103027344, 39.876546372401194 ],
            [ -75.26870727539062, 39.876546372401194 ]
          ]
        ]
      }
}' "http://localhost:8080/counts"
```

where `nlcd/nlcd_2011...10_10.img` can be any EPSG:5070 raster in the `DATA_DIR` directory.

Returns:

```json
{
  "cellCount": 425199,
  "counts": {
    "11": 31371,
    "21": 55497,
    "22": 64413,
    "23": 125696,
    "24": 114420,
    "31": 380,
    "41": 18562,
    "42": 127,
    "43": 1102,
    "52": 1206,
    "71": 752,
    "81": 1240,
    "82": 503,
    "90": 5675,
    "95": 4255
  },
  "time": 0.04755900000000013
}
```

#### Request a count with modifications applied to the source raster
Adding an additional key to the JSON payload above, one can alter the value of the raster that the operation is being performed on, prior to analysis.  Add a `modifications` key like the following:
```json
"modifications": [
    {
        "geom": {
            "type": "Polygon",
            "coordinates": [
                [
                    [ -75.16571044921875, 39.95975404544819 ],
                    [ -75.16571044921875, 39.983960059494684 ],
                    [ -75.13481140136719, 39.983960059494684 ],
                    [ -75.13481140136719, 39.95975404544819 ],
                    [ -75.16571044921875, 39.95975404544819 ]
                ]
            ]
        },
        "newValue": 255
    },
    {
        "geom": {
            "type": "Polygon",
            "coordinates": [
                [
                    [ -75.26321411132812, 40.01604611654875 ],
                    [ -75.26321411132812, 40.042334918180536 ],
                    [ -75.22956848144531, 40.042334918180536 ],
                    [ -75.22956848144531, 40.01604611654875 ],
                    [ -75.26321411132812, 40.01604611654875 ]
                ]
            ]
        },
        "newValue": 200
    },
    {
        "geom": {
            "type": "Polygon",
            "coordinates": [
                [
                    [ -75.08399963378906, 39.882342585755744 ],
                    [ -75.08399963378906, 39.90657598772841 ],
                    [ -75.05104064941405, 39.90657598772841 ],
                    [ -75.05104064941405, 39.882342585755744 ],
                    [ -75.08399963378906, 39.882342585755744 ]
                ]
            ]
        },
        "newValue": 150
    }
]
```

and the value of `newValue` will be applied to the raster where it intersects with the corresponding polygon, before analysis.  The total cell count will not increase, since old values are replaced by new ones.

```json
{
  "cellCount": 425199,
  "counts": {
    "11": 31074,
    "21": 49731,
    "22": 58613,
    "23": 119795,
    "24": 109322,
    "31": 371,
    "41": 15794,
    "42": 81,
    "43": 833,
    "52": 1160,
    "71": 747,
    "81": 1240,
    "82": 503,
    "90": 5436,
    "95": 4219,
    "150": 8648,
    "200": 9538,
    "255": 8094
  },
  "time": 0.05383799999999983
}
```

#### Sample a raster value at a given coordinate
Example query config:
```json
{
    "rasters": ["nlcd/nlcd_2011_landcover_2011_edition_2014_10_10.img"],
    "queryPolygon":

     {
        "type": "Point",
        "coordinates": [
          -75.31883239746094,
          39.84492203964992
        ]
      }

}
```
output:

```json
{
  "time": 0.034891000000000005,
  "value": 11
}
```

#### Requesting stats for a given area
Apply the same request configuration to the `/stats/<min|max|mean|stddev>` endpoint to receive the result of that statistical analysis over the supplied `geom`:
```json
{
  "stat": "stddev",
  "time": 0.06605499999999997,
  "value": 12.477841682004621
}
```

#### Rendering a raster as image tiles
Currently, a hard coded path to the NLCD raster, reprojected into EPSG:3857 (web mercator) is used at the endpoint:
`http://localhost:8080/nlcd/{z}/{x}/{y}.png`

You'll need a file name `nlcd/nlcd_webm.tif` in the `DATA_DIR` to use this endpoint. It will render resampled tiles as overlays for a common Leaflet map, using the default color scheme defined inside of the raster as a ColorTable.

To do some processing on a visual tile before rendering, try the example endpoint:
`http://localhost:8080/nlcd-grouped/{z}/{x}/{y}.png`
which reclassifies NLCD codes into aggregate groups on the fly before rendering.

To test, try the following:
* Visit [http://geojson.io](http://geojson.io)
* Meta -> Add Map Layer
* Paste in one of the above URL templates into the box
* Browse the continental USA to see the overlay applied

#### Sample Rasters
The 2011 NLCD is a 30m conterminous raster that is in an equal area projection (EPSG:5070).  It can be downloaded for free:

[http://www.landfire.gov/bulk/downloadfile.php?TYPE=nlcd2011&FNAME=nlcd_2011_landcover_2011_edition_2014_10_10.zip](http://www.landfire.gov/bulk/downloadfile.php?TYPE=nlcd2011&FNAME=nlcd_2011_landcover_2011_edition_2014_10_10.zip)
The zip file is approximately 1.1GB.

Unzipped, the raster content is approximately 18GB and in the IMG format, which rasterio can read natively.
