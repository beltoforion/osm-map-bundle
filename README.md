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

If you follow these instructions you should be able to see the output from the tileserver by navigating to the 
address: http://127.0.0.1/sample_leaflet.html

![lokaler-tileserver-im-browser](https://github.com/user-attachments/assets/3ad8e2b3-d12a-4c13-b257-666d382049cc)

## Step 2: Create the tiles for your slippy map

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

## Step 3: Adding the slippy map to your HTML

### Create a map container and load osm-map-bundle.js

```
<div id="map" style="height:750px; width:750px;"></div>
<link rel="stylesheet" href="ol.css" />
<script src="osm-map-bundle.js"></script>
```

### Initialize and set up the map

```
<script>
const config = new GpxOsmMap.GpxOsmMapConfig(
    'map',                  // Map container ID
    13.3604225,             // Longitude (center)
    50.9951988,             // Latitude (center)
    "./osm_tiles"           // Path to local tiles
);

// Set zoom level configurations
config.setZoom(14, 19, 14); // Min, max, and initial zoom levels

// Optional: Add GPX layers for tracks
config.setGpxLayers([
  { url: 'grabentour.gpx', color: '#f00', width: 4 }
]);

// Optional: Add annotation points with names and coordinates
config.setAnnotationLayer({
	"type": "FeatureCollection",
	"features": [
	{ 
		"type": "Feature", 
		"properties": { "name": "Wünschmannmühle" }, 
		"geometry": { 
			"type": "Point", 	
			"coordinates": [13.370541, 50.985271] 
		}
	},
	{ 
		"type": "Feature", 
		"properties": { "name": "4. Lichtloch" }, 
		"geometry": { 
			"type": "Point", 
			"coordinates": [13.366876, 51.007467] 
		}
	}]
});

const map = new GpxOsmMap.GpxOsmMap(config);
</script>
```
