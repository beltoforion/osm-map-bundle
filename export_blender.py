#!/bin/python3
"""
Exportiert das Hoehenmodell um das 1. Lichtloch als glTF-Binaerdatei (.glb) fuer
Blender - je eine Datei fuer DGM1 (Gelaende) und DOM1 (Oberflaeche).

Grundlage sind die von build_lichtloch_3d.py erzeugten Hoehengitter
(dist/lichtloch3d/*.bin, 512x512 Float32, Nord oben). Erzeugt wird ein
echtes Dreiecksnetz mit:
  - Position   (Meter; 1 Blender-Einheit = 1 m, X=Ost, Y=Hoehe, Z=Sued)
  - Normalen   (aus dem Hoehengradienten, fuer korrekte Schattierung)
  - Vertexfarben (hypsometrisch nach Hoehe, wie im Web-Viewer)

Hoehe Y = Hoehe ueber dem gemeinsamen Minimum beider Modelle (~227,9 m), damit
DGM1 und DOM1 vertikal zusammenpassen, wenn man beide in Blender laedt.

Import in Blender: Datei > Import > glTF 2.0 (.glb). Massstab ist Meter.
"""

import os
import json
import struct

import numpy as np

DATADIR = "./dist/lichtloch3d"
OUTDIR = "./dist/blender"
PRODUCTS = ("dgm1", "dom1")

# hypsometrische Farbskala (gruen -> oliv -> braun -> weiss), Stops in [0,1]
STOPS = [(0.0, (46, 125, 50)), (0.45, (158, 157, 36)),
         (0.75, (141, 110, 99)), (1.0, (245, 245, 245))]


def hypso(t):
    t = float(np.clip(t, 0, 1))
    for i in range(1, len(STOPS)):
        if t <= STOPS[i][0]:
            (a0, ca), (b0, cb) = STOPS[i - 1], STOPS[i]
            f = (t - a0) / (b0 - a0) if b0 > a0 else 0.0
            return tuple(int(round(ca[k] + (cb[k] - ca[k]) * f)) for k in range(3))
    return STOPS[-1][1]


def pad4(b, fill=b"\x00"):
    return b + fill * ((4 - len(b) % 4) % 4)


def write_glb(path, positions, normals, colors, indices, name):
    """Schreibt ein minimales, valides glb (POSITION, NORMAL, COLOR_0, indices)."""
    pos_b = positions.astype("<f4").tobytes()
    nrm_b = normals.astype("<f4").tobytes()
    col_b = colors.astype("<u1").tobytes()            # VEC4 ubyte (normalisiert)
    idx_b = indices.astype("<u4").tobytes()

    # BufferViews 4-Byte-aligned aneinanderreihen
    blobs, views, offset = [], [], 0
    for data, target in ((pos_b, 34962), (nrm_b, 34962), (col_b, 34962), (idx_b, 34963)):
        data = pad4(data)
        views.append({"buffer": 0, "byteOffset": offset, "byteLength": len(data), "target": target})
        blobs.append(data)
        offset += len(data)
    bindata = b"".join(blobs)
    n = len(positions) // 3

    gltf = {
        "asset": {"version": "2.0", "generator": "osm-map-bundle/export_blender"},
        "scene": 0, "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0, "name": name}],
        "meshes": [{"name": name, "primitives": [{
            "attributes": {"POSITION": 0, "NORMAL": 1, "COLOR_0": 2},
            "indices": 3, "mode": 4}]}],
        "buffers": [{"byteLength": len(bindata)}],
        "bufferViews": views,
        "accessors": [
            {"bufferView": 0, "componentType": 5126, "count": n, "type": "VEC3",
             "min": positions.reshape(-1, 3).min(0).tolist(),
             "max": positions.reshape(-1, 3).max(0).tolist()},
            {"bufferView": 1, "componentType": 5126, "count": n, "type": "VEC3"},
            {"bufferView": 2, "componentType": 5121, "normalized": True, "count": n, "type": "VEC4"},
            {"bufferView": 3, "componentType": 5125, "count": len(indices), "type": "SCALAR"},
        ],
    }

    json_b = pad4(json.dumps(gltf).encode("utf-8"), b" ")
    total = 12 + 8 + len(json_b) + 8 + len(bindata)
    with open(path, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, total))          # glb-Header
        f.write(struct.pack("<II", len(json_b), 0x4E4F534A)); f.write(json_b)   # JSON-Chunk
        f.write(struct.pack("<II", len(bindata), 0x004E4942)); f.write(bindata)  # BIN-Chunk


def build(product, meta, global_min, global_max):
    G = meta["grid"]
    size = float(meta["sizeMeters"])
    cell = size / (G - 1)
    h = np.fromfile(os.path.join(DATADIR, f"{product}.bin"), dtype="<f4").reshape(G, G)

    rows, cols = np.indices((G, G), dtype=np.float32)
    X = (cols / (G - 1) - 0.5) * size           # Ost
    Y = h - global_min                          # Hoehe (gemeinsames Datum)
    Z = (rows / (G - 1) - 0.5) * size           # Sued
    positions = np.stack([X, Y, Z], axis=-1).reshape(-1, 3)

    gx = np.gradient(h, cell, axis=1)           # dHoehe/dOst
    gz = np.gradient(h, cell, axis=0)           # dHoehe/dSued
    nrm = np.stack([-gx, np.ones_like(h), -gz], axis=-1).reshape(-1, 3)
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True)

    span = (global_max - global_min) or 1.0
    lut = np.array([hypso(i / 255.0) for i in range(256)], dtype=np.uint8)
    ti = np.clip(((h - global_min) / span) * 255, 0, 255).astype(np.uint8).ravel()
    colors = np.empty((G * G, 4), dtype=np.uint8)
    colors[:, :3] = lut[ti]
    colors[:, 3] = 255

    # Dreiecksindizes (zwei pro Gitterzelle)
    r, c = np.mgrid[0:G - 1, 0:G - 1]
    v00 = (r * G + c).ravel(); v01 = v00 + 1
    v10 = v00 + G; v11 = v10 + 1
    tris = np.empty((v00.size * 2, 3), dtype=np.uint32)
    tris[0::2] = np.stack([v00, v11, v10], axis=1)
    tris[1::2] = np.stack([v00, v01, v11], axis=1)
    return positions.ravel(), nrm.ravel(), colors.ravel(), tris.ravel()


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    meta = json.load(open(os.path.join(DATADIR, "meta.json")))
    gmin = min(meta["products"][p]["min"] for p in PRODUCTS)
    gmax = max(meta["products"][p]["max"] for p in PRODUCTS)
    for product in PRODUCTS:
        pos, nrm, col, idx = build(product, meta, gmin, gmax)
        out = os.path.join(OUTDIR, f"lichtloch_{product}.glb")
        write_glb(out, pos, nrm, col, idx, f"Lichtloch_{product.upper()}")
        print(f"  {product}: {len(pos)//3} Vertices, {len(idx)//3} Dreiecke -> "
              f"{out} ({os.path.getsize(out)//1024} KB)")
    print(f"Import in Blender: Datei > Import > glTF 2.0 (.glb)  [1 Einheit = 1 m]")


if __name__ == "__main__":
    main()
