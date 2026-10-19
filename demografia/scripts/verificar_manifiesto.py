#!/usr/bin/env python3
"""
verificar_manifiesto.py — Control de integridad del módulo demografía.

Comprueba tres cosas y falla (exit 1) si alguna no se cumple:

  1. Cada fila del manifiesto apunta a un archivo que existe.
  2. El sha256 del archivo coincide con el registrado en el manifiesto.
  3. Cada figura D3 lleva impreso, en su bloque META, el sha256 del CSV que consume.

Uso:
  python3 scripts/verificar_manifiesto.py

Se puede correr en CI (ver .github/workflows/verificar-datos.yml): si alguien edita
un CSV sin volver a sellar las figuras, el job falla y el commit no pasa limpio.
"""

import csv
import hashlib
import os
import re
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATOS = os.path.join(BASE, "datos")
FIGURAS = os.path.join(BASE, "figuras")

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
    manifiesto = os.path.join(DATOS, "manifiesto.csv")
    if not os.path.exists(manifiesto):
        print(f"✗ no existe {manifiesto}")
        return 1

    filas = list(csv.DictReader(open(manifiesto, encoding="utf-8")))
    errores = []
    verificados = 0

    print(f"1) Archivos del manifiesto ({len(filas)} filas)")
    for fila in filas:
        ruta = os.path.join(BASE, fila["archivo"])
        if not os.path.exists(ruta):
            errores.append(f"falta {fila['archivo']} (id {fila['id']})")
            continue
        real = sha256(ruta)
        if real != fila["sha256_archivo"]:
            errores.append(
                f"hash distinto en {fila['archivo']} (id {fila['id']}): "
                f"manifiesto {fila['sha256_archivo'][:12]}… vs disco {real[:12]}…")
            continue
        verificados += 1
    print(f"   {verificados}/{len(filas)} filas verificadas")

    print("2) Figuras selladas con el hash de su dato")
    for figura, csv_nombre in FIGURAS_CSV.items():
        ruta_html = os.path.join(FIGURAS, figura)
        ruta_csv = os.path.join(DATOS, csv_nombre)
        if not os.path.exists(ruta_html):
            errores.append(f"falta la figura {figura}")
            continue
        html = open(ruta_html, encoding="utf-8").read()
        esperado = sha256(ruta_csv)
        m = re.search(r'sha256:\s*"([0-9a-fA-F]+)"', html)
        if not m:
            errores.append(f"{figura}: no tiene campo sha256")
        elif m.group(1) != esperado:
            errores.append(
                f"{figura}: hash impreso {m.group(1)[:12]}… ≠ hash del CSV {esperado[:12]}… "
                f"(correr scripts/02_sellar_figuras.py)")
        else:
            print(f"   ✓ {figura} · {esperado[:16]}…")

    print("3) Datos con la forma esperada")
    for nombre, filas_esperadas in (("tfr_8entidades_1950_2024.csv", 600),
                                    ("tfr_cohorte_hijos_30_1950_1995.csv", 368)):
        ruta = os.path.join(DATOS, nombre)
        if not os.path.exists(ruta):
            errores.append(f"falta {nombre}")
            continue
        n = sum(1 for _ in open(ruta, encoding="utf-8")) - 1
        if n != filas_esperadas:
            errores.append(f"{nombre}: {n} filas, se esperaban {filas_esperadas}")
        else:
            print(f"   ✓ {nombre} · {n} filas")

    print()
    if errores:
        print(f"FALLA — {len(errores)} problema(s):")
        for e in errores:
            print(f"   ✗ {e}")
        return 1
    print("PASS — manifiesto, figuras y datos consistentes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
