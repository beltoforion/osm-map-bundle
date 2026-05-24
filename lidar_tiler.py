#!/bin/python3
"""
LiDAR-Tiler: Erzeugt WebP-Slippy-Map-Kacheln aus den digitalen Hoehenmodellen
des Landesamtes fuer Geobasisinformation Sachsen (GeoSN).

Datenquelle:
    https://www.geodaten.sachsen.de/downloadbereich-digitale-hoehenmodelle-4851.html

Die DGM1/DOM1-Daten liegen als GeoTIFF (EPSG:25833, ETRS89/UTM33) in 2x2 km
Kacheln, verpackt in ZIP-Dateien, vor. Rohe Hoehenwerte sind als Kartenhintergrund
nicht sichtbar - dieses Skript rechnet sie in eine Schummerung (Hillshade) um und
zerlegt das Ergebnis in XYZ-Kacheln, die sich direkt mit OsmMap.addTileLayer()
verwenden lassen:

    map.addTileLayer('./lidar_tiles/{z}/{x}/{y}.webp');

Ablauf der Verarbeitung:
    1. ZIP-Dateien im Eingabeordner entpacken und alle GeoTIFFs einsammeln
    2. gdalbuildvrt   -> virtuelles Mosaik aller Kacheln (in EPSG:25833)
    3. gdaldem        -> Schummerung berechnen (metrisch, korrekter z-Faktor)
    4. gdal2tiles.py  -> nach Web-Mercator reprojizieren und WebP-XYZ-Kacheln schneiden

Voraussetzung: GDAL >= 3.6 inkl. gdal2tiles.py (WebP-Tiledriver, --xyz).
"""

import os
import sys
import glob
import shutil
import zipfile
import argparse
import subprocess


def run(cmd):
    """Fuehrt ein Kommando aus und bricht bei Fehler mit Klartext ab."""
    print("  $ " + " ".join(cmd))
    result = subprocess.run(cmd)
    if result.returncode != 0:
        raise SystemExit(f"Abbruch: '{cmd[0]}' endete mit Code {result.returncode}")


def collect_geotiffs(input_dir, work_dir, prefix=None):
    """Entpackt ZIP-Dateien und sammelt alle GeoTIFFs (rekursiv) ein.

    Mit prefix (z.B. 'dgm1' oder 'dom1') werden nur Dateien beruecksichtigt,
    deren Name damit beginnt. So laesst sich ein gemeinsamer Cache, der DGM1-
    UND DOM1-Kacheln enthaelt, getrennt nach Produkt verarbeiten.
    """
    def matches(path):
        return prefix is None or os.path.basename(path).lower().startswith(prefix)

    zips = [z for z in glob.glob(os.path.join(input_dir, "**", "*.zip"), recursive=True)
            if matches(z)]
    if zips:
        extract_dir = os.path.join(work_dir, "extracted")
        os.makedirs(extract_dir, exist_ok=True)
        for zip_path in zips:
            print(f"Entpacke {os.path.basename(zip_path)} ...")
            with zipfile.ZipFile(zip_path) as zf:
                zf.extractall(extract_dir)

    tiffs = []
    for root in (input_dir, work_dir):
        for ext in ("*.tif", "*.tiff", "*.TIF", "*.TIFF"):
            tiffs.extend(glob.glob(os.path.join(root, "**", ext), recursive=True))

    tiffs = sorted(set(os.path.abspath(t) for t in tiffs if matches(t)))
    if not tiffs:
        raise SystemExit(
            f"Keine GeoTIFF-Dateien in '{input_dir}' gefunden (Filter: {prefix or 'kein'}).")

    print(f"{len(tiffs)} GeoTIFF-Kachel(n) gefunden.")
    return tiffs


def build_mosaic(tiffs, work_dir):
    """Erzeugt ein virtuelles Mosaik (VRT) aus allen Eingabe-Kacheln."""
    vrt_path = os.path.join(work_dir, "mosaic.vrt")
    list_path = os.path.join(work_dir, "tiles.txt")
    with open(list_path, "w") as f:
        f.write("\n".join(tiffs))

    print("Erstelle Mosaik (VRT) ...")
    run(["gdalbuildvrt", "-input_file_list", list_path, vrt_path])
    return vrt_path


def clip_to_bbox(vrt_path, work_dir, min_lat, max_lat, min_lon, max_lon):
    """Schneidet das Mosaik auf einen Lat/Lon-Bereich zu (virtuell, ohne Kopie).

    Der Bereich wird in EPSG:4326 (Laenge/Breite) angegeben; die Projektion des
    Mosaiks (EPSG:25833) bleibt erhalten, damit die Schummerung metrisch korrekt
    bleibt. gdal2tiles reprojiziert spaeter selbst nach Web-Mercator.
    """
    clip_path = os.path.join(work_dir, "mosaic_clip.vrt")
    print(f"Beschneide auf Bereich Lat[{min_lat}, {max_lat}] Lon[{min_lon}, {max_lon}] ...")
    run([
        "gdalwarp",
        "-of", "VRT",                          # virtuell -> keine grosse Zwischendatei
        "-te_srs", "EPSG:4326",                # Bereichsangabe in Laenge/Breite
        "-te", str(min_lon), str(min_lat), str(max_lon), str(max_lat),
        "-overwrite",
        vrt_path, clip_path,
    ])
    return clip_path


def build_hillshade(vrt_path, work_dir, mode, z_factor, azimuth, altitude):
    """Berechnet die Schummerung in der metrischen Quell-Projektion (EPSG:25833)."""
    hs_path = os.path.join(work_dir, "hillshade.tif")
    cmd = [
        "gdaldem", "hillshade", vrt_path, hs_path,
        "-z", str(z_factor),
        "-compute_edges",          # keine schwarzen Raender zwischen Kacheln
        "-of", "GTiff",
        "-co", "COMPRESS=DEFLATE",
    ]
    if mode == "multidirectional":
        cmd.append("-multidirectional")   # beleuchtet aus mehreren Richtungen
    elif mode == "igor":
        cmd.append("-igor")               # weiche Schummerung nach Igor Pilkin
    else:  # standard
        cmd += ["-az", str(azimuth), "-alt", str(altitude)]

    print(f"Berechne Schummerung (Modus: {mode}) ...")
    run(cmd)

    # Die Schummerung ist einbandig (Graustufen). Der WebP-Treiber von gdal2tiles
    # braucht aber RGB oder RGBA. Daher wird ein Alpha-Band aus den Nodata-Bereichen
    # erzeugt (transparente Raender) und die Graustufen auf R=G=B abgebildet.
    alpha_path = os.path.join(work_dir, "hillshade_alpha.vrt")
    run(["gdalwarp", "-of", "VRT", "-dstalpha", "-overwrite", hs_path, alpha_path])

    rgba_path = os.path.join(work_dir, "hillshade_rgba.vrt")
    run([
        "gdal_translate", "-of", "VRT",
        "-b", "1", "-b", "1", "-b", "1", "-b", "2",   # grau,grau,grau,alpha
        "-colorinterp", "red,green,blue,alpha",
        alpha_path, rgba_path,
    ])
    return rgba_path


def cut_tiles(hs_path, output_dir, zoom, resampling, webp_quality, processes):
    """Reprojiziert nach Web-Mercator und schneidet WebP-XYZ-Kacheln."""
    print("Schneide WebP-XYZ-Kacheln (gdal2tiles) ...")
    run([
        "gdal2tiles.py",
        "--xyz",                       # OSM/OpenLayers-Kachelnummerierung
        "--profile=mercator",          # reprojiziert von EPSG:25833 nach 3857
        "--tiledriver=WEBP",
        f"--webp-quality={webp_quality}",
        f"--zoom={zoom}",
        f"--resampling={resampling}",
        f"--processes={processes}",
        "--no-kml",
        "-w", "none",                  # kein HTML-Viewer noetig
        hs_path,
        output_dir,
    ])


def main():
    parser = argparse.ArgumentParser(
        description="Wandelt Sachsen-DGM1/DOM1-GeoTIFFs in WebP-Slippy-Map-Kacheln (Schummerung).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--input", default="./dgm1_download",
                        help="Ordner mit heruntergeladenen ZIP- und/oder GeoTIFF-Dateien.")
    parser.add_argument("--output", default="./dist/lidar_tiles",
                        help="Ausgabeordner fuer die {z}/{x}/{y}.webp Kacheln.")
    parser.add_argument("--zoom", default="11-18",
                        help="Zoom-Stufen, z.B. '11-18' oder '15'.")
    parser.add_argument("--product", default="any", choices=["any", "dgm1", "dom1"],
                        help="Nur Kacheln dieses Produkts verarbeiten (Namenspraefix-Filter). "
                             "Nuetzlich bei gemeinsamem Cache mit DGM1 und DOM1.")
    parser.add_argument("--min-lat", type=float, default=None, help="Minimale Breite (Lat) des Ausschnitts.")
    parser.add_argument("--max-lat", type=float, default=None, help="Maximale Breite (Lat) des Ausschnitts.")
    parser.add_argument("--min-lon", type=float, default=None, help="Minimale Laenge (Lon) des Ausschnitts.")
    parser.add_argument("--max-lon", type=float, default=None, help="Maximale Laenge (Lon) des Ausschnitts.")
    parser.add_argument("--mode", default="multidirectional",
                        choices=["standard", "multidirectional", "igor"],
                        help="Schummerungs-Modus. 'multidirectional' zeigt Mikrorelief "
                             "(z.B. Bergbauspuren) unabhaengig von der Hangrichtung.")
    parser.add_argument("--z-factor", type=float, default=1.0,
                        help="Ueberhoehungsfaktor. 1.0 ist korrekt fuer Meter-Daten (UTM).")
    parser.add_argument("--azimuth", type=float, default=315.0,
                        help="Lichtrichtung in Grad (nur Modus 'standard').")
    parser.add_argument("--altitude", type=float, default=45.0,
                        help="Lichthoehe in Grad (nur Modus 'standard').")
    parser.add_argument("--resampling", default="bilinear",
                        help="Resampling beim Reprojizieren/Verkleinern.")
    parser.add_argument("--webp-quality", type=int, default=75,
                        help="WebP-Qualitaet (1-100).")
    parser.add_argument("--processes", type=int, default=os.cpu_count() or 4,
                        help="Anzahl paralleler Prozesse fuer gdal2tiles.")
    parser.add_argument("--work-dir", default="./.lidar_work",
                        help="Ordner fuer Zwischendateien (VRT, Schummerung).")
    parser.add_argument("--keep-work", action="store_true",
                        help="Zwischendateien nach Abschluss nicht loeschen.")
    args = parser.parse_args()

    if shutil.which("gdal2tiles.py") is None:
        raise SystemExit("gdal2tiles.py nicht gefunden - bitte GDAL (>=3.6) installieren.")

    os.makedirs(args.work_dir, exist_ok=True)
    os.makedirs(args.output, exist_ok=True)

    bbox = (args.min_lat, args.max_lat, args.min_lon, args.max_lon)
    if any(v is not None for v in bbox) and not all(v is not None for v in bbox):
        raise SystemExit("Fuer den Ausschnitt bitte alle vier Werte angeben: "
                         "--min-lat --max-lat --min-lon --max-lon")

    prefix = None if args.product == "any" else args.product
    tiffs = collect_geotiffs(args.input, args.work_dir, prefix)
    vrt = build_mosaic(tiffs, args.work_dir)
    if all(v is not None for v in bbox):
        vrt = clip_to_bbox(vrt, args.work_dir,
                           args.min_lat, args.max_lat, args.min_lon, args.max_lon)
    hillshade = build_hillshade(vrt, args.work_dir, args.mode,
                                args.z_factor, args.azimuth, args.altitude)
    cut_tiles(hillshade, args.output, args.zoom,
              args.resampling, args.webp_quality, args.processes)

    if not args.keep_work:
        shutil.rmtree(args.work_dir, ignore_errors=True)

    print(f"\nFertig. Kacheln liegen in: {args.output}")
    print(f"Einbinden mit:  map.addTileLayer('./{os.path.basename(args.output)}/{{z}}/{{x}}/{{y}}.webp');")


if __name__ == "__main__":
    main()
