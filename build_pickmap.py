#!/bin/python3
"""
Erzeugt die Schummerungsbilder des 1-km-Ausschnitts um das 1. Lichtloch als
Hintergrund fuer die Klick-Karte (dist/lichtloch-pick.html).

Die Schummerung wird mit GDAL (gdaldem, autoritativ) aus den DGM1-GeoTIFFs des
Caches gerechnet - in ZWEI Lichtrichtungen:
  - dgm1_hs_nw.png : Licht aus NW (oben-links)  - Standard
  - dgm1_hs_se.png : Licht aus SE (unten-rechts) - gegen die Relief-Inversion

Wegen der Relief-Inversions-Taeuschung koennen erhabene Formen (Damm) wie
vertiefte (Graben) aussehen; mit der gespiegelten Lichtrichtung kippt der
Eindruck zurueck. Das Gitter ist identisch zu dist/lichtloch3d/dgm1.bin, daher
passt die Hoehenanzeige der Klick-Karte exakt zu den Pixeln.
"""

import os
import glob
import numpy as np
from osgeo import gdal, osr
from PIL import Image

gdal.UseExceptions()

CENTER_LAT, CENTER_LON = 51.051132, 13.387667
HALF_M, GRID = 500, 512
CACHE, OUTDIR = "./tiles_cache", "./dist/lichtloch3d"


def main():
    src = osr.SpatialReference(); src.ImportFromEPSG(4326)
    src.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    dst = osr.SpatialReference(); dst.ImportFromEPSG(25833)
    dst.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
    e, n, _ = osr.CoordinateTransformation(src, dst).TransformPoint(CENTER_LON, CENTER_LAT)
    bounds = [e - HALF_M, n - HALF_M, e + HALF_M, n + HALF_M]

    tiffs = [f"/vsizip/{z}/{os.path.basename(z)[:-len('_tiff.zip')]}.tif"
             for z in sorted(glob.glob(os.path.join(CACHE, "dgm1_*.zip")))]
    vrt = gdal.BuildVRT("", tiffs)
    dem = gdal.Warp("", vrt, format="MEM", outputBounds=bounds,
                    width=GRID, height=GRID, dstSRS="EPSG:25833", resampleAlg="bilinear")

    for az, tag in ((315, "nw"), (135, "se")):
        hs = gdal.DEMProcessing("", dem, "hillshade", format="MEM",
                                azimuth=az, altitude=45, computeEdges=True)
        arr = hs.GetRasterBand(1).ReadAsArray().astype(np.uint8)
        out = os.path.join(OUTDIR, f"dgm1_hs_{tag}.png")
        Image.fromarray(arr, "L").save(out)
        print(f"  Licht {az:3d} Grad ({tag}) -> {out}")


if __name__ == "__main__":
    main()
