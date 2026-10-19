# Metodología — módulo demografía

## 1. Fuente

| | |
|---|---|
| **Organismo** | United Nations, Department of Economic and Social Affairs, Population Division |
| **Producto** | World Population Prospects 2024, **variante media** |
| **Archivos** | `WPP2024_Demographic_Indicators_Medium.csv.gz` (TGF de periodo) · `WPP2024_Fertility_by_Age1.csv.gz` (tasas por edad simple, para las cohortes) |
| **URL base** | `https://population.un.org/wpp/assets/Excel%20Files/1_Indicator%20(Standard)/CSV_FILES/` |
| **Consulta** | 2026-10-19 |
| **Cobertura usada** | 1950-2024 · 8 entidades: LAC (LocID 904) + Brasil, México, Colombia, Argentina, Perú, Chile y Paraguay |

Los hashes SHA-256 de los dos insumos y de cada archivo derivado están en
[`datos/manifiesto.csv`](datos/manifiesto.csv). El manifiesto es la fuente de verdad: si un hash no
coincide, el dato no vale.

## 2. Qué mide cada serie

**TGF de periodo** (`tfr_8entidades_1950_2024.csv`): hijos que tendría una mujer si viviera toda su
vida fértil con las tasas de ese año. Es un indicador **sintético**, no la descendencia real de una
generación. Responde a "cuántos hijos por mujer en ese año", no a "cuántos hijos tuvo esa mujer".

**Hijos acumulados a los 30** (`tfr_cohorte_hijos_30_1950_1995.csv`): para la cohorte nacida en *b*,
suma de las tasas específicas de fecundidad (ASFR) de las edades 15 a 29 en los años *b*+15 … *b*+29.
Es una **serie derivada** —el WPP no la publica— y mide fecundidad **parcial**: a los 30 años la
historia reproductiva no terminó. Última cohorte con ventana completa: **1995** (cumple 29 años en 2024,
30 en 2025).

**Por qué no se comparan entre sí.** La TGF de periodo en 1995 (4,11 en Paraguay) y los hijos a los 30
de la cohorte 1995 (1,60) no describen a las mismas mujeres: la primera habla de todas las mujeres en
edad fértil en 1995 —la generación de las madres— y la segunda de las que nacieron en 1995, que ese año
tenían 0 años. Confundirlas es el error más fácil de cometer con estas dos gráficas.

## 3. Validación aplicada

| Control | Resultado |
|---|---|
| **V1 · identidad aritmética** — TGF = 5 × Σ(ASFR por grupo quinquenal) del propio WPP | 160/160 series-año dentro de tolerancia (desvío máximo 0,0117 hijos) |
| **V2 · fuente espejo** — API del Banco Mundial `SP.DYN.TFRT.IN`, mismo país-año | 155/160 coinciden a ≤0,01; los 5 restantes son el agregado regional 2020-2024 (desvío 0,010-0,013), declarados |
| **V3 · fuente nacional 2024** | Brasil (nacidos vivos IBGE, −5,9 % vs WPP) · Argentina (TBN DEIS 8,9 ‰, −19,7 %) · Paraguay (TGF INE 1,946, −19,4 %) · Chile (TGF INE 1,03, −9,6 %) · México (nacimientos INEGI 1.672.227, −17,4 %). **Los cinco quedan por debajo del WPP.** |
| **V4 · exactitud del derivado** — cohortes calculadas con ASFR de grupo quinquenal vs edad simple | desvío medio 0,005 · máximo 0,020 (Paraguay, cohorte 1973) · sin cambios de orden |

Los cinco contrastes nacionales apuntan en la misma dirección: **el WPP sobreestima el nivel de 2024**.
La serie del WPP se mantiene porque es la única comparable entre países; el sesgo se declara en el pie
de cada figura.

## 4. Decisiones de arquitectura

### D3.js en HTML autónomo, con los datos en CSV aparte

- El gráfico **no lleva los datos adentro**: los lee de `datos/*.csv` con `d3.csv()`. Así el CSV es la
  única fuente de verdad y el hash del pie corresponde a un archivo que existe y se puede verificar.
- Cada HTML incluye un bloque `META` con el `sha256` del CSV que consume. `02_sellar_figuras.py` lo
  inscribe y `verificar_manifiesto.py` comprueba que siga coincidiendo. Si el dato cambia y la figura
  no se vuelve a sellar, **la CI falla**.
- Sin build step ni dependencias locales más allá de D3 por CDN: se abre con un servidor estático
  cualquiera (o GitHub Pages) y el archivo se puede citar por URL.

### ¿Quarto? No para las figuras; sí —más adelante— para el documento narrativo

| Necesidad | Herramienta | Por qué |
|---|---|---|
| Figuras interactivas (tooltip, cambio de ventana) | **HTML + D3** | Quarto no aporta nada acá: el gráfico es JavaScript igual, y Quarto agrega una cadena de build (Pandoc, knitr/Jupyter) que hay que mantener |
| Datos y su procedencia | **CSV + manifiesto + scripts** | Verificable con `sha256sum`, sin depender de ningún runtime |
| Control de integridad | **GitHub Actions** | Corre en cada push, no depende de que alguien se acuerde |
| Informe largo, PDF o Word, con texto y tablas | **Quarto** (capa futura) | Ahí sí gana: un `.qmd` por módulo puede embeber las mismas figuras y exportar a PDF/DOCX con numeración y referencias cruzadas |

**Recomendación:** quedarse en HTML + CSV mientras el producto sea un repositorio de figuras. Si más
adelante hace falta un *paper* por módulo o un libro (`quarto book`), Quarto entra **como capa de
publicación que consume los mismos CSV**, no como reemplazo del pipeline. Meterlo ahora duplica la
infraestructura sin resolver nada que el HTML estático no resuelva.

### Animación: dos implementaciones, un dato

| Formato | Archivo | Cuándo usarlo |
|---|---|---|
| **D3 interactivo** | `figuras/tfr-animacion.html` | Reproduce/pausa, barra de arrastre, `?anio=1990` para fijar un año. Todo en el navegador, sin assets |
| **GIF** | `figuras/tfr-animacion.gif` | Se incrusta en README, presentaciones o redes. 75 cuadros, 869×495 px, 1,7 MB, 5,2 s |

El GIF lo genera `03_animacion.py` con matplotlib + Pillow: un cuadro por año, panel de valores a la
derecha y barra de progreso. **No es un video exportado del HTML** —son dos renderizadores distintos
sobre el mismo CSV— y por eso ambos llevan el mismo hash. Regenerar el GIF **cambia su propio hash**,
así que el script actualiza su fila en `manifiesto.csv` antes de que corra el verificador.

Detalles de implementación que importan:

- El GIF se cuantiza a 128 colores con dithering desactivado: con dithering, las líneas finas se
  llenan de ruido y el archivo pesa el doble.
- Se agregan 12 cuadros duplicados al final: sin esa pausa, el último año se pierde al reiniciar el loop.
- La página D3 respeta `prefers-reduced-motion`: quien tenga esa preferencia activada ve directamente
  el estado final en lugar de la animación.

### Paleta

Ocho series no pueden codificarse solo con color: medido con el verificador de la bóveda, el set elegido
da ΔL\* 1,48 y deuteranopía 24,7 contra umbrales de 5 y 45. Por eso cada serie lleva además **trazo
propio** y **rótulo directo** al final de la línea. El color acompaña; no es el canal que decide.

## 5. Límites declarados

- **2024 es estimación del modelo**, no registro. Donde hay registro oficial (cinco países) el valor
  observado es menor que el estimado.
- **Paraguay**: la serie del INE discrepa del WPP en 0,47 hijos (19,4 %) en 2024. Este módulo usa el
  WPP por comparabilidad regional; el dato nacional está documentado en el contraste V3.
- **Sin microdatos**: no se usaron registros individuales; todas las series son agregadas.
- **Colombia** no tiene contraste nacional 2024 en este módulo: el portal del DANE rechaza la conexión
  programática y los conjuntos abiertos disponibles son muestras parciales.
