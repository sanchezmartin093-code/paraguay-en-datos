#!/usr/bin/env python3
"""
02_sellar_figuras.py — Inyecta el sha256 del dato dentro de cada figura D3.

Cada HTML lleva un bloque META con el hash del CSV que consume. Este script lo
escribe: si el CSV cambia y no se vuelve a sellar, `verificar_manifiesto.py` falla.

Uso:
  python3 02_sellar_figuras.py
"""

import hashlib
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATOS = os.path.join(BASE, "datos")
FIGURAS = os.path.join(BASE, "figuras")

# figura → CSV que consume
FIGURAS_CSV = {
    "tfr-latam-1950-2024.html": "tfr_8entidades_1950_2024.csv",
    "tfr-generacional.html": "tfr_cohorte_hijos_30_1950_1995.csv",
    "tfr-animacion.html": "tfr_8entidades_1950_2024.csv",
}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    fallos = 0
    for figura, csv_nombre in FIGURAS_CSV.items():
        ruta_csv = os.path.join(DATOS, csv_nombre)
        ruta_html = os.path.join(FIGURAS, figura)
        if not os.path.exists(ruta_csv):
            print(f"  ✗ falta {csv_nombre}")
            fallos += 1
            continue
        if not os.path.exists(ruta_html):
            print(f"  ✗ falta {figura}")
            fallos += 1
            continue

        digest = sha256(ruta_csv)
        html = open(ruta_html, encoding="utf-8").read()
        nuevo, n = re.subn(r'(sha256:\s*)"[0-9a-fA-F]*"|(sha256:\s*)"PENDIENTE"',
                           lambda m: (m.group(1) or m.group(2)) + '"' + digest + '"',
                           html, count=1)
        if n == 0:
            print(f"  ✗ {figura}: no encontré el campo sha256 en el bloque META")
            fallos += 1
            continue
        open(ruta_html, "w", encoding="utf-8").write(nuevo)
        print(f"  ✓ {figura} ← {digest[:16]}…")

    if fallos:
        print(f"\n{fallos} problema(s).")
        return 1
    print("\nFiguras selladas. Verificá con: python3 scripts/verificar_manifiesto.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
