#!/bin/python3
import os
import math
import argparse
import requests
from PIL import Image
import io

def deg2tile(lat, lon, zoom):
    """Convert latitude and longitude to tile numbers."""
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    xtile = int((lon + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
    return xtile, ytile


def download_tile(x, y, z, output_dir, url_template):
    """Download a single tile with retry logic."""

    url = url_template.format(z=z, x=x, y=y)
    output_path = os.path.join(output_dir, str(z), str(x), f"{y}.webp")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    print(f"Downloading tile: Zoom={z}, X={x}, Y={y}, URL={url} ...", end=" ")
    response = requests.get(url, stream=True)
    if response.status_code == 200:
#        with open(output_path, "wb") as f:
#            f.write(response.content)
        image = Image.open(io.BytesIO(response.content))
        webp_output_path = output_path.replace('.png', '.webp')
        image.save(webp_output_path, 'WEBP')
        print(f"done")
    else:
        raise Exception(f"Failed to download: {url} with status code {response.status_code}")


def main(min_lat, max_lat, min_lon, max_lon, zoom_levels, output_dir, url_template):
    """
    Main function to download tiles for a bounding box.
    The bounding box is defined by min_lat, max_lat, min_lon, max_lon.
    """
    print(f"Bounding box: ({min_lat}, {min_lon}) -> ({max_lat}, {max_lon})")

    for zoom in zoom_levels:
        min_x, max_y = deg2tile(min_lat, min_lon, zoom)
        max_x, min_y = deg2tile(max_lat, max_lon, zoom)

        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                download_tile(x, y, zoom, output_dir, url_template)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download tiles from a OSM Tile server for a specified bounding box.")
    parser.add_argument("--min-lat", type=float, default=50.797, help="Minimum latitude.")
    parser.add_argument("--max-lat", type=float, default=51.0824, help="Maximum latitude.")
    parser.add_argument("--min-lon", type=float, default=13.2701, help="Minimum longitude.")
    parser.add_argument("--max-lon", type=float, default=13.4488, help="Maximum longitude.")
    parser.add_argument("--zoom", nargs="+", type=int, default=list(range(11, 18)),
                        help="Zoom levels to download (e.g., 9 10 11 12).")
    parser.add_argument("--output", default="./dist/osm_tiles", help="Output directory for tiles.")
    parser.add_argument("--url-template", default="http://127.0.0.1/hot/{z}/{x}/{y}.png",
                        help="URL template for querying the tiles from a OSM tile server.")
    args = parser.parse_args()

    main(
        min_lat=args.min_lat,
        max_lat=args.max_lat,
        min_lon=args.min_lon,
        max_lon=args.max_lon,
        zoom_levels=args.zoom,
        output_dir=args.output,
        url_template=args.url_template
    )
