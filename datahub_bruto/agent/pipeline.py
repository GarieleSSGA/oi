"""
Pipeline principal: genera todos los productos geoespaciales para las 5 zonas
y los cataloga en DataHub con su linaje.

Flujo por cada zona:
1. Genera rasters crudos (NDVI, NDWI, humedad, lluvia, DEM, LST) -> "fuente"
2. Genera puntos tipo openMateo/estación y los interpola         -> "proceso"
3. Aplica buffer espacial                                          -> "proceso"
4. Calcula estadísticas y clasificación                           -> "producto"
5. Cataloga todo en DataHub con upstreamLineage (si GMS disponible)
   o en un manifest local (fallback).

El resultado es un grafo de linaje ordenado: producto -> proceso -> fuente.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Asegurar que la carpeta que contiene el paquete 'datahub_bruto' esté en el
# path. pipeline.py -> datahub_bruto/agent/ -> parents[2] = HackSocial 2026.
_RUTA_ENTORNO = Path(__file__).resolve().parents[2]
if str(_RUTA_ENTORNO) not in sys.path:
    sys.path.insert(0, str(_RUTA_ENTORNO))

# Raíz del paquete (datahub_bruto/) para las rutas de datos
RUTA_RAIZ = Path(__file__).resolve().parents[1]

from datahub_bruto.config import cargar_config  # noqa: E402
from datahub_bruto.zonas.zonas import todas_las_zonas, Zona  # noqa: E402
from datahub_bruto.geo.sinteticos import generar_raster, guardar_geotiff  # noqa: E402
from datahub_bruto.geo import analisis  # noqa: E402
from datahub_bruto.datahub_write.catalogar import Catalogador  # noqa: E402

# Tipos de raster crudo que generamos (todos los que pidió el usuario)
TIPOS_RASTER = ["ndvi", "ndwi", "humedad", "lluvia", "dem", "lst"]


def generar_productos_zona(zona: Zona, dir_salida: Path,
                           shape=(48, 48), seed: int = 42) -> dict:
    """
    Genera rasters crudos para una zona y los guarda como GeoTIFF.
    Devuelve dict {tipo: {ruta, urn_base}}.
    """
    dir_salida = Path(dir_salida)
    dir_salida.mkdir(parents=True, exist_ok=True)
    rasters = {}
    for tipo in TIPOS_RASTER:
        arr = generar_raster(tipo, zona.perfil, shape=shape,
                             seed=seed + len(tipo))
        ruta = dir_salida / f"{tipo}_{zona.id}.tif"
        guardar_geotiff(arr, ruta, zona.bbox)
        rasters[tipo] = {"ruta": str(ruta), "arr": arr}
    return rasters


def analizar_zona(zona: Zona, rasters: dict, config: dict) -> dict:
    """
    Ejecuta operaciones de análisis sobre los rasters de una zona:
    buffer, interpolación de puntos, estadísticas, clasificación.
    Devuelve dict de productos de análisis.
    """
    umbral_ndvi = config["alertas"]["umbral_ndvi"]
    radios = config["buffer"]["radios_km"]
    productos = {}

    # 1) buffer espacial sobre el bbox
    buffers = {}
    for r in radios:
        buffers[r] = analisis.buffer_bbox(zona.bbox, r)
    productos["buffers_km"] = buffers

    # 2) interpolación de puntos (simula openMateo/estaciones) -> NDVI interpolado
    coords, vals = analisis.puntos_aleatorios(zona.bbox, 60, seed=99,
                                              vmin=0.0, vmax=0.9)
    ndvi_interp = analisis.interpolar_idw(coords, vals, zona.bbox,
                                          shape=rasters["ndvi"]["arr"].shape)
    productos["ndvi_interpolado"] = ndvi_interp

    # 3) interpolación de lluvia (estaciones pluviométricas)
    coords_l, vals_l = analisis.puntos_aleatorios(zona.bbox, 40, seed=101,
                                                  vmin=0, vmax=120)
    lluvia_interp = analisis.interpolar_idw(coords_l, vals_l, zona.bbox,
                                            shape=rasters["lluvia"]["arr"].shape)
    productos["lluvia_interpolada"] = lluvia_interp

    # 4) estadísticas y clasificación del NDVI crudo
    productos["stats_ndvi"] = analisis.estadisticas(
        rasters["ndvi"]["arr"], vmin=umbral_ndvi)
    productos["clasificacion_ndvi"] = analisis.clasificar_ndvi(
        rasters["ndvi"]["arr"])

    # 5) estadísticas de los demás índices
    for tipo in ["lluvia", "humedad", "dem", "lst", "ndwi"]:
        productos[f"stats_{tipo}"] = analisis.estadisticas(rasters[tipo]["arr"])

    return productos


def procesar_todas(catalogo=True, shape=(48, 48), seed=42) -> dict:
    """
    Ejecuta el pipeline completo para las 5 zonas y cataloga en DataHub.
    Devuelve resumen de productos generados.
    """
    config = cargar_config()
    dir_datos = RUTA_RAIZ / "data"
    dir_sinteticos = dir_datos / "sinteticos"
    dir_productos = dir_datos / "productos"

    cat = Catalogador(config) if catalogo else None
    resumen = {"zonas": [], "total_productos": 0}

    for zona in todas_las_zonas():
        # --- paso 1: rasters crudos ---
        rasters = generar_productos_zona(zona, dir_sinteticos,
                                         shape=shape, seed=seed)
        urns_fuente = {}
        for tipo, info in rasters.items():
            urn = None
            if cat:
                urn = cat.catalogar(
                    f"raster_{tipo}_{zona.id}",
                    f"Raster crudo {tipo.upper()} de {zona.nombre}",
                    ruta_archivo=info["ruta"],
                    etiquetas={"tipo": tipo, "zona": zona.id, "origen": "sintetico"},
                )
            urns_fuente[tipo] = urn

        # --- paso 2: productos de análisis ---
        productos = analizar_zona(zona, rasters, config)

        # guardar productos interpolados como GeoTIFF y catalogar con linaje
        for nombre, arr in [
            ("ndvi_interpolado", productos["ndvi_interpolado"]),
            ("lluvia_interpolada", productos["lluvia_interpolada"]),
        ]:
            ruta = dir_productos / f"{nombre}_{zona.id}.tif"
            guardar_geotiff(arr, ruta, zona.bbox)
            if cat:
                cat.catalogar(
                    f"producto_{nombre}_{zona.id}",
                    f"{nombre} de {zona.nombre} (interpolado)",
                    upstream_urns=[urns_fuente["ndvi"], urns_fuente["lluvia"]]
                    if urns_fuente["ndvi"] else None,
                    ruta_archivo=str(ruta),
                    etiquetas={"tipo": "interpolado", "zona": zona.id},
                )

        # --- paso 3: resumen de zona ---
        resumen["zonas"].append({
            "zona": zona.id,
            "nombre": zona.nombre,
            "rasters": list(rasters.keys()),
            "stats_ndvi": productos["stats_ndvi"],
            "clasificacion_ndvi": productos["clasificacion_ndvi"],
            "buffers_km": productos["buffers_km"],
        })
        resumen["total_productos"] += len(rasters) + 2

    # guardar manifest local (siempre, para trazabilidad/fallback)
    if cat:
        manifest_ruta = dir_datos / "manifest_completo.json"
        cat.guardar_manifest(manifest_ruta)
        resumen["manifest"] = str(manifest_ruta)

    return resumen


if __name__ == "__main__":
    resumen = procesar_todas(catalogo=True, shape=(48, 48))
    print("\n=== RESUMEN PIPELINE ===")
    print(f"Zonas procesadas: {len(resumen['zonas'])}")
    print(f"Total productos catalogados: {resumen['total_productos']}")
    for z in resumen["zonas"]:
        print(f"\n[{z['zona']}] {z['nombre']}")
        print(f"  rasters: {z['rasters']}")
        print(f"  NDVI media={z['stats_ndvi']['media']:.3f} "
              f"bajo_umbral={z['stats_ndvi'].get('pct_bajo_umbral', 0):.1f}%")
        print(f"  clasificación: {z['clasificacion_ndvi']}")
        print(f"  buffers_km: {list(z['buffers_km'].keys())}")
    if resumen.get("manifest"):
        print(f"\nManifest: {resumen['manifest']}")