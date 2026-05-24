#!/bin/python3
"""
Rekonstruiert den durchbrochenen Teichdamm im DGM1-Hoehengitter um das 1. Lichtloch.

Die Krone ist die Gerade #1 (Ost516,Nord441) -> #2 (Ost590,Nord451), Hoehe entlang
der Geraden von 252.3 m auf 251.8 m interpoliert. Im Bruchabschnitt (zwischen #3
Ost560 und #4 Ost584) liegt das Gelaende heute tiefer -> es wird auf das
Dammprofil angehoben (Kronenbreite 3 m, Boeschung 1:2). Erhaltene Teile bleiben
unveraendert (Maximum aus Bestand und Zielprofil).

Eingabe : dist/lichtloch3d/dgm1.bin (512x512 Float32, Nord oben)
Ausgabe : dist/lichtloch3d/dgm1_dam.bin (Damm wiederhergestellt)
"""

import os, json
import numpy as np

DATADIR = "./dist/lichtloch3d"
P1 = np.array([516.0, 441.0]); H1 = 252.3      # Krone West (Ost,Nord)
P2 = np.array([590.0, 451.0]); H2 = 251.8      # Krone Ost
CREST_W = 3.0      # Kronenbreite (m)
SLOPE   = 2.0      # Boeschung 1:2 (horizontal je 1 m Hoehe)


def main():
    meta = json.load(open(os.path.join(DATADIR, "meta.json")))
    G, size = meta["grid"], meta["sizeMeters"]
    h = np.fromfile(os.path.join(DATADIR, "dgm1.bin"), dtype="<f4").reshape(G, G).astype(np.float64)

    rows, cols = np.indices((G, G))
    Ost = cols / (G - 1) * size
    Nord = (1 - rows / (G - 1)) * size

    L = P2 - P1; length = np.hypot(*L); u = L / length
    qx, qy = Ost - P1[0], Nord - P1[1]
    proj = qx * u[0] + qy * u[1]                       # entlang der Krone
    perp = np.abs(qx * u[1] - qy * u[0])               # senkrechter Abstand
    t = np.clip(proj / length, 0, 1)
    crest_h = H1 + (H2 - H1) * t
    target = crest_h - np.maximum(0.0, perp - CREST_W / 2) / SLOPE   # Dammprofil

    in_seg = (proj >= 0) & (proj <= length)
    new = np.where(in_seg, np.maximum(h, target), h)

    raised = (new - h) > 0.05
    out = os.path.join(DATADIR, "dgm1_dam.bin")
    new.astype("<f4").tofile(out)
    print(f"Damm rekonstruiert: {int(raised.sum())} Zellen angehoben, "
          f"max +{(new - h).max():.1f} m  -> {out}")


if __name__ == "__main__":
    main()
