# simple-raster-processing
A research project into creating a web request raster processing pipeline using open source python tools

### Get started
Start Vagrant by providing it with an ENV which points to a directory on your host which containers GeoTiffs:
```bash
DATA_DIR=~/my/shapes vagrant up
```

### Request a count
```
curl -X POST "http://localhost:8080/counts?filename=<your_file.tiff>"
```

where `<your_file.tiff>` is a GeoTiff in the `DATA_DIR` directory.

Presently, it's assumed that the raster is large enough to have data cells at the window:
`((10000, 10350), (10000, 10350))`
but that's a temporary restriction while this work progresses.
