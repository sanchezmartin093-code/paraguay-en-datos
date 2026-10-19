# demografia/ — Fecundidad y transición demográfica

Series de **tasa global de fecundidad (TGF)** para América Latina y el Caribe y siete países,
con dos lecturas del mismo fenómeno: por **año calendario** (1950-2024) y por **generación**
(hijos acumulados a los 30 años, cohortes 1950-1995).

## Figuras interactivas (D3.js)

| Figura | Qué muestra | Datos |
|---|---|---|
| [`figuras/tfr-latam-1950-2024.html`](figuras/tfr-latam-1950-2024.html) | TGF por año, 1950-2024. Botón para saltar a los últimos 20 años; tooltip con los ocho valores de cada año | `datos/tfr_8entidades_1950_2024.csv` |
| [`figuras/tfr-generacional.html`](figuras/tfr-generacional.html) | Hijos acumulados a los 30 años por cohorte de nacimiento (1950-1995), con eje doble: año de nacimiento y edad en 2025 | `datos/tfr_cohorte_hijos_30_1950_1995.csv` |

**Cómo verlas.** Un navegador no puede leer archivos locales desde `file://` por seguridad, así que
hay dos caminos:

```bash
# 1) servidor local, desde la raíz del repo
python3 -m http.server 8000
# luego: http://localhost:8000/demografia/figuras/tfr-latam-1950-2024.html
```

2) GitHub Pages: *Settings → Pages → Deploy from branch → main / (root)*. Las rutas relativas
(`../datos/...`) funcionan igual porque las figuras viven un nivel por debajo de `demografia/`.

## Estructura

```
demografia/
├── datos/
│   ├── tfr_8entidades_1950_2024.csv           600 filas (8 series × 75 años)
│   ├── tfr_cohorte_hijos_30_1950_1995.csv     368 filas (8 series × 46 cohortes)
│   └── manifiesto.csv                         16 filas: fuente, fecha, sha256, script
├── figuras/
│   ├── tfr-latam-1950-2024.html
│   └── tfr-generacional.html
├── scripts/
│   ├── 01_extraer_wpp.py        descarga el WPP y regenera los dos CSV + el manifiesto
│   ├── 02_sellar_figuras.py     inyecta el sha256 del dato dentro de cada figura
│   └── verificar_manifiesto.py  control de integridad (lo corre la CI)
└── METODOLOGIA.md
```

## Reproducir

```bash
cd demografia
python3 scripts/01_extraer_wpp.py        # 1) datos desde el WPP (descarga ~320 MB la primera vez)
python3 scripts/02_sellar_figuras.py     # 2) sella las figuras con el hash del dato
python3 scripts/verificar_manifiesto.py  # 3) verifica: debe imprimir PASS
```

El paso 3 es el mismo que corre GitHub Actions en cada push: si alguien edita un CSV y no vuelve
a sellar las figuras, el chequeo falla.

## Qué se puede y qué no se puede decir con estos datos

- **Sí:** la TGF de la región cayó de 5,79 (1950) a 1,80 (2024); siete de las ocho series están bajo
  el reemplazo (2,1). La cohorte de 1995 acumuló 1,33 hijos a los 30 años frente a 2,77 de la de 1950.
- **No:** que 2024 sea un dato observado. El WPP lo **estima**; el registro administrativo de muchos
  países llega más tarde o está incompleto.
- **No:** comparar los hijos a los 30 años con el umbral de reemplazo. Es fecundidad parcial.

Detalle de fuentes, validación y límites en [`METODOLOGIA.md`](METODOLOGIA.md).
