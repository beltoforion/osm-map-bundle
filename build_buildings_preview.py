#!/bin/python3
"""
Berechnet aus den Klick-Ecken (Position/Ausrichtung) + den verbindlichen Massen
die Geometrie-Parameter der beiden Gebaeude + Schornstein fuer die 3D-Vorschau
(dist/lichtloch-buildings.html). Ergebnis: dist/lichtloch3d/buildings.json.

Weltkoordinaten (wie im 3D-Viewer): X = Ost-500, Z = 500-Nord (Nord = -Z),
Y = Hoehe - globalMin. Massstab Meter.
"""

import os, json
import numpy as np

DATADIR = "./dist/lichtloch3d"

# --- Eingaben aus lichtloch_rekonstruktion.md ---
B1_CORNERS = [(497,441),(506,448),(482,471),(475,465)]   # Gebaeude 1
B1 = dict(L=24.0, W=8.0, wallH=3.0, roofH=4.0)   # Satteldach 4,0 m
B1_LIFT = 0.1                                    # Bergschmiede zusaetzlich 0,1 m anheben

B2_CORNERS = [(517,487),(527,494),(499,512),(492,504)]   # Gebaeude 2 (gesamt)
B2_TOTAL_L, B2_W = 29.3, 9.0
B2_REAR_L = 13.16            # hinterer (dammnaher) Teil = der NIEDRIGERE/KUERZERE
B2_FRONT_L = B2_TOTAL_L - B2_REAR_L   # vorderer Teil = hoeher/laenger
B2_FRONT = dict(wallH=6.0,  roofH=4.0)    # Treibe-/Maschinenhaus (Schacht): Wand 6 m (gesch.) + Satteldach 4 m
B2_REAR  = dict(wallH=4.32, roofH=2.5)    # Kesselhaus (aus alter Zeichnung): Wand 4,32 m + Satteldach 2,5 m
B2_LIFT  = 2.0                            # Treibe-/Maschinen- + Kesselhaus zusaetzlich anheben (2x 1 m)
CHIMNEY = dict(height=16.0, size=2.24, sizeTop=1.5)   # quadratisch, unten 2,24 m -> oben 1,5 m (verjuengt)


def main():
    meta = json.load(open(os.path.join(DATADIR, "meta.json")))
    G, size = meta["grid"], meta["sizeMeters"]
    gmin = min(meta["products"]["dgm1"]["min"], meta["products"]["dom1"]["min"])
    elev = np.fromfile(os.path.join(DATADIR, "dgm1.bin"), dtype="<f4").reshape(G, G)

    def elev_at(ost, nord):
        c = int(round(np.clip(ost/size*(G-1), 0, G-1)))
        r = int(round(np.clip((1-nord/size)*(G-1), 0, G-1)))
        return float(elev[r, c])

    def axis(corners):
        """Mittelpunkt (Ost,Nord) + Laengsachsen-Richtung (Einheitsvektor)."""
        p = np.array(corners, float)
        edges = [p[(i+1) % 4] - p[i] for i in range(4)]
        lens = [np.hypot(*e) for e in edges]
        o = np.argsort(lens)[::-1]
        e1, e2 = edges[o[0]], edges[o[1]]
        if np.dot(e1, e2) < 0:
            e2 = -e2
        u = e1 + e2
        return p.mean(0), u/np.hypot(*u)

    def base_y(center, u, L, W):
        """Bodenhoehe = min. Gelaende an den 4 Eckpunkten des Footprints."""
        v = np.array([-u[1], u[0]])
        hs = [elev_at(*(center + sl*L/2*u + sw*W/2*v)) for sl in (-1,1) for sw in (-1,1)]
        return min(hs) - gmin

    def ry(u):
        # lokale +X-Achse -> Welt-Laengsrichtung (uX, uZ)=(u_ost, -u_nord)
        return float(np.arctan2(u[1], u[0]))   # atan2(-uZ,uX) mit uZ=-u_nord

    def world(center):
        return float(center[0]-size/2), float(size/2-center[1])

    out = {"globalMin": gmin, "size": size, "buildings": []}

    # Gebaeude 1
    c1, u1 = axis(B1_CORNERS)
    x1, z1 = world(c1)
    baseY1 = base_y(c1, u1, B1["L"], B1["W"]) + B1_LIFT
    out["buildings"].append(dict(name="Bergschmiede", cx=x1, cz=z1, ry=ry(u1),
        L=B1["L"], W=B1["W"], wallH=B1["wallH"], roofH=B1["roofH"], baseY=baseY1,
        ost=float(c1[0]), nord=float(c1[1]), ux=float(u1[0]), uy=float(u1[1]),
        floorAbs=baseY1 + gmin))

    # Gebaeude 2: u so orientieren, dass +u nach Norden (vom Damm weg) zeigt
    c2, u2 = axis(B2_CORNERS)
    if u2[1] < 0:
        u2 = -u2
    s_rear  = -B2_TOTAL_L/2 + B2_REAR_L/2
    s_front = -B2_TOTAL_L/2 + B2_REAR_L + B2_FRONT_L/2
    c_rear  = c2 + s_rear * u2
    c_front = c2 + s_front * u2
    # Schacht (blaue Markierung) liegt SHAFT_FROM_REAR m von der hinteren (Nord-/
    # damm-abgewandten) Wand des Treibehauses entfernt, mittig auf dem First.
    BLUE = np.array([496.81, 498.29])      # alternative Schachtposition (51.051116/13.387622)
    SHAFT_FROM_REAR = 4.5                   # Schachtmittelpunkt -> hintere Treibehaus-Wand (aus Zeichnung) -- MERKEN
    off = B2_FRONT_L / 2 - SHAFT_FROM_REAR  # Versatz des Schachts von der Treibehaus-Mitte (entlang First)
    shift = (BLUE - off * u2) - c_front     # Treibehaus-Mitte = BLUE - off*u2
    c_front = c_front + shift
    c_rear  = c_rear + shift
    front_baseY = base_y(c_front, u2, B2_FRONT_L, B2_W) + B2_LIFT
    # Kesselhaus-Boden liegt 2,8 m UNTER dem Boden des Treibe-/Maschinenhauses (aus Zeichnung)
    for nm, cc, L, hh, by in (
            ("Kesselhaus (hinten, Schornstein)", c_rear, B2_REAR_L, B2_REAR, front_baseY - 2.8),
            ("Treibe- und Maschinenhaus (vorne, Schacht)", c_front, B2_FRONT_L, B2_FRONT, front_baseY)):
        xx, zz = world(cc)
        out["buildings"].append(dict(name=nm, cx=xx, cz=zz, ry=ry(u2),
            L=L, W=B2_W, wallH=hh["wallH"], roofH=hh["roofH"], baseY=by,
            ost=float(cc[0]), nord=float(cc[1]), ux=float(u2[0]), uy=float(u2[1]),
            floorAbs=by + gmin))

    # Schornstein: laengs mittig am Kesselhaus; quer 7,7 m von der dammseitigen
    # (langen) Wand entfernt -> liegt nahe der dammabgewandten Rueckwand.
    v2 = np.array([-u2[1], u2[0]])
    n = v2 if v2[1] > 0 else -v2          # +n = Richtung Norden (vom Damm weg)
    CHIMNEY_FROM_DAMWALL = 7.7            # Schornstein-Mitte -> dammseitige Stirnwand (entlang First) -- MERKEN
    along = CHIMNEY_FROM_DAMWALL - B2_REAR_L/2      # Laengsversatz von der Kesselhaus-Mitte
    perp  = B2_W/2 + CHIMNEY["size"]/2             # AUSSERHALB, an der dammabgewandten Rueckwand
    cs = c_rear + along * u2 + perp * n
    xs, zs = world(cs)
    # Schornstein steht auf Kesselhaus-Bodenhoehe (nicht auf dem natuerlichen Gelaende)
    out["chimney"] = dict(x=xs, z=zs, baseY=front_baseY - 2.8, ry=ry(u2),
                          height=CHIMNEY["height"], size=CHIMNEY["size"], sizeTop=CHIMNEY["sizeTop"])

    json.dump(out, open(os.path.join(DATADIR, "buildings.json"), "w"), indent=2)
    for b in out["buildings"]:
        print(f"  {b['name']}: L={b['L']:.1f} W={b['W']:.1f} Wand={b['wallH']} "
              f"Dach={b['roofH']} BodenY={b['baseY']:.1f}  (ry={np.degrees(b['ry']):.0f} Grad)")
    print(f"  Schornstein: {CHIMNEY['height']} m, BodenY={out['chimney']['baseY']:.1f}")
    print("-> dist/lichtloch3d/buildings.json")


if __name__ == "__main__":
    main()
