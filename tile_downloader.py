import os
import math
import argparse
import requests
import random
import time

def deg2tile(lat, lon, zoom):
    """Convert latitude and longitude to tile numbers."""
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    xtile = int((lon + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
    return xtile, ytile

def download_tile(x, y, z, output_dir, url_template, retries=3):
    """Download a single tile with retry logic."""
    url = url_template.format(z=z, x=x, y=y)
    output_path = os.path.join(output_dir, str(z), str(x), f"{y}.png")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    headers = {
        "User-Agent": "TileDownloadForMyWebPage/1.0 (osm_tiles@beltoforion.de)"
    }

    for attempt in range(1, retries + 1):
        print(f"Attempting to download tile: Zoom={z}, X={x}, Y={y}, URL={url} (Attempt {attempt})")
        response = requests.get(url, headers=headers, stream=True)
        if response.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(response.content)
            print(f"Successfully downloaded: {url}")
            return True
        elif response.status_code == 404:
            print(f"Tile not found: {url} (404)")
            break
        else:
            print(f"Failed to download: {url} with status code {response.status_code}")
        
        # Add a delay before retrying
        time_to_wait = random.uniform(1, 3)
        print(f"Waiting {time_to_wait:.2f} seconds before retrying...")
        time.sleep(time_to_wait)

    # Log the missing tile
    log_missing_tile(z, x, y, url)
    return False

def log_missing_tile(z, x, y, url):
    """Log missing tiles to a file."""
    with open("missing_tiles.log", "a") as log_file:
        log_file.write(f"Missing tile: Zoom={z}, X={x}, Y={y}, URL={url}\n")

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
    parser = argparse.ArgumentParser(description="Download tiles for a specified bounding box.")
    parser.add_argument("--min-lat", type=float, default=50.8592, help="Minimum latitude.")
    parser.add_argument("--max-lat", type=float, default=51.0824, help="Maximum latitude.")
    parser.add_argument("--min-lon", type=float, default=13.2701, help="Minimum longitude.")
    parser.add_argument("--max-lon", type=float, default=13.4488, help="Maximum longitude.")
    parser.add_argument("--zoom", nargs="+", type=int, default=list(range(11, 18)),
                        help="Zoom levels to download (e.g., 9 10 11 12).")
    parser.add_argument("--output", default="./dist/osm_tiles", help="Output directory for tiles.")
    parser.add_argument("--url-template", default="http://127.0.0.1/hot/{z}/{x}/{y}.png",
                        help="Tile URL template.")
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
