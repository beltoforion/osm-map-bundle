#!/bin/python3
"""
DGM1-Downloader: Laedt die digitalen Gelaendemodelle (DGM1) des Landesamtes
fuer Geobasisinformation Sachsen (GeoSN) automatisiert herunter.

Statt die umstaendliche Karten-Auswahl auf
    https://www.geodaten.sachsen.de/batch-download-4719.html
manuell zu bedienen, gibt man hier einen Laengen-/Breitenbereich an. Das Skript
ermittelt die ueberdeckenden 2x2 km Kacheln, baut die Download-URLs der GeoCloud
und laedt nur die noch fehlenden ZIP-Dateien in einen Cache-Ordner.

Cache-Verhalten:
    Vor jedem Download wird im Cache-Ordner nachgesehen. Liegt die Kachel dort
    bereits als gueltige ZIP-Datei, wird sie uebersprungen. So kostet ein zweiter
    Lauf (z.B. mit groesserem Bereich) nur die wirklich neuen Kacheln.

Datenquelle / URL-Schema (aus dem Batch-Download-Portal abgeleitet):
    https://geocloud.landesvermessung.sachsen.de/public.php/dav/files/<SHARE_ID>/<DATEINAME>
    DATEINAME = dgm1_33<Ostwert_km>_<Nordwert_km>_2_sn_tiff.zip   (gerade km-Werte)
    Koordinatensystem: ETRS89/UTM33 (EPSG:25833). Lizenz: dl-de/by-2-0 (Geodaten Sachsen).

Die Kacheln landen als ZIP im Cache und koennen direkt mit lidar_tiler.py
weiterverarbeitet werden:

    python3 dgm1_downloader.py --min-lat 50.91 --max-lat 50.93 --min-lon 13.32 --max-lon 13.36
    python3 lidar_tiler.py --input ./dgm1_cache --output ./dist/lidar_tiles
"""

import os
import math
import argparse
import zipfile

import requests
from osgeo import osr

# GeoCloud-Share und Dateinamen-Muster je Produkt (aus dem Batch-Download-Portal).
# {e} = Ostwert in km (gerade), {n} = Nordwert in km (gerade).
PRODUCTS = {
    "dgm1": {"share": "JCcXyifaNdLDnxZ", "pattern": "dgm1_33{e}_{n}_2_sn_tiff.zip"},
    "dom1": {"share": "S6wwnFwX7882sZm", "pattern": "dom1_33{e}_{n}_2_sn_tiff.zip"},
}

BASE_URL = "https://geocloud.landesvermessung.sachsen.de/public.php/dav/files"
TILE_KM = 2  # Kachelgroesse in km (2x2 km), ausgerichtet auf gerade km-Werte


def make_transformer():
    """Transformer von WGS84 (Lon/Lat) nach ETRS89/UTM33 (EPSG:25833)."""
    src = osr.SpatialReference()
    src.ImportFromEPSG(4326)
    src.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)  # Eingabe (Lon, Lat)
    dst = osr.SpatialReference()
    dst.ImportFromEPSG(25833)
    dst.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    return osr.CoordinateTransformation(src, dst)


def tiles_for_bbox(min_lat, max_lat, min_lon, max_lon):
    """Liefert die Liste der (Ost_km, Nord_km)-Kacheln, die den Bereich ueberdecken."""
    ct = make_transformer()
    eastings, northings = [], []
    for lon in (min_lon, max_lon):
        for lat in (min_lat, max_lat):
            e, n, _ = ct.TransformPoint(lon, lat)
            eastings.append(e)
            northings.append(n)

    # auf das 2-km-Gitter (gerade km) abrunden bzw. aufrunden
    e0 = int(math.floor(min(eastings) / 2000.0)) * TILE_KM
    e1 = int(math.floor(max(eastings) / 2000.0)) * TILE_KM
    n0 = int(math.floor(min(northings) / 2000.0)) * TILE_KM
    n1 = int(math.floor(max(northings) / 2000.0)) * TILE_KM

    return [(e, n)
            for e in range(e0, e1 + 1, TILE_KM)
            for n in range(n0, n1 + 1, TILE_KM)]


def is_valid_zip(path):
    """True, wenn die Datei existiert und ein vollstaendiges, lesbares ZIP ist."""
    if not os.path.isfile(path) or os.path.getsize(path) == 0:
        return False
    try:
        with zipfile.ZipFile(path) as zf:
            return zf.testzip() is None
    except zipfile.BadZipFile:
        return False


def download_tile(session, product, e_km, n_km, cache_dir):
    """Laedt eine einzelne Kachel, sofern sie nicht schon (gueltig) im Cache liegt.

    Rueckgabe: 'cached', 'downloaded' oder 'missing' (Kachel existiert serverseitig nicht).
    """
    cfg = PRODUCTS[product]
    filename = cfg["pattern"].format(e=e_km, n=n_km)
    target = os.path.join(cache_dir, filename)

    # --- Zuerst im Cache nachsehen ---
    if is_valid_zip(target):
        print(f"  [cache] {filename}")
        return "cached"

    url = f"{BASE_URL}/{cfg['share']}/{filename}"
    tmp = target + ".part"
    try:
        with session.get(url, stream=True, timeout=120) as r:
            if r.status_code == 404:
                print(f"  [fehlt] {filename} (nicht vorhanden)")
                return "missing"
            r.raise_for_status()
            with open(tmp, "wb") as f:
                for chunk in r.iter_content(chunk_size=1 << 16):
                    f.write(chunk)
    except requests.RequestException as exc:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise SystemExit(f"Fehler beim Laden von {url}: {exc}")

    if not is_valid_zip(tmp):
        os.remove(tmp)
        print(f"  [fehlt] {filename} (keine gueltige ZIP-Antwort)")
        return "missing"

    os.replace(tmp, target)
    size_mb = os.path.getsize(target) / (1024 * 1024)
    print(f"  [neu]   {filename} ({size_mb:.1f} MB)")
    return "downloaded"


def main():
    parser = argparse.ArgumentParser(
        description="Laedt Sachsen-DGM1/DOM1-Kacheln fuer einen Lat/Lon-Bereich in einen Cache.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--min-lat", type=float, required=True, help="Minimale Breite (Lat).")
    parser.add_argument("--max-lat", type=float, required=True, help="Maximale Breite (Lat).")
    parser.add_argument("--min-lon", type=float, required=True, help="Minimale Laenge (Lon).")
    parser.add_argument("--max-lon", type=float, required=True, help="Maximale Laenge (Lon).")
    parser.add_argument("--product", default="dgm1", choices=sorted(PRODUCTS),
                        help="Hoehenmodell-Produkt.")
    parser.add_argument("--cache-dir", default="./dgm1_cache",
                        help="Cache-Ordner fuer die heruntergeladenen ZIP-Kacheln.")
    args = parser.parse_args()

    if args.min_lat >= args.max_lat or args.min_lon >= args.max_lon:
        raise SystemExit("Ungueltiger Bereich: min muss kleiner als max sein.")

    os.makedirs(args.cache_dir, exist_ok=True)
    tiles = tiles_for_bbox(args.min_lat, args.max_lat, args.min_lon, args.max_lon)
    print(f"Bereich deckt {len(tiles)} Kachel(n) (2x2 km) ab. Cache: {args.cache_dir}")

    session = requests.Session()
    session.headers.update({"User-Agent": "osm-map-bundle/dgm1_downloader"})

    stats = {"cached": 0, "downloaded": 0, "missing": 0}
    for e_km, n_km in tiles:
        stats[download_tile(session, args.product, e_km, n_km, args.cache_dir)] += 1

    print(f"\nFertig. Neu geladen: {stats['downloaded']}, aus Cache: {stats['cached']}, "
          f"nicht vorhanden: {stats['missing']}.")
    print(f"Kacheln weiterverarbeiten mit:\n"
          f"  python3 lidar_tiler.py --input {args.cache_dir} --output ./dist/lidar_tiles")


if __name__ == "__main__":
    main()
