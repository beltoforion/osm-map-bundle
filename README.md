# osm-map-bundle
A module for a DSGVO compliant slippy map for geographic data from the Open Street Map project.

This archive contains a javascript module for displaying the map as well as command line python tool 
for downloading the necessary tiles from a local tile server.

## Prerequisites
The slippy map uses Open Layers with locally stored tile files. Before you continue you must have created those tiles.
Please note that you cannot use publicly available tile servers from the Open Street Map project for 
scraping the tiles. This is against their [tile usage policy](https://operations.osmfoundation.org/policies/tiles/).
And the script provided here will not work for that purpose.

I recommend setting up a local tile server as described here:
* https://switch2osm.org/serving-tiles/manually-building-a-tile-server-ubuntu-24-04-lts/
* https://switch2osm.org/serving-tiles/manually-building-a-tile-server-ubuntu-22-04-lts/
