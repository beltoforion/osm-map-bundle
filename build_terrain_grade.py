#!/bin/python3
"""
Passt das DGM1-Hoehengitter um Gebaeude 2 an und traegt zwei vom Nutzer markierte
Bereiche ab:

1. Treibe-/Maschinenhaus + Kesselhaus: ebene Plattform / Rampe auf Bodenhoehe,
   weich (BLEND) ans Gelaende angebunden -- damit die Gebaeude nicht in einem Loch
   stehen bzw. nicht schweben.
2. Halde (aufgeschuettetes Dammmaterial westlich des Durchbruchs): wird auf eine
   durch die Rand-Klickpunkte gelegte Ebene abgetragen (nur Abtrag).
3. Huegel vor dem Kesselhaus (dammzugewandte Seite): auf Kesselhaus-Bodenhoehe.

Eingaben : dist/lichtloch3d/{dgm1.bin, dgm1_dam.bin, meta.json, buildings.json}
Ausgaben : dist/lichtloch3d/{dgm1_graded.bin, dgm1_dam_graded.bin}
"""

import os, json
import numpy as np
from scipy.sparse import lil_matrix
from scipy.sparse.linalg import spsolve

DATADIR = "./dist/lichtloch3d"
APRON = 1.5     # ebener Streifen ueber die Gebaeudewand hinaus (m)
BLEND = 12.0    # Boeschungslaenge der Gebaeude-Pads zum Gelaende (m)
FEATHER = 3.5   # Rand-Ueberblendung der Polygon-Bereiche nach aussen (m)
TREIBE = "Treibe- und Maschinenhaus"   # vorderer, hoeherer Teil -> ebene Plattform
KESSEL = "Kesselhaus"                  # hinterer, niedrigerer Teil -> Rampe

# --- vom Nutzer in der Klick-Karte markiert (Ost, Nord in m) ---
# Halde nordseitig des Damms, westlich des Durchbruchs -> auf das Damm-Gefaelle abtragen:
HALDE_POLY = [(538,462),(539,470),(542,479),(552,479),(559,472),(559,463),(558,457),(548,457)]
# Huegel vor dem Kesselhaus (dammseitig) -> auf Kesselhaus-Boden:
HUEGEL_POLY = [(523,485),(518,475),(521,469),(525,471),(531,479)]

# Bereich, dessen Inneres per Laplace-Gleichung geglaettet wird (keine inneren
# Erhebungen; die Polygon-Raender bleiben als Dirichlet-Randwerte unveraendert):
SMOOTH_POLY = [(517,480),(514,476),(514,472),(515,468),(518,464),(522,463),(529,465),
               (531,464),(529,461),(529,458),(531,455),(533,453),(535,452),(542,450),
               (546,450),(552,450),(554,454),(551,460),(552,462),(559,463),(563,461),
               (566,466),(566,472),(565,477),(559,484),(554,487),(545,487),(537,484),
               (535,484),(531,487),(527,489),(522,487),(519,482)]

# Damm-Profil (wie build_reconstruction.py): Krone als Gerade #1->#2, Gefaelle 1:2.
DAM_P1, DAM_H1 = np.array([516.0, 441.0]), 252.3
DAM_P2, DAM_H2 = np.array([590.0, 451.0]), 251.8
CREST_W, SLOPE, DAM_TOE = 3.0, 2.0, 243.0   # Kronenbreite, Boeschung 1:2, Niveau am Fuss


def hillshade(a, azimuth, altitude, cell):
    """Einfache Schummerung (0..255) fuer die Klick-Karte; az=315 -> Licht von NW."""
    x, y = np.gradient(a, cell)
    slope = np.pi / 2 - np.arctan(np.hypot(x, y))
    aspect = np.arctan2(-x, y)
    az, alt = np.radians(azimuth), np.radians(altitude)
    sh = np.sin(alt) * np.sin(slope) + np.cos(alt) * np.cos(slope) * np.cos((az - np.pi / 2) - aspect)
    return np.clip(255 * (sh + 1) / 2, 0, 255).astype(np.uint8)


def laplace_fill(h, mask):
    """Ersetzt die Zellen in `mask` durch die Loesung von Laplace ∇²h=0 mit den
    umgebenden (festen) Zellen als Dirichlet-Rand -> glatteste Flaeche ohne innere
    Erhebungen, Raender unveraendert. (mask liegt vollstaendig im Gitterinneren.)"""
    cells = np.argwhere(mask)
    idx = {(r, c): k for k, (r, c) in enumerate(cells)}
    N = len(cells)
    A = lil_matrix((N, N)); b = np.zeros(N)
    for k, (r, c) in enumerate(cells):
        A[k, k] = 4.0
        for rr, cc in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
            if (rr, cc) in idx:
                A[k, idx[(rr, cc)]] = -1.0
            else:
                b[k] += h[rr, cc]           # fester Randwert
    sol = spsolve(A.tocsr(), b)
    out = h.copy()
    for k, (r, c) in enumerate(cells):
        out[r, c] = sol[k]
    return out


def poly_inside(O, N, poly):
    res = np.zeros(O.shape, bool); n = len(poly); j = n - 1
    for i in range(n):
        xi, yi = poly[i]; xj, yj = poly[j]
        cond = ((yi > N) != (yj > N)) & (O < (xj - xi) * (N - yi) / ((yj - yi) + 1e-12) + xi)
        res ^= cond; j = i
    return res


def poly_dist(O, N, poly):
    d = np.full(O.shape, np.inf); n = len(poly)
    for i in range(n):
        ax, ay = poly[i]; bx, by = poly[(i + 1) % n]
        dx, dy = bx - ax, by - ay; L2 = dx * dx + dy * dy + 1e-12
        t = np.clip(((O - ax) * dx + (N - ay) * dy) / L2, 0, 1)
        d = np.minimum(d, np.hypot(O - (ax + t * dx), N - (ay + t * dy)))
    return d


def main():
    meta = json.load(open(os.path.join(DATADIR, "meta.json")))
    G, size = meta["grid"], meta["sizeMeters"]
    B = json.load(open(os.path.join(DATADIR, "buildings.json")))
    treibe = next(b for b in B["buildings"] if b["name"].startswith(TREIBE))
    kessel = next(b for b in B["buildings"] if b["name"].startswith(KESSEL))

    rows, cols = np.indices((G, G))
    Ost = cols / (G - 1) * size
    Nord = (1 - rows / (G - 1)) * size
    nat0 = np.fromfile(os.path.join(DATADIR, "dgm1.bin"), dtype="<f4").reshape(G, G).astype(np.float64)

    wmax = np.zeros((G, G))
    floor = np.zeros((G, G))

    def combine(w, target):
        nonlocal wmax, floor
        take = w > wmax
        floor = np.where(take, target, floor)
        wmax = np.where(take, w, wmax)

    def pad_weight(b):
        dx, dy = Ost - b["ost"], Nord - b["nord"]
        along = dx * b["ux"] + dy * b["uy"]          # entlang First (+ Richtung Treibehaus)
        perp  = -dx * b["uy"] + dy * b["ux"]         # quer
        ddx = np.abs(along) - b["L"] / 2
        ddy = np.abs(perp)  - b["W"] / 2
        d = np.hypot(np.maximum(ddx, 0), np.maximum(ddy, 0))
        t = np.clip(1 - (d - APRON) / BLEND, 0, 1)
        return t * t * (3 - 2 * t), along

    def region_weight(poly):
        ds = np.where(poly_inside(Ost, Nord, poly), 1, -1) * poly_dist(Ost, Nord, poly)
        t = np.clip(1 + ds / FEATHER, 0, 1)          # 1 innen, 0 ab FEATHER ausserhalb
        return t * t * (3 - 2 * t)

    # Treibe-/Maschinenhaus: ebene Plattform
    wt, _ = pad_weight(treibe)
    combine(wt, treibe["floorAbs"])

    # Kesselhaus: Rampe (Fuge = Treibehaus-Niveau, freies Ende = Kesselhaus-Niveau)
    wk, along_k = pad_weight(kessel)
    frac = np.clip((along_k + kessel["L"] / 2) / kessel["L"], 0, 1)   # 0 = freies Ende, 1 = Fuge
    combine(wk, kessel["floorAbs"] + frac * (treibe["floorAbs"] - kessel["floorAbs"]))

    # Halde: auf das Damm-Gefaelle (1:2 vom Kronenprofil) abtragen, am Fuss auf das
    # natuerliche Niveau (DAM_TOE) auslaufend; nur Abtrag, damit der Damm bleibt.
    Lv = DAM_P2 - DAM_P1; ln = np.hypot(*Lv); uu = Lv / ln
    proj = (Ost - DAM_P1[0]) * uu[0] + (Nord - DAM_P1[1]) * uu[1]
    perp = np.abs((Ost - DAM_P1[0]) * uu[1] - (Nord - DAM_P1[1]) * uu[0])
    crest_h = DAM_H1 + (DAM_H2 - DAM_H1) * np.clip(proj / ln, 0, 1)
    profile = crest_h - np.maximum(0.0, perp - CREST_W / 2) / SLOPE
    target_halde = np.minimum(nat0, np.maximum(profile, DAM_TOE))
    combine(region_weight(HALDE_POLY), target_halde)

    # Huegel vor dem Kesselhaus: auf Kesselhaus-Bodenhoehe
    combine(region_weight(HUEGEL_POLY), kessel["floorAbs"])

    # Glaettungs-Maske (Inneres des markierten Polygons) fuer den Laplace-Schritt
    smooth_mask = poly_inside(Ost, Nord, SMOOTH_POLY)

    dam_graded = None
    for name in ("dgm1.bin", "dgm1_dam.bin"):
        nat = np.fromfile(os.path.join(DATADIR, name), dtype="<f4").reshape(G, G).astype(np.float64)
        graded = wmax * floor + (1 - wmax) * nat
        graded = laplace_fill(graded, smooth_mask)   # Inneres glaetten, Raender fest
        out = name.replace(".bin", "_graded.bin")
        graded.astype("<f4").tofile(os.path.join(DATADIR, out))
        if name == "dgm1_dam.bin":
            dam_graded = graded
        d = graded - nat
        print(f"{name}: max Auftrag +{d.max():.1f} m, max Abtrag {d.min():.1f} m "
              f"({int((np.abs(d) > 0.05).sum())} Zellen) -> {out}")

    # Schummerung der bearbeiteten Flaeche (Damm wiederhergestellt) fuer die Klick-Karte
    try:
        from PIL import Image
        cell = size / (G - 1)
        for az, tag in ((315, "nw"), (135, "se")):
            Image.fromarray(hillshade(dam_graded, az, 45, cell), "L").save(
                os.path.join(DATADIR, f"dgm1g_hs_{tag}.png"))
        print("  Schummerung (bearbeitet) -> dgm1g_hs_nw.png / dgm1g_hs_se.png")
    except Exception as e:
        print("  (Schummerung uebersprungen:", e, ")")


if __name__ == "__main__":
    main()
