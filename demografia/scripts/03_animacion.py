#!/usr/bin/env python3
"""
03_animacion.py — GIF animado de la TGF 1950-2024.

Lee `datos/tfr_8entidades_1950_2024.csv` y escribe `figuras/tfr-animacion.gif`:
un barrido año por año con el panel de valores a la derecha.

Uso:
  python3 scripts/03_animacion.py
"""

import csv
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from PIL import Image

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUENTE = os.path.join(BASE, "datos", "tfr_8entidades_1950_2024.csv")
SALIDA = os.path.join(BASE, "figuras", "tfr-animacion.gif")

ORDEN = ["LAC", "Brasil", "Paraguay", "México", "Colombia", "Argentina", "Perú", "Chile"]
NOMBRE = {
    "LAC": "América Latina y el Caribe", "Brasil": "Brasil", "Paraguay": "Paraguay",
    "México": "México", "Colombia": "Colombia", "Argentina": "Argentina",
    "Perú": "Perú", "Chile": "Chile",
}
COLOR = {
    "LAC": "#0072B2", "Brasil": "#D55E00", "Paraguay": "#009E73", "México": "#CC79A7",
    "Colombia": "#8C564B", "Argentina": "#B8860B", "Perú": "#6A3D9A", "Chile": "#333333",
}
TRAZO = {
    "LAC": "solid", "Brasil": "solid", "Paraguay": (0, (7, 4)), "México": (0, (2, 3)),
    "Colombia": (0, (9, 3, 2, 3)), "Argentina": (0, (5, 3)), "Perú": (0, (3, 3)),
    "Chile": (0, (1, 3)),
}
TINTA, GRIS, SUAVE = "#1a1a1a", "#5a5a5a", "#8a8a8a"


def cargar():
    serie = {k: {} for k in ORDEN}
    with open(FUENTE, encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            serie[fila["entidad"]][int(fila["anio"])] = float(fila["tgf"])
    return serie


def registrar_en_manifiesto():
    """Añade o actualiza la fila del GIF en datos/manifiesto.csv."""
    import hashlib

    ruta_man = os.path.join(BASE, "datos", "manifiesto.csv")
    if not os.path.exists(ruta_man):
        return
    h = hashlib.sha256()
    with open(SALIDA, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    filas = list(csv.DictReader(open(ruta_man, encoding="utf-8")))
    campos = list(filas[0].keys())
    nueva = {
        "id": "GIF-TFR",
        "dato": "Animación 1950-2024 (GIF, 75 cuadros)",
        "entidad": "8 series",
        "anio_cobertura": "1950-2024",
        "archivo": "figuras/tfr-animacion.gif",
        "url_fuente": "https://population.un.org/wpp/",
        "fecha_consulta": "2026-10-19",
        "sha256_archivo": h.hexdigest(),
        "sha256_fuente": next((f["sha256_fuente"] for f in filas if f["id"] == "TFR-LAC"), ""),
        "script": "scripts/03_animacion.py",
        "estado": "derivado verificado",
        "nota": "misma serie que tfr_8entidades_1950_2024.csv, renderizada cuadro a cuadro",
    }
    filas = [f for f in filas if f["id"] != "GIF-TFR"] + [nueva]
    with open(ruta_man, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(filas)


def main():
    serie = cargar()
    anios = range(1950, 2025)
    plt.rcParams.update({"font.family": "Helvetica", "font.size": 9})

    fig = plt.figure(figsize=(7.9, 4.5), dpi=110, facecolor="white")
    ax = fig.add_axes([0.065, 0.12, 0.60, 0.76])
    px = fig.add_axes([0.705, 0.12, 0.275, 0.76])
    px.axis("off")

    frames = []
    total = len(list(anios))

    for i, anio in enumerate(anios):
        ax.clear()
        px.clear()
        px.axis("off")

        ax.set_xlim(1950, 2024)
        ax.set_ylim(0, 7.3)
        ax.set_yticks(range(0, 8, 1))
        ax.set_xticks([1950, 1960, 1970, 1980, 1990, 2000, 2010, 2024])
        ax.grid(axis="y", color="#ededed", linewidth=0.7)
        ax.set_axisbelow(True)
        for lado in ("top", "right", "left"):
            ax.spines[lado].set_visible(False)
        ax.spines["bottom"].set_color("#d5d5d5")
        ax.tick_params(colors=SUAVE, labelsize=8, length=2)
        ax.set_ylabel("Hijos por mujer", color=SUAVE, fontsize=8)

        ax.axhline(2.1, color="#b03a2e", linewidth=1, linestyle=(0, (5, 4)), zorder=1)
        ax.axvline(anio, color="#e3e3e3", linewidth=0.9, zorder=0)
        ax.text(1951, 2.2, "reemplazo · 2,10", color="#b03a2e", fontsize=7.6)

        for k in ORDEN:
            xs = [a for a in range(1950, anio + 1)]
            ys = [serie[k][a] for a in xs]
            ax.plot(xs, ys, color=COLOR[k], linestyle=TRAZO[k], linewidth=1.9,
                    solid_capstyle="round", zorder=3)
            ax.scatter([anio], [serie[k][anio]], s=26, color=COLOR[k], zorder=4,
                       edgecolor="white", linewidth=0.8)

        # Panel de valores del año
        ordenados = sorted(ORDEN, key=lambda k: -serie[k][anio])
        px.set_xlim(0, 1)
        px.set_ylim(0, 8.6)
        px.text(0.0, 8.35, str(anio), fontsize=25, fontweight="bold", color=TINTA)
        px.text(0.0, 7.95, "hijos por mujer", fontsize=8, color=SUAVE)
        for j, k in enumerate(ordenados):
            y = 7.15 - j * 0.92
            px.plot([0.0, 0.16], [y + 0.28, y + 0.28], color=COLOR[k], linewidth=3,
                    linestyle=TRAZO[k], solid_capstyle="butt")
            px.text(0.22, y + 0.16, NOMBRE[k][:22] if k != "LAC" else "América Latina",
                    fontsize=8.4, color=TINTA if k in ("LAC", "Brasil", "Paraguay") else GRIS,
                    fontweight="bold" if k in ("LAC", "Brasil", "Paraguay") else "normal")
            px.text(1.0, y + 0.16, f"{serie[k][anio]:.2f}".replace(".", ","),
                    fontsize=10.5, color=COLOR[k], fontweight="bold", ha="right")

        fig.suptitle("La fecundidad cae en toda la región", x=0.065, y=0.965,
                     ha="left", fontsize=13.5, fontweight="bold", color=TINTA)
        fig.text(0.065, 0.905, "Tasa global de fecundidad por año · UN WPP 2024, variante media",
                 ha="left", fontsize=8.2, color=GRIS)

        # Barra de progreso
        fig.patches = [p for p in fig.patches if getattr(p, "_barra", False) is False]
        from matplotlib.patches import Rectangle
        barra = Rectangle((0.065, 0.045), 0.60 * (i + 1) / total, 0.008,
                          transform=fig.transFigure, facecolor="#1a1a1a", edgecolor="none")
        barra._barra = True
        fig.patches.append(barra)
        fondo = Rectangle((0.065, 0.045), 0.60, 0.008, transform=fig.transFigure,
                          facecolor="#e8e8e8", edgecolor="none", zorder=0)
        fondo._barra = True
        fig.patches.append(fondo)

        fig.canvas.draw()
        import numpy as np
        img = Image.fromarray(np.asarray(fig.canvas.buffer_rgba())).convert("RGB")
        frames.append(img.quantize(colors=128, method=Image.MEDIANCUT, dither=Image.NONE))

    # pausa final de 1,2 s
    frames += [frames[-1]] * 12
    frames[0].save(SALIDA, save_all=True, append_images=frames[1:],
                   duration=70, loop=0, optimize=True, disposal=2)
    registrar_en_manifiesto()

    kb = os.path.getsize(SALIDA) / 1024
    print(f"GIF: {SALIDA} · {len(frames)} cuadros · {img.width}×{img.height} · {kb:.0f} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
