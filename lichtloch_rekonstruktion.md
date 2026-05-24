# Rekonstruktion am 1. Lichtloch — Spezifikation (Damm + 2 Gebäude)

Ziel: durchbrochenen Teichdamm wiederherstellen und zwei Gebäude (als Häuser)
in das DGM1-Höhenmodell des 1-km-Ausschnitts um das 1. Lichtloch einbauen.
**Status: WARTEN auf „Go" des Nutzers — noch nichts bauen.**

## Koordinatensystem der Klick-Punkte
- Lokales Meter-Raster des Ausschnitts: `Ost` = Meter ab Westkante (0..1000), `Nord` = Meter ab Südkante (0..1000).
- Gitter 512×512, Mitte (Ost 500 / Nord 500) = 1. Lichtloch.
- UTM33 (EPSG:25833): Mitte E=386990.7, N=5656747.7 → Punkt (Ost,Nord) = UTM (386490.7+Ost, 5656247.7+Nord).
- Höhen in m ü. NN (DHHN2016).
- Verbindlich: **Maße** wie unten; **Position/Ausrichtung** aus den Klick-Ecken.

## Damm (Teichdamm, wiederherzustellen)
Krone als Linie durch 4 geklickte Punkte (West→Ost):

| # | Ost | Nord | Zelle (c,r) | Höhe (geklickt) |
|---|-----|------|-------------|-----------------|
| 1 | 516 | 441  | 264,285     | 252.3 m |
| 3 | 560 | 447  | 286,283     | 252.1 m |
| 4 | 584 | 449  | 299,282     | 251.5 m |
| 2 | 590 | 451  | 302,280     | 251.8 m |

- Länge ~75 m, Verlauf ~ENE. **Kronenhöhe ≈ 252 m**.
- **Krone ist eine GERADE von #1 (516,441) nach #2 (590,451)** — Höhe entlang der Geraden zwischen 252.3 m (#1) und 251.8 m (#2) interpolieren.
- **Der Durchbruch liegt zwischen #3 (Ost 560) und #4 (Ost 584)** — nur dieser Abschnitt (~24 m) muss auf das Kronenprofil aufgefüllt werden. Außerhalb (Ost 516→560 und 584→590) ist der Damm intakt → unverändert lassen.
- Vorgehen: Gelände im Durchbruch entlang der Geraden auf das Kronenprofil anheben; erhaltene Teile bleiben unangetastet.
- Default-Parameter (anpassbar): **Kronenbreite 3 m**, **Böschung 1:2** (1 m Höhe = 2 m horizontal).

## Gebäude 1 = BERGSCHMIEDE (Fachwerkhaus)
- Grundfläche **24 × 8,5 m** (verbindlich). Klick-Ecken ergaben grob ~34×10 m → Position/Ausrichtung daraus, Größe = 24×8,5.
- **Eingeschossig**, Wandhöhe **3,0 m**, **Spitzdach (Satteldach) +3,0 m** → First ~6 m.
- Klick-Ecken: (497,441)H253.1 · (506,448)H251.9 · (482,471)H251.7 · (475,465)H252.5
- Lage: **auf ~Dammkronenhöhe (~252 m)**, etwas **versetzt hinter dem Damm** (leicht nördlich der Kronenlinie). Bodenniveau Vorschau ~251,8 m.
- Bauart laut techn. Zeichnung (2 Ansichten: Giebel + Traufe): **Fachwerk**, steiles Satteldach (Dach ≈ Wandhöhe), **zwei geschwungene Fledermaus-Gauben** an der Traufseite, kleine Schornsteine an den Firstenden. (Details für spätere Ausgestaltung; Massenmodell = Kasten + Satteldach.)

## Gebäude 2 = TREIBE- UND MASCHINENHAUS + KESSELHAUS (zwei zusammengebaute Teile)
**Namen (vom Nutzer):** vorderer/höherer Teil über dem Schacht = **Treibe- und Maschinenhaus** (zweistöckig, ~6 m Wand); hinterer/niedrigerer Teil mit Schornstein = **Kesselhaus**.
**Schachtlage (MERKEN):** Schachtmittelpunkt liegt **4,5 m von der hinteren Treibehaus-Wand** entfernt, mittig auf dem First (aus Zeichnung).
**Kesselhaus-Boden:** 2,8 m unter dem Boden des Treibe-/Maschinenhauses (aus Zeichnung).

- Gesamt **Länge 29,3 m** × **Breite 9 m** (Breite aus früherer Angabe, beim Go bestätigen).
- **Hinterer Teil (näher am Damm): 13,16 m lang** → vorderer Teil ≈ 16,14 m.
- Hinterer Teil ist **niedriger und tiefer** gelegen (dammseitig).
- **Nur eingeschossig**, **Spitzdach**. Höhen: **Erdgeschoss 4,42 m**, **Spitzdach 2,75 m** → First ~7,17 m.
  - (Korrigiert die frühere Angabe „2 Stockwerke / ~11 m" — gilt nicht mehr.)
- Klick-Ecken: (517,487)H245.5 · (527,494)H241.2 · (499,512)H243.4 · (492,504)H244.4
  - Dammnahe Ecken (#9/#10, Nord 487/494) liegen bei ~241–245 m, also deutlich **unter** der Dammkrone (~252 m).

### Schornstein (zu Gebäude 2)
- **Höhe 16 m** (angenommen), schlanker vertikaler Baukörper (Querschnitt-Annahme ~1×1 m — beim Go bestätigen).
- Lage: **mittig (längs) am eingeschossigen Gebäudeteil**, **hinter dem Gebäude auf der dem Damm abgewandten Seite**.
  - Damm liegt südlich (Nord ~441–451) → abgewandte Seite = **Nordseite** von Gebäude 2 (höhere Nord-Werte, ~504–512).
  - Also: Schornstein an der Nordwand, auf halber Länge des eingeschossigen Teils, knapp außerhalb/hinter der Wand.
- Offen: Welcher der beiden Teile ist „der eingeschossige" (vorderer ~16,14 m oder hinterer ~13,16 m)? Querschnittsmaß des Schornsteins?

### Geländeanpassung (Grading)
`build_terrain_grade.py` passt das Gelände an Gebäude 2 an (Ergebnis
`dgm1_graded.bin` / `dgm1_dam_graded.bin`, vom Viewer geladen):
- **Treibe-/Maschinenhaus:** ebene Plattform auf seiner Bodenhöhe (`floorAbs`).
- **Kesselhaus:** *Rampe* statt Stufe — an der Fuge auf Treibehaus-Niveau, fällt
  über die ~13 m Länge sanft auf Kesselhaus-Niveau ab. Das Bodenniveau stimmt nur
  am **freien (dammseitigen) Ende**; zur Fuge hin liegt das Gelände an der Wand an.
- Außen über `BLEND`=12 m / `APRON`=1,5 m weich ins Naturgelände ausgeblendet.
- **Schornstein-Fuß** liegt auf Kesselhaus-Bodenhöhe (`front_baseY − 2,8`).

Zusätzlich abgetragene, vom Nutzer in der Klick-Karte markierte Bereiche
(Polygone in `build_terrain_grade.py`, Rand-Überblendung `FEATHER`=3,5 m):
- **Halde** (aufgeschüttetes Dammmaterial, nordseitig des Damms, *westlich des
  Durchbruchs*, Ost 538–559 / Nord 457–479): auf das **Damm-Gefälle** abgetragen —
  Profil = Kronengerade #1→#2 minus Böschung 1:2, am Fuß auf `DAM_TOE`=243 m
  auslaufend, nur Abtrag (`min(Profil bzw. Fuß, Bestand)`) → Damm-Krone bleibt
  unangetastet (Kontrolle: Nord 443–449 unverändert ~252 m). Abtrag bis ~5 m.
- **Hügel vor dem Kesselhaus** (dammseitig, Ost 518–531 / Nord 469–485): auf
  Kesselhaus-Bodenhöhe (242,7 m) eingeebnet.
- **Glättung (Laplace)** im 33-Punkt-Polygon `SMOOTH_POLY` (Damm-Böschung +
  Übergang zum Bruch, Ost 514–566 / Nord 450–489): Inneres per `laplace_fill`
  (∇²h=0, Polygon-Ränder als feste Dirichlet-Werte) → glattest mögliche Fläche
  ganz **ohne innere Erhebungen**, Ränder unverändert. 361 Zellen.

Klick-Karte `dist/lichtloch-pick.html`: gezoomt (Ost 440–620 / Nord 400–580),
zeigt das *bearbeitete* Gelände (`dgm1g_hs_{nw,se}.png` aus build_terrain_grade)
+ Damm/Gebäude als Bezug; Markiertyp „Glätten".

### Viewer `dist/lichtloch-rekonstruktion.html`
Panel-Umschalter **Topographie**:
- **1853** = rekonstruiert: `dgm1_dam_graded.bin` + Gebäude + Schornstein + Wasser.
- **heute** = Rohgelände `dgm1.bin` (Bruch, Halde), ohne Gebäude/Wasser.
Nach dem Laden wird die Szene per `applyTopo()` an den (ggf. vom Browser
wiederhergestellten) Panel-Zustand angeglichen; Schacht-Marker werden auf das
aktive Gelände nachgeführt (`activeTerr`).

### ⚠️ Wichtiger Vermerk (vom Nutzer)
Der hintere, dammnahe Teil von Gebäude 2 liegt tiefer (~241–245 m) als die Dammkrone (~252 m).
**Falls sich Gebäude 2 (hinterer Teil) nicht mit der Geländehöhe / dem rekonstruierten Damm in Einklang bringen lässt** (z. B. Damm-Böschung überlappt den niedrigeren Gebäudeteil), ist das bekannt und beabsichtigt — beim Bau gesondert behandeln (Gebäudeteil ggf. in die Böschung einbinden / eigene Bodenhöhe pro Teil).

## Offene Punkte (beim „Go" bestätigen)
1. Gebäude 2: Breite wirklich 9 m? Höhe des **hinteren** (niedrigeren) Teils — wie viel niedriger als 4,42 m EG?
2. Gebäude 2: Gelten 4,42 m EG + 2,75 m Dach für den **vorderen** Teil, beide Teile, oder nur das Hauptgebäude?
3. Damm: Kronenhöhe 252 m, Breite 3 m, Böschung 1:2 ok?
4. Dachfirst-Ausrichtung der Spitzdächer (entlang der Längsseite — Standardannahme).

## Weitere vom Nutzer angekündigte Angaben
- (Nutzer war beim Erfassen noch nicht fertig — weitere Daten möglich.)
