#!/usr/bin/env python3
"""
01_extraer_wpp.py — Genera las series de fecundidad a partir de UN WPP 2024.

Fuente: United Nations, World Population Prospects 2024, variante media.
  · WPP2024_Demographic_Indicators_Medium.csv.gz   (TFR de periodo)
  · WPP2024_Fertility_by_Age1.csv.gz               (ASFR por edad simple → cohortes)

Uso:
  python3 01_extraer_wpp.py --fuente-dir ~/.hermes/cache/scratch
  python3 01_extraer_wpp.py                 # descarga los dos archivos (~320 MB)

Salidas (en ../datos/):
  · tfr_8entidades_1950_2024.csv           600 filas  (8 series × 75 años)
  · tfr_cohorte_hijos_30_1950_1995.csv     368 filas  (8 series × 46 cohortes)
  · manifiesto.csv                         una fila por serie, con sha256

El script NO inventa valores: todo sale de las columnas TFR y ASFR del WPP.
Cualquier cambio de cifra tiene que venir de una nueva revisión del WPP.
"""

import argparse
import csv
import gzip
import hashlib
import os
import sys
import urllib.request

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATOS = os.path.join(BASE, "datos")

URLS = {
    "wpp.csv.gz": "https://population.un.org/wpp/assets/Excel%20Files/1_Indicator%20(Standard)/CSV_FILES/WPP2024_Demographic_Indicators_Medium.csv.gz",
    "wpp_age1.csv.gz": "https://population.un.org/wpp/assets/Excel%20Files/1_Indicator%20(Standard)/CSV_FILES/WPP2024_Fertility_by_Age1.csv.gz",
}

# LocID del WPP → nombre usado en el repo
ENTIDADES = {
    "904": "LAC",
    "76": "Brasil",
    "484": "México",
    "170": "Colombia",
    "32": "Argentina",
    "604": "Perú",
    "152": "Chile",
    "600": "Paraguay",
}

NOMBRE_LARGO = {
    "LAC": "América Latina y el Caribe",
    "Brasil": "Brasil",
    "México": "México",
    "Colombia": "Colombia",
    "Argentina": "Argentina",
    "Perú": "Perú",
    "Chile": "Chile",
    "Paraguay": "Paraguay",
}

FECHA_CONSULTA = "2026-10-19"
URL_MANIFIESTO = {
    "png": "https://population.un.org/wpp/",
}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def asegurar_fuente(fuente_dir):
    """Devuelve las rutas de los dos CSV.gz, descargándolos si faltan."""
    rutas = {}
    for nombre, url in URLS.items():
        ruta = os.path.join(fuente_dir, nombre)
        if not os.path.exists(ruta):
            print(f"  descargando {nombre} …", end="", flush=True)
            urllib.request.urlretrieve(url, ruta)
            print(f" {os.path.getsize(ruta) / 2**20:.0f} MB")
        rutas[nombre] = ruta
    return rutas


def serie_tfr(ruta):
    """(entidad, año) → TFR publicado, 1950-2024."""
    out = {}
    with gzip.open(ruta, "rt", encoding="utf-8", errors="ignore") as f:
        for fila in csv.DictReader(f):
            if fila.get("LocID") not in ENTIDADES or not fila.get("TFR"):
                continue
            try:
                anio = int(float(fila["Time"]))
            except ValueError:
                continue
            if 1950 <= anio <= 2024:
                out[(ENTIDADES[fila["LocID"]], anio)] = float(fila["TFR"])
    return out


def serie_cohorte(ruta):
    """
    Hijos acumulados a los 30 años por cohorte de nacimiento.
    Para la cohorte b: suma de ASFR de edades simples 15…29 en los años b+15 … b+29.
    Última cohorte con ventana completa: 1995 (cumple 29 años en 2024).
    """
    asfr = {}
    with gzip.open(ruta, "rt", encoding="utf-8", errors="ignore") as f:
        for fila in csv.DictReader(f):
            if fila.get("LocID") not in ENTIDADES or fila.get("Variant") != "Medium":
                continue
            try:
                anio = int(float(fila["Time"]))
                edad = int(float(fila["AgeGrpStart"]))
                valor = float(fila["ASFR"]) / 1000.0
            except (ValueError, TypeError):
                continue
            if 1950 <= anio <= 2024 and 15 <= edad <= 29:
                asfr[(ENTIDADES[fila["LocID"]], anio, edad)] = valor

    out = {}
    for entidad in ENTIDADES.values():
        for cohorte in range(1950, 1996):
            if cohorte + 29 > 2024:
                continue
            out[(entidad, cohorte)] = sum(
                asfr.get((entidad, cohorte + edad, edad), 0.0) for edad in range(15, 30)
            )
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fuente-dir", default=os.path.join(BASE, "..", ".fuente"),
                    help="carpeta con los .csv.gz del WPP (se descargan si no están)")
    args = ap.parse_args()

    os.makedirs(DATOS, exist_ok=True)
    fuente = os.path.abspath(args.fuente_dir)
    os.makedirs(fuente, exist_ok=True)

    print("1/4 Fuente")
    rutas = asegurar_fuente(fuente)
    sha_fuente = {k: sha256(v) for k, v in rutas.items()}
    for k, v in sha_fuente.items():
        print(f"   {k}: sha256 {v[:16]}… ({os.path.getsize(rutas[k])/2**20:.0f} MB)")

    print("2/4 Serie de periodo 1950-2024")
    tfr = serie_tfr(rutas["wpp.csv.gz"])
    ruta_tfr = os.path.join(DATOS, "tfr_8entidades_1950_2024.csv")
    with open(ruta_tfr, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["entidad", "entidad_nombre", "anio", "tgf"])
        for entidad in ENTIDADES.values():
            for anio in range(1950, 2025):
                w.writerow([entidad, NOMBRE_LARGO[entidad], anio, round(tfr[(entidad, anio)], 4)])
    print(f"   {ruta_tfr} · {sum(1 for _ in open(ruta_tfr)) - 1} filas")

    print("3/4 Cohorte: hijos acumulados a los 30")
    coh = serie_cohorte(rutas["wpp_age1.csv.gz"])
    ruta_coh = os.path.join(DATOS, "tfr_cohorte_hijos_30_1950_1995.csv")
    with open(ruta_coh, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["entidad", "entidad_nombre", "cohorte_nacimiento", "hijos_a_los_30", "cumple_30_en"])
        for entidad in ENTIDADES.values():
            for cohorte in range(1950, 1996):
                w.writerow([entidad, NOMBRE_LARGO[entidad], cohorte,
                            round(coh[(entidad, cohorte)], 3), cohorte + 30])
    print(f"   {ruta_coh} · {sum(1 for _ in open(ruta_coh)) - 1} filas")

    print("4/4 Manifiesto")
    ruta_man = os.path.join(DATOS, "manifiesto.csv")
    filas = []
    for entidad in ENTIDADES.values():
        filas.append({
            "id": f"TFR-{entidad}",
            "dato": "Tasa global de fecundidad, serie de periodo 1950-2024",
            "entidad": entidad,
            "anio_cobertura": "1950-2024",
            "archivo": "datos/tfr_8entidades_1950_2024.csv",
            "url_fuente": URLS["wpp.csv.gz"],
            "fecha_consulta": FECHA_CONSULTA,
            "sha256_archivo": sha256(ruta_tfr),
            "sha256_fuente": sha_fuente["wpp.csv.gz"],
            "script": "scripts/01_extraer_wpp.py",
            "estado": "verificado",
            "nota": "TFR publicado por el WPP; 2024 es estimación del modelo, no registro",
        })
        filas.append({
            "id": f"COH-{entidad}",
            "dato": "Hijos acumulados a los 30 años por cohorte de nacimiento",
            "entidad": entidad,
            "anio_cobertura": "cohortes 1950-1995",
            "archivo": "datos/tfr_cohorte_hijos_30_1950_1995.csv",
            "url_fuente": URLS["wpp_age1.csv.gz"],
            "fecha_consulta": FECHA_CONSULTA,
            "sha256_archivo": sha256(ruta_coh),
            "sha256_fuente": sha_fuente["wpp_age1.csv.gz"],
            "script": "scripts/01_extraer_wpp.py",
            "estado": "derivado verificado",
            "nota": "suma de ASFR de edades simples 15-29; no es una serie publicada por el WPP",
        })
    campos = ["id", "dato", "entidad", "anio_cobertura", "archivo", "url_fuente",
              "fecha_consulta", "sha256_archivo", "sha256_fuente", "script", "estado", "nota"]
    with open(ruta_man, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(filas)
    print(f"   {ruta_man} · {len(filas)} filas")
    print("\nListo. Verificá integridad con: python3 scripts/verificar_manifiesto.py")


if __name__ == "__main__":
    sys.exit(main())
