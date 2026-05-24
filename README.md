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
const map = new OsmMap.OsmMap('map');
map.setView([50.963785, 13.343821], 10, 16, 15);
map.addTileLayer('./osm_tiles/{z}/{x}/{y}.png');

// Add GPX layers
map.addGpxLayer('rothschönberger-stolln.gpx', '#f00', 4);
map.addGpxLayer('kurprinzkanal.gpx', '#55f', 2);

var jsonStyles = {
	'PointMarker': new OsmMap.AnnotatedPointStyle('pointMarker', '#ff0')
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

## Step 4: Optional UI helpers

The bundle exposes a few optional helpers for common map UI needs. They are all opt-in — if you
don't call them (or don't add the matching HTML), nothing changes.

### Version number

The current bundle version (taken from `package.json`) is available as `OsmMap.VERSION`:

```js
console.log(OsmMap.VERSION);   // e.g. "1.0.0"
```

### Hiding POI labels below a zoom level

POI text labels (the `name` property of your GeoJSON features) can be hidden when the map is
zoomed out past a configurable threshold — only the markers/icons stay visible, and the labels
reappear as you zoom back in. The default is `0` (always show labels).

```js
map.setLabelMinZoom(15);   // labels are shown from zoom level 15 upwards
```

### Info panel (coordinates, copy button, version) — purely declarative

`map.bindInfoControls()` wires up an optional info panel that you define entirely in your own
HTML. You control the markup, placement and styling; the bundle only attaches the behaviour.
Add any of these `data-*` attributes to elements of your choice:

| Attribute | Behaviour |
| --- | --- |
| `data-osm-version` | element text is set to the bundle version |
| `data-osm-coords` | element text shows the map centre (`lat, lon`), updated on every pan/zoom |
| `data-osm-copy` | clicking copies the current coordinates to the clipboard and dispatches an `osm:copy` event (`detail: { text, ok }`) |

```html
<!-- Place and style this however you like; omit it entirely for no panel -->
<div class="map-info">
  v<span data-osm-version></span>
  <span data-osm-coords>-</span>
  <button data-osm-copy>Copy</button>
</div>

<script>
  map.bindInfoControls();   // wires up the data-osm-* elements above

  // optional: react to the copy event for your own feedback
  document.querySelector('[data-osm-copy]')
    .addEventListener('osm:copy', e => console.log('copied:', e.detail.text, e.detail.ok));
</script>
```

Optional configuration:

```js
map.bindInfoControls({
  format: (lat, lon) => `${lat.toFixed(4)}, ${lon.toFixed(4)}`,  // custom coordinate format
  root: document.getElementById('sidebar'),                      // limit the search to a subtree
});
```

### Shareable position permalinks

`map.bindPermalink()` keeps the current view (zoom + centre) in the URL hash, so a position can be
bookmarked in the browser or shared as a link. The hash uses the common slippy-map format
`#<zoom>/<lat>/<lon>`. On load, an existing hash is applied (overriding the initial `setView`);
on every map move the hash is rewritten via `history.replaceState` (no history entries, no scroll
jump). If there is no hash, the `setView` start position is kept.

```js
map.bindPermalink();   // URL becomes e.g. #16/50.96379/13.34382
```

Optional configuration — attach page-specific state (e.g. the active base layer) to the hash:

```js
map.bindPermalink({
  precision: 5,                                   // decimals for lat/lon (default 5)
  getState: () => ({ layer: layerSelect.value }), // serialised as &layer=... in the hash
  setState: (s) => { if (s.layer) showLayer(s.layer); },  // applied when a hash is loaded
});

// After changing page state that is part of getState() (e.g. switching the layer),
// refresh the hash so the link stays in sync:
layerSelect.onchange = () => { showLayer(layerSelect.value); map.updatePermalink(); };
```

`map.updatePermalink()` is a no-op until `bindPermalink()` has been called.

### Centre crosshair while the map moves

`map.enableCenterCrosshair()` shows a small crosshair at the centre of the map while the map is
being moved (panned/zoomed) and hides it again when the movement ends, so the current centre is
visible. The overlay element is created and appended to the map viewport by the bundle, never
intercepts clicks (`pointer-events: none`), and uses an inline SVG with a halo for contrast on
light and dark tiles. No extra HTML or CSS is required.

```js
map.enableCenterCrosshair();

// optional appearance tweaks:
map.enableCenterCrosshair({ size: 40, color: '#1c1c24', haloColor: '#ffffff' });
```

### Direct access to the OpenLayers map

For anything not covered above, `map.getMap()` returns the underlying
[OpenLayers `Map`](https://openlayers.org/en/latest/apidoc/module-ol_Map-Map.html) instance, so
you can attach your own controls, layers or event handlers.

```js
map.getMap().on('moveend', () => { /* ... */ });
```
