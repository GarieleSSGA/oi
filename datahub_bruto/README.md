# datahub_bruto — Análisis geoespacial con linaje en DataHub

Potenciación de **DataHub como memoria de un pipeline de análisis bruto**:
se generan rasters sintéticos clasificados (NDVI, NDWI, humedad, lluvia, DEM,
LST), se ejecutan operaciones de análisis (buffer, interpolación) y **cada
producto se cataloga en DataHub con su linaje** (`upstreamLineage`).

Hay **5 zonas ficticias** definidas. Al consultar al agente, devuelve los
productos de cada zona y su linaje.

## 🗂️ Estructura

```
datahub_bruto/
├── config.py               # carga central de config (env > yaml > defaults)
├── config/config.example.yaml
├── zonas/zonas.py          # las 5 zonas ficticias (id, nombre, bbox, perfil)
├── geo/
│   ├── sinteticos.py       # generador de rasters sintéticos (GeoTIFF)
│   └── analisis.py         # stats, buffer, interpolación IDW, tendencia
├── datahub_write/
│   └── catalogar.py        # write-back a DataHub (GMS) con fallback local
├── agent/
│   ├── pipeline.py         # genera productos + cataloga con linaje
│   └── orquestador.py      # responde consultas por zona
├── scripts/
│   └── generar_catalogo.py # punto de entrada: genera todo
├── data/                   # rasters sintéticos, productos, manifest linaje
└── requirements.txt
```

## 🚀 Arranque rápido (PowerShell)

```powershell
# 1) SIEMPRE primero (CA del entorno rota)
Remove-Item Env:CURL_CA_BUNDLE

# 2) Generar el catálogo completo (5 zonas, 40 productos, linaje)
python scripts/generar_catalogo.py

# 3) Consultar por zona (el agente)
python agent/orquestador.py "dame el ndvi de la zona alfa"
python agent/orquestador.py "que zonas hay"
python agent/orquestador.py "lluvia interpolada de costa epsilon"
python agent/orquestador.py --linaje producto_ndvi_interpolado_zona_alfa
```

## 🌐 DataHub

- **Catálogo:** si DataHub (GMS) está arriba, cada producto se registra como
  dataset con su `upstreamLineage`.
- **Fallback:** si DataHub está apagado, se guarda `data/manifest_completo.json`
  con todo el linaje (la demo nunca se rompe).
- **Config:** `config/config.yaml` → `datahub.{gms_url, token, activado}`.

## 🗺️ Las 5 zonas

| id | nombre | NDVI base | perfil |
|----|--------|-----------|--------|
| zona_alfa    | Distrito Alfa      | 0.28 | semiárida costera |
| zona_beta    | Valle Beta         | 0.62 | agrícola de valle (húmeda) |
| zona_gamma   | Altiplano Gamma    | 0.40 | andina alta (fría) |
| zona_delta   | Selva Delta        | 0.78 | amazónica húmeda |
| zona_epsilon | Costa Epsilon      | 0.15 | costera desértica |

## 📦 Dependencias

```
numpy, rasterio, requests, PyYAML
```

Instalar: `pip install -r requirements.txt`

## ⚠️ Notas de entorno (Windows)

- Limpiar `PROJ_LIB`/`GDAL_DATA` antes de usar rasterio (se hace en el código).
- `Remove-Item Env:CURL_CA_BUNDLE` al inicio de cada sesión.
- Si Docker/DataHub no corre, el pipeline funciona igual con fallback local.
## 🧠 IA que no alucina: catálogo de operaciones GIS en DataHub + MCP

El agente (opencode/Ollama/API) puede **descubrir y usar operaciones GIS con
precisión** en vez de improvisar:

- **`geo/catalogo_operaciones.py`** — inventario de **93 operaciones** (lectura,
  estadística, máscaras/cortes, índices, álgebra, transformaciones, morfología,
  interpolación, vectorial, series, calidad, visualización, zonal, clima) con su
  descripción, entradas, salidas y ejemplo.
- **`datahub_write/registrar_catalogo_ops.py`** — registra las 93 operaciones en
  DataHub (plataforma `geoBrutoOps`) como datasets descubribles. Backend dual:
  si GMS está arriba → DataHub real; si no → `data/manifest_operaciones.json`.
- **`agent/mcp_bruto.py`** — servidor MCP que expone a la IA las herramientas:
  `listar_operaciones`, `buscar_operaciones`, `detalle_operacion`,
  `linaje_producto`, `listar_memoria_datahub`.

```bash
# registrar el catálogo en DataHub
python datahub_write/registrar_catalogo_ops.py

# arrancar el MCP (stdio) para que la IA lo consuma
python agent/mcp_bruto.py --transport stdio

# o en HTTP
DATAHUB_GMS_HOST=localhost DATAHUB_GMS_PORT=8080 \
  python agent/mcp_bruto.py --transport http
```

## ☁️ DataHub en Codespaces (sin gastar RAM local)

- Levanta el stack completo con Docker dentro del Codespace:
  `bash deploy/codespaces/levantar_datahub.sh` (GMS en :8080).
- Con GMS arriba, `generar_catalogo.py` y el registrador escriben en el DataHub
  real (`gms_ok: true`).
- Si Docker/GMS no corre → fallback local automatico (la demo nunca se rompe).