# GDPR compliant slippy maps from OpenStreetMap data
This archive contains a javascript module for displaying a slippy map made up of locally stored tiles 
and a command line python tool for downloading the necessary tiles from a local tile server.

A german article is available online:

[https://beltoforion.de/de/openstreetmap-dsgvo](https://beltoforion.de/de/openstreetmap-dsgvo)

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

If you follow these instructions you should be able to see the output from the tileserver by navigating to the 
address: http://127.0.0.1/sample_leaflet.html

![lokaler-tileserver-im-browser](https://github.com/user-attachments/assets/3ad8e2b3-d12a-4c13-b257-666d382049cc)

## Step 2: Create the tiles for your slippy map

Use the python script tile_downloader.py for rendering tiles for your target area. Specify the geographic coordinates, the desired zoom levels and the output folder.

```bash
python tile_downloader.py \
    --min-lat 50.0 \
    --max-lat 51.0 \
    --min-lon 13.0 \
    --max-lon 14.0 \
    --zoom 11 12 13 \
    --output ./osm_tiles
```

## Step 3: Adding the slippy map to your HTML

### Create a map container and load osm-map-bundle.js

```html
<div id="map" style="height:750px; width:750px;"></div>
<link rel="stylesheet" href="ol.css" />
<script src="osm-map-bundle.js"></script>
```

### Initialize and set up the map

```html
<script>
const map = new GpxOsmMap.OsmMap('map');
map.setView([50.963785, 13.343821], 10, 16, 15);
map.addTileLayer('./osm_tiles/{z}/{x}/{y}.png');

// Add GPX layers
map.addGpxLayer('rothschönberger-stolln.gpx', '#f00', 4);
map.addGpxLayer('kurprinzkanal.gpx', '#55f', 2);

var jsonStyles = {
	'PointMarker': new GpxOsmMap.AnnotatedPointStyle('pointMarker', '#ff0')
};

var jsonData = {
	"type": "FeatureCollection",
	"crs": {
		"type": "name",
		"properties": { "name": "urn:ogc:def:crs:OGC:1.3:CRS84" }
	},
	"features": [
		{
			"type": "Feature",
			"properties": { 
				"name": "7. Lichtloch", 
				"type": "PointMarker" 
			},
			"geometry": {
				"type": "Point",
				"coordinates": [13.343821, 50.963785]
			}
		},
		{
			"type": "Feature",
			"properties": { 
				"name": "8. Lichtloch", 
				"type": "PointMarker" 
			},
			"geometry": {
				"type": "Point",
				"coordinates": [13.348811, 50.958655]
			}
		}
    ]
};

map.addJsonLayer(jsonData, jsonStyles);
</script>
```
