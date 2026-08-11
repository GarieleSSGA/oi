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