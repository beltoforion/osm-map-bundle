#!/bin/python3
"""
Baut die Hoehendaten fuer einen interaktiven 3D-Viewer (three.js) der Gegend um
das 1. Lichtloch des Rothschoenberger Stollns - jeweils aus DGM1 (Gelaende) und
DOM1 (Oberflaeche).

Aus den im Cache liegenden GeoTIFFs wird ein quadratischer Ausschnitt
ausgeschnitten, auf ein handliches Gitter (GRID x GRID) resampelt und als
Float32-Binaerdatei (zeilenweise, Nord oben) nach dist/lichtloch3d/ geschrieben.
dist/lichtloch-3d.html laedt diese Daten und stellt sie als 3D-Relief dar.
"""

import os
import glob
import json
import struct

import numpy as np
from osgeo import gdal, osr

gdal.UseExceptions()

CENTER_LAT, CENTER_LON = 51.051132, 13.387667   # 1. Lichtloch
HALF_M = 500           # halbe Kantenlaenge -> 1 x 1 km Ausschnitt (ca. 500 m um das Lichtloch)
GRID = 512             # Gitteraufloesung des Hoehenmodells (GRID x GRID Punkte)
CACHE = "./tiles_cache"
OUTDIR = "./dist/lichtloch3d"
PRODUCTS = ("dgm1", "dom1")


def utm_center():
    src = osr.SpatialReference(); src.ImportFromEPSG(4326)
    src.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    dst = osr.SpatialReference(); dst.ImportFromEPSG(25833)
    dst.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    e, n, _ = osr.CoordinateTransformation(src, dst).TransformPoint(CENTER_LON, CENTER_LAT)
    return e, n


def vsizip_tiffs(product):
    """Pfade der GeoTIFFs (im ZIP) fuer ein Produkt."""
    paths = []
    for zip_path in sorted(glob.glob(os.path.join(CACHE, f"{product}_*.zip"))):
        base = os.path.basename(zip_path)[:-len("_tiff.zip")]   # dgm1_33xxx_yyyy_2_sn
        paths.append(f"/vsizip/{zip_path}/{base}.tif")
    return paths


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    e, n = utm_center()
    bounds = [e - HALF_M, n - HALF_M, e + HALF_M, n + HALF_M]   # minx,miny,maxx,maxy (EPSG:25833)
    print(f"1. Lichtloch UTM33: E={e:.1f} N={n:.1f}, Ausschnitt {2*HALF_M} m, Gitter {GRID}x{GRID}")

    meta = {"grid": GRID, "sizeMeters": 2 * HALF_M, "products": {}}
    for product in PRODUCTS:
        tiffs = vsizip_tiffs(product)
        if not tiffs:
            raise SystemExit(f"Keine {product}-GeoTIFFs im Cache gefunden.")
        vrt = gdal.BuildVRT("", tiffs)
        # auf Ausschnitt zuschneiden + auf GRID x GRID resampeln (metrisch, EPSG:25833)
        ds = gdal.Warp("", vrt, format="MEM", outputBounds=bounds,
                       width=GRID, height=GRID, dstSRS="EPSG:25833",
                       resampleAlg="bilinear")
        band = ds.GetRasterBand(1)
        arr = band.ReadAsArray().astype(np.float32)         # [Zeile(Nord->Sued)][Spalte]
        nodata = band.GetNoDataValue()
        if nodata is not None:
            arr[arr == nodata] = np.nan
        valid = arr[~np.isnan(arr)]
        zmin, zmax = float(valid.min()), float(valid.max())
        arr[np.isnan(arr)] = zmin                            # Luecken auf Minimum setzen

        out = os.path.join(OUTDIR, f"{product}.bin")
        with open(out, "wb") as f:
            f.write(struct.pack("<" + "f" * arr.size, *arr.ravel(order="C")))
        meta["products"][product] = {"min": zmin, "max": zmax}
        print(f"  {product}: Hoehe {zmin:.1f}..{zmax:.1f} m  -> {out} "
              f"({os.path.getsize(out)//1024} KB)")

    with open(os.path.join(OUTDIR, "meta.json"), "w") as f:
        json.dump(meta, f, indent=2)
    print(f"meta.json geschrieben. 3D-Viewer: dist/lichtloch-3d.html")


if __name__ == "__main__":
    main()
