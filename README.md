# GDPR compliant slippy maps from OpenStreetMap data
This archive contains a javascript module for displaying a slippy map made up of locally stored tiles 
and a command line python tool for downloading the necessary tiles from a local tile server.

Pros:
- Tiles are prerendered and served from a local folder in your own webspace
- No connection to a third party tile server is necessary
- No cookies necessary

Cons:
- Storing tiles locally may require a lot of space

## Step 1: Set up a local tile server 
The slippy map uses Open Layers with locally stored tile files. Therefore the first step is creating 
the tiles. Please note that you cannot use publicly available tile servers from the Open Street Map project for 
scraping the tiles. This is against their [tile usage policy](https://operations.osmfoundation.org/policies/tiles/).
The script provided here will not work for that purpose.

I recommend setting up a local tile server as described here:
* https://switch2osm.org/serving-tiles/manually-building-a-tile-server-ubuntu-24-04-lts/
* https://switch2osm.org/serving-tiles/manually-building-a-tile-server-ubuntu-22-04-lts/

## Step 2: Create the tiles for your map

Use the python script tile_downloader.py for rendering tiles for your target area. Specify the geographic coordinates, the desired zoom levels and the output folder.

```
python tile_downloader.py \
    --min-lat 50.0 \
    --max-lat 51.0 \
    --min-lon 13.0 \
    --max-lon 14.0 \
    --zoom 11 12 13 \
    --output ./osm_tiles
```
