#!/bin/python3
"""
Orchestrator: Laedt fuer eine Liste von Sehenswuerdigkeiten (Bergbau im Freiberger
Revier) jeweils eine quadratische Flaeche als DGM1 UND DOM1 herunter und erzeugt
daraus zwei WebP-Kachelsaetze (Schummerung) - je einen fuer DGM1 und DOM1.

Ablauf:
    1. Fuer jede Sehenswuerdigkeit wird eine BOX_KM x BOX_KM grosse Flaeche um den
       Punkt bestimmt und in 2x2 km-Kacheln (ETRS89/UTM33) uebersetzt.
    2. Die Vereinigungsmenge aller Kacheln wird als DGM1 und DOM1 in den Cache
       geladen (vorhandene Kacheln werden uebersprungen -> siehe dgm1_downloader).
    3. lidar_tiler.py erzeugt daraus zwei getrennte Kachelsaetze:
         - DGM1 -> dist/dgm1_tiles
         - DOM1 -> dist/dom1_tiles
       Alle Sehenswuerdigkeiten landen jeweils im selben Verzeichnis.

Aufruf:
    python3 build_landmarks.py --dry-run        # nur Kachelanzahl/Groesse schaetzen
    python3 build_landmarks.py                  # herunterladen + kacheln
    python3 build_landmarks.py --skip-download   # nur (neu) kacheln aus Cache

Koordinaten ueberwiegend aus Wikipedia (siehe Kommentare). Bei einer 3x3 km-Box
sind kleine Ungenauigkeiten unkritisch.
"""

import os
import sys
import math
import argparse
import subprocess

# eigene Module
import dgm1_downloader as dl

# (Name, Breite/lat, Laenge/lon) - Quelle in Klammern
LANDMARKS = [
    # Rothschoenberger Stolln: Mundloch + Lichtloecher 1-7 (Wikipedia)
    ("Stollnmundloch Rothschoenberg", 51.067223, 13.399587),
    ("Lichtloch 1",                   51.051132, 13.387667),
    ("Lichtloch 2",                   51.036260, 13.380795),
    ("Lichtloch 3",                   51.022147, 13.374192),
    ("Lichtloch 4",                   51.007467, 13.366773),
    ("Lichtloch 5",                   50.993352, 13.357787),
    ("Lichtloch 6",                   50.978791, 13.351446),
    ("Lichtloch 7 (Halsbruecke)",     50.963779, 13.343770),
    # weitere Sehenswuerdigkeiten
    ("Kahnhebehaus Halsbruecke/Rothenfurth", 50.961266, 13.338104),  # Wikipedia (Erzkanal)
    ("Kahnhebehaus Grossvoigtsberg",         50.983744, 13.302176),  # Wikipedia (Erzkanal); "Kleinvoigtsberg" war nie gebaut
    ("Grube Churprinz",                      50.969699, 13.309791),  # Wikipedia (Erzkanal)
    ("Altvaeterbruecke Halsbruecke",         50.958546, 13.331278),  # Wikipedia
    ("Alter Tiefer Fuerstenstolln (Mundloch)", 50.940300, 13.371700),  # Wikipedia
    ("Alte Mordgrube",                       50.869617, 13.335552),  # Wikipedia
    ("Grosshartmannsdorfer Teich (Unterer)", 50.808333, 13.339444),  # Wikipedia
    ("Hungerborn (Rotvorwerksteich)",        50.879216, 13.312816),  # Wikipedia (Rotvorwerksteich; Hungerborn speist diesen)
    ("Bartholomaeusschacht Brand-Erbisdorf", 50.860000, 13.319450),  # museen.de (nicht Wikipedia) - bei Bedarf anpassen
    ("Konstantinschacht (Naeherung)",        50.873000, 13.340000),  # Schaetzung - kein Wikipedia-Eintrag gefunden
    # zusaetzliche Orte (Wikipedia, sofern nicht anders vermerkt)
    ("Freiberg",                             50.917051, 13.342730),  # Wikipedia (Stadtzentrum)
    ("Brand-Erbisdorf (Zentrum)",            50.869167, 13.321944),  # Wikipedia
    ("Thelersberger Stolln (Mundloch)",      50.878336, 13.282028),  # Wikipedia
    ("Erzengler Teich",                      50.852222, 13.339444),  # Wikipedia
    ("Weigmannsdorf-Muedisdorf",             50.839042, 13.381319),  # Wikipedia
    ("Rothenfurth",                          50.966333, 13.314550),  # Wikipedia
    ("Grossschirma",                         50.966389, 13.278056),  # Wikipedia
    ("Zechenteich (Fuerstenwald ~ Lossnitz)", 50.934722, 13.330556),  # Wikipedia (Lossnitz) - Naeherung
    ("Siebenlehn",                           51.031944, 13.308333),  # Wikipedia
    ("Reinsberg",                            51.008333, 13.363889),  # Wikipedia
    ("Zollhausbruecke (Bobritzsch ~ Bieberstein)", 51.007600, 13.352000),  # Naeherung (Bieberstein/Reinsberg)
    ("Langhennersdorf",                      50.943232, 13.249103),  # Wikipedia
    ("Krummenhennersdorf",                   50.979167, 13.362500),  # Wikipedia
    ("Steinbruch Oberschoena",               50.893300, 13.274200),  # ins-erzgebirge/wikimapia
    ("Wegefahrt (~Obersch.)",                50.913000, 13.272000),  # Naeherung (kein Wiki-Eintrag)
    ("Grosser Teich / Waldbad Freiberg",     50.909000, 13.353000),  # Naeherung (kein Wiki-Koord.)
    ("Mittelteich Freiberg",                 50.911000, 13.349000),  # Naeherung (kein Wiki-Koord.)
    ("Naundorf (Bobritzsch)",                50.935000, 13.420556),  # Wikipedia
    ("Niederbobritzsch",                     50.898611, 13.435000),  # Wikipedia
    ("Muldenhuetten",                        50.903056, 13.384722),  # Wikipedia
    ("Weissenborn/Erzgeb.",                  50.871111, 13.400833),  # Wikipedia
]

BOX_KM = 5  # Kantenlaenge der Flaeche pro Sehenswuerdigkeit


def tiles_for_landmarks(landmarks, box_km):
    """Vereinigungsmenge der 2x2 km-Kacheln (Ost_km, Nord_km) ueber alle Punkte."""
    ct = dl.make_transformer()
    half = box_km * 1000.0 / 2.0
    tiles = set()
    for _, lat, lon in landmarks:
        e, n, _ = ct.TransformPoint(lon, lat)
        e0 = int(math.floor((e - half) / 2000.0)) * dl.TILE_KM
        e1 = int(math.floor((e + half) / 2000.0)) * dl.TILE_KM
        n0 = int(math.floor((n - half) / 2000.0)) * dl.TILE_KM
        n1 = int(math.floor((n + half) / 2000.0)) * dl.TILE_KM
        for ek in range(e0, e1 + 1, dl.TILE_KM):
            for nk in range(n0, n1 + 1, dl.TILE_KM):
                tiles.add((ek, nk))
    return sorted(tiles)


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--cache-dir", default="./tiles_cache",
                   help="Gemeinsamer Cache fuer DGM1- und DOM1-ZIP-Kacheln.")
    p.add_argument("--dgm1-out", default="./dist/dgm1_tiles", help="Ausgabe DGM1-Kacheln.")
    p.add_argument("--dom1-out", default="./dist/dom1_tiles", help="Ausgabe DOM1-Kacheln.")
    p.add_argument("--zoom", default="13-18", help="Zoom-Stufen fuer lidar_tiler.")
    p.add_argument("--products", nargs="+", default=["dgm1", "dom1"],
                   choices=["dgm1", "dom1"], help="Welche Produkte verarbeiten.")
    p.add_argument("--dry-run", action="store_true",
                   help="Nur Kachelanzahl und geschaetzte Downloadgroesse zeigen.")
    p.add_argument("--skip-download", action="store_true",
                   help="Download ueberspringen, nur aus vorhandenem Cache kacheln.")
    args = p.parse_args()

    tiles = tiles_for_landmarks(LANDMARKS, BOX_KM)
    n_prod = len(args.products)
    print(f"{len(LANDMARKS)} Sehenswuerdigkeiten, {BOX_KM}x{BOX_KM} km je Punkt.")
    print(f"-> {len(tiles)} einzigartige 2x2 km-Kacheln x {n_prod} Produkt(e) "
          f"= {len(tiles) * n_prod} Downloads (~14 MB/Kachel, grob "
          f"{len(tiles) * n_prod * 14 / 1024:.1f} GB ungecacht).")

    if args.dry_run:
        return

    # --- 1. Download (DGM1 + DOM1) in gemeinsamen Cache ---
    if not args.skip_download:
        os.makedirs(args.cache_dir, exist_ok=True)
        session = dl.requests.Session()
        session.headers.update({"User-Agent": "osm-map-bundle/build_landmarks"})
        for product in args.products:
            print(f"\n=== Download {product.upper()} ({len(tiles)} Kacheln) ===")
            stats = {"cached": 0, "downloaded": 0, "missing": 0}
            for ek, nk in tiles:
                stats[dl.download_tile(session, product, ek, nk, args.cache_dir)] += 1
            print(f"  {product}: neu {stats['downloaded']}, Cache {stats['cached']}, "
                  f"fehlt {stats['missing']}")

    # --- 2. Kacheln pro Produkt erzeugen ---
    outdir = {"dgm1": args.dgm1_out, "dom1": args.dom1_out}
    for product in args.products:
        print(f"\n=== Kacheln erzeugen: {product.upper()} -> {outdir[product]} ===")
        subprocess.run([sys.executable, "lidar_tiler.py",
                        "--input", args.cache_dir,
                        "--output", outdir[product],
                        "--product", product,
                        "--zoom", args.zoom], check=True)

    print("\nFertig.")
    for product in args.products:
        print(f"  {product.upper()}: map.addTileLayer('./{os.path.basename(outdir[product])}/"
              f"{{z}}/{{x}}/{{y}}.webp', 18);")


if __name__ == "__main__":
    main()
