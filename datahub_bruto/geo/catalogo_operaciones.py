"""
Catálogo de operaciones geoespaciales (rasterio/GIS).

Objetivo: darle a la IA (local o por API) un inventario estructurado de
~100 operaciones que puede aplicar sobre rasters, de modo que las descubra,
entienda sus entradas/salidas y las ejecute con precisión (casi sin errores).

Cada operación: {id, cat, nom, desc, inp, out, ej}
  - id   : identificador único (se registra en DataHub como dataset)
  - cat  : categoría (lectura, estadistica, mascara, indice, transformacion,
           morfologia, algebra, interpola, vector, serie, calidad)
  - desc : qué hace
  - inp  : entradas (nombre: tipo)
  - out  : salidas
  - ej   : ejemplo de uso

Se registra en DataHub mediante datahub_write/registrar_catalogo_ops.py
"""

CATALOGO: list[dict] = []


def _op(id_: str, cat: str, nom: str, desc: str,
        inp: str, out: str, ej: str) -> dict:
    """Construye la entrada de una operación de forma compacta."""
    return {"id": id_, "cat": cat, "nom": nom,
            "desc": desc, "inp": inp, "out": out, "ej": ej}


# ===========================================================================
# 1) LECTURA / ESCRITURA
# ===========================================================================
CATALOGO += [
    _op("op_leer_geotiff", "lectura", "leer_geotiff",
        "Lee un GeoTIFF y devuelve el ndarray (banda 1) + metadatos.",
        "ruta: str", "arr: ndarray, meta: dict", "leer_geotiff('ndvi.tif')"),
    _op("op_escribir_geotiff", "lectura", "escribir_geotiff",
        "Guarda un ndarray como GeoTIFF con bbox y CRS.",
        "arr: ndarray, ruta: str, bbox: list, crs: str",
        "ruta: Path", "escribir_geotiff(arr,'sal.tif',bbox)"),
    _op("op_leer_banda", "lectura", "leer_banda",
        "Lee una banda concreta de un raster multibanda.",
        "ruta: str, banda: int", "arr: ndarray", "leer_banda('rgb.tif',2)"),
    _op("op_metadata_raster", "lectura", "metadata_raster",
        "Devuelve metadatos: shape, crs, transform, dtype, resolucion.",
        "ruta: str", "meta: dict", "metadata_raster('ndvi.tif')"),
    _op("op_listar_capas", "lectura", "listar_capas",
        "Lista las capas/bandas disponibles en un archivo.",
        "ruta: str", "capas: list", "listar_capas('multi.tif')"),
]

# ===========================================================================
# 2) ESTADÍSTICAS
# ===========================================================================
CATALOGO += [
    _op("op_estadisticas", "estadistica", "estadisticas",
        "Media, min, max, std y %NaN de un raster.",
        "arr: ndarray", "dict", "estadisticas(arr)"),
    _op("op_pct_bajo_umbral", "estadistica", "pct_bajo_umbral",
        "% de píxeles bajo un umbral (ej: degradación).",
        "arr: ndarray, vmin: float", "float", "pct_bajo_umbral(arr,0.3)"),
    _op("op_pct_alto_umbral", "estadistica", "pct_alto_umbral",
        "% de píxeles sobre un umbral.",
        "arr: ndarray, vmax: float", "float", "pct_alto_umbral(arr,0.6)"),
    _op("op_histograma", "estadistica", "histograma",
        "Histograma de valores (bins).",
        "arr: ndarray, bins: int", "hist: ndarray, bordes: ndarray",
        "histograma(arr, bins=20)"),
    _op("op_percentil", "estadistica", "percentil",
        "Valor en el percentil p (0-100).",
        "arr: ndarray, p: float", "float", "percentil(arr, 95)"),
    _op("op_stats_por_zona", "estadistica", "stats_por_zona",
        "Estadísticas regionales promediando por zona/máscara.",
        "arr: ndarray, mascara: ndarray, n_zonas: int",
        "tabla: dict", "stats_por_zona(arr, masc, 5)"),
    _op("op_ratio_2bandas", "estadistica", "ratio_2bandas",
        "División pixel a pixel de dos rasters (evita /0).",
        "a: ndarray, b: ndarray", "ndarray", "ratio_2bandas(a,b)"),
]

# ===========================================================================
# 3) MÁSCARAS / TESELAS / CORTES
# ===========================================================================
CATALOGO += [
    _op("op_mascara_umbral", "mascara", "mascara_umbral",
        "Máscara binaria (True/False) donde arr cumple el umbral.",
        "arr: ndarray, operador: str, valor: float", "mask: ndarray bool",
        "mascara_umbral(arr,'<',0.3)"),
    _op("op_recorte_bbox", "mascara", "recorte_bbox",
        "Recorta un raster a un bbox [oeste,sur,este,norte].",
        "arr: ndarray, bbox: list, geo: bbox geo",
        "sub: ndarray", "recorte_bbox(arr, [-77.5,-12.5,-77.2,-12.2])"),
    _op("op_cortar_tile", "mascara", "cortar_tile",
        "Extrae un tile rectangular (fila/col/alt/ancho).",
        "arr: ndarray, fila: int, col: int, alto: int, ancho: int",
        "tile: ndarray", "cortar_tile(arr, 0,0, 32, 32)"),
    _op("op_enmascarar_nan", "mascara", "enmascarar_nan",
        "Convierte valores no válidos (-9999, inf) a NaN.",
        "arr: ndarray, nodata: float", "arr: ndarray",
        "enmascarar_nan(arr, -9999)"),
    _op("op_clasificar", "mascara", "clasificar",
        "Clasifica en rangos y asigna etiquetas (para NDVI).",
        "arr: ndarray, clases: list[umbral]", "arr_clas: ndarray int",
        "clasificar(arr, [0,0.3,0.6])"),
    _op("op_regiones_conectadas", "mascara", "regiones_conectadas",
        "Etiqueta componentes conectadas de una máscara.",
        "mask: ndarray bool", "labels: ndarray int, n: int",
        "regiones_conectadas(mask)"),
]
# ===========================================================================
# 4) ÍNDICES ESPECTRALES
# ===========================================================================
CATALOGO += [
    _op("op_calc_ndvi", "indice", "ndvi",
        "Índice de vegetación (NIR-R)/(NIR+R).",
        "rojo: ndarray, nir: ndarray", "ndvi: ndarray",
        "ndvi(rojo, nir)"),
    _op("op_calc_ndwi", "indice", "ndwi",
        "Índice de agua (G-NIR)/(G+NIR).",
        "verde: ndarray, nir: ndarray", "ndwi: ndarray",
        "ndwi(verde, nir)"),
    _op("op_calc_ndci", "indice", "ndci",
        "Índice de clorofila en agua.",
        "rededge: ndarray, rojo: ndarray", "ndci: ndarray",
        "ndci(rededge, rojo)"),
    _op("op_calc_ndmi", "indice", "ndmi",
        "Índice de humedad (NIR-SWIR)/(NIR+SWIR).",
        "nir: ndarray, swir: ndarray", "ndmi: ndarray",
        "ndmi(nir, swir)"),
    _op("op_calc_nbr", "indice", "nbr",
        "Normalized Burn Ratio (severidad de fuego).",
        "nir: ndarray, swir2: ndarray", "nbr: ndarray", "nbr(nir, swir2)"),
    _op("op_calc_savi", "indice", "savi",
        "SAVI con factor L (suelos).",
        "rojo: ndarray, nir: ndarray, L: float=0.5", "savi: ndarray",
        "savi(rojo, nir, L=0.5)"),
    _op("op_calc_evi", "indice", "evi",
        "Enhanced Vegetation Index.",
        "rojo,nir,azul: ndarray", "evi: ndarray", "evi(rojo,nir,azul)"),
    _op("op_calc_bare_soil", "indice", "bare_soil",
        "Índice de suelo desnudo (BI).",
        "swir,rojo,nir: ndarray", "bi: ndarray",
        "bare_soil(swir,rojo,nir)"),
]

# ===========================================================================
# 5) ÁLGEBRA DE BANDAS
# ===========================================================================
CATALOGO += [
    _op("op_suma_rasters", "algebra", "suma_rasters",
        "Suma pixel a pixel de varios rasters.",
        "rasters: list[ndarray]", "ndarray", "suma_rasters([a,b,c])"),
    _op("op_resta_rasters", "algebra", "resta_rasters",
        "Resta pixel a pixel (a - b).",
        "a: ndarray, b: ndarray", "ndarray", "resta_rasters(a,b)"),
    _op("op_producto_rasters", "algebra", "producto_rasters",
        "Producto pixel a pixel.",
        "a: ndarray, b: ndarray", "ndarray", "producto_rasters(a,b)"),
    _op("op_normalizar", "algebra", "normalizar",
        "Escala a [0,1] (min-max).",
        "arr: ndarray", "ndarray", "normalizar(arr)"),
    _op("op_estandarizar", "algebra", "estandarizar",
        "Estandariza a media 0 / std 1.",
        "arr: ndarray", "ndarray", "estandarizar(arr)"),
    _op("op_log1p", "algebra", "log1p",
        "log(1+arr) para datos asimétricos.",
        "arr: ndarray", "ndarray", "log1p(arr)"),
    _op("op_relu", "algebra", "relu",
        "max(arr, 0).",
        "arr: ndarray", "ndarray", "relu(arr)"),
    _op("op_clip_rango", "algebra", "clip_rango",
        "Recorta valores a [vmin, vmax].",
        "arr: ndarray, vmin: float, vmax: float", "ndarray",
        "clip_rango(arr, 0, 1)"),
]

# ===========================================================================
# 6) TRANSFORMACIONES (reproyectar, remuestrear, geomorph)
# ===========================================================================
CATALOGO += [
    _op("op_reproyectar", "transformacion", "reproyectar",
        "Cambia la proyección/CRS de un raster.",
        "arr: ndarray, crs_origen: str, crs_destino: str",
        "arr_new: ndarray, transform: Affine",
        "reproyectar(arr,'EPSG:4326','EPSG:32718')"),
    _op("op_remuestrear", "transformacion", "remuestrear",
        "Cambia resolución / tamaño de píxel (método).",
        "arr: ndarray, factor: float, metodo: str='bilinear'",
        "ndarray", "remuestrear(arr, factor=0.5)"),
    _op("op_recortar_mascara_shp", "transformacion", "recortar_mascara_shp",
        "Recorta/extrae un raster usando un polígono (shp/geojson).",
        "arr, transform, crs, poligono; ruta: str", "ndarray",
        "recortar_mascara_shp(arr, tf, crs, 'poligono.geojson')"),
    _op("op_mosaicar", "transformacion", "mosaicar",
        "Une varios teselas/raster en uno.",
        "rutas/rasters: list", "ndarray", "mosaicar([a.tif,b.tif])"),
    _op("op_calcular_pendiente", "transformacion", "pendiente",
        "Pendiente en grados desde un DEM.",
        "dem: ndarray, resolucion: float", "ndarray", "pendiente(dem, 30)"),
    _op("op_calcular_aspecto", "transformacion", "aspecto",
        "Orientación de la pendiente (0-360°).",
        "dem: ndarray, resolucion: float", "ndarray", "aspecto(dem, 30)"),
    _op("op_hillshade", "transformacion", "hillshade",
        "Sombreado del relieve (visualización).",
        "dem: ndarray, alt_sol: float, az_sol: float", "ndarray 0-255",
        "hillshade(dem, 45, 315)"),
    _op("op_curvatura", "transformacion", "curvatura",
        "Curvatura del terreno desde un DEM.",
        "dem: ndarray", "ndarray", "curvatura(dem)"),
    _op("op_ruggedness", "transformacion", "ruggedness",
        "Índice de rugosidad del terreno (TRI).",
        "dem: ndarray", "ndarray", "ruggedness(dem)"),
]
# ===========================================================================
# 7) MORFOLOGÍA / SUAVIZADO / FILTRADO
# ===========================================================================
CATALOGO += [
    _op("op_erosion", "morfologia", "erosion",
        "Erosión morfológica de una máscara (reduce).",
        "mask: ndarray bool, size: int", "mask: ndarray",
        "erosion(mask, size=3)"),
    _op("op_dilatacion", "morfologia", "dilatacion",
        "Dilatación morfológica (expande).",
        "mask: ndarray bool, size: int", "mask: ndarray",
        "dilatacion(mask, size=3)"),
    _op("op_apertura", "morfologia", "apertura",
        "Apertura (erosion+dilatacion) para limpiar ruido.",
        "mask: ndarray bool, size: int", "mask: ndarray",
        "apertura(mask, size=3)"),
    _op("op_cierre", "morfologia", "cierre",
        "Cierre (dilatación+erosión) para rellenar huecos.",
        "mask: ndarray bool, size: int", "mask: ndarray",
        "cierre(mask, size=3)"),
    _op("op_suavizar_gauss", "morfologia", "suavizar_gauss",
        "Filtro gaussiano de suavizado (deriva).",
        "arr: ndarray, sigma: float", "ndarray", "suavizar_gauss(arr, 2.0)"),
    _op("op_mediana", "morfologia", "mediana",
        "Filtro de mediana (ruido salt-pepper).",
        "arr: ndarray, size: int", "ndarray", "mediana(arr, size=3)"),
    _op("op_filtro_laplace", "morfologia", "filtro_laplace",
        "Realce de bordes con Laplaciano.",
        "arr: ndarray", "ndarray", "filtro_laplace(arr)"),
    _op("op_deteccion_bordes", "morfologia", "deteccion_bordes",
        "Detección de bordes (gradiente de Sobel).",
        "arr: ndarray", "bordes: ndarray", "deteccion_bordes(arr)"),
]

# ===========================================================================
# 8) INTERPOLACIÓN / RELLENO
# ===========================================================================
CATALOGO += [
    _op("op_interpolar_idw", "interpola", "interpolar_idw",
        "IDW de puntos a raster (estaciones/openMateo).",
        "puntos,valores: list, bbox: list, shape, potencia: float",
        "ndarray", "interpolar_idw(p, v, bbox, shape=(64,64))"),
    _op("op_interpolar_linear", "interpola", "interpolar_linear",
        "Interpolación bilineal (rellena NaN con vecinos).",
        "arr: ndarray", "ndarray", "interpolar_linear(arr)"),
    _op("op_rellenar_nan", "interpola", "rellenar_nan",
        "Rellena NaN con un valor / vecino más cercano.",
        "arr: ndarray, valor: float|None", "ndarray",
        "rellenar_nan(arr, valor=0)"),
    _op("op_kriging_lite", "interpola", "kriging_lite",
        "Interpolación con corrección de media (aproximación).",
        "puntos,valores: list, bbox, shape", "ndarray",
        "kriging_lite(p, v, bbox, (64,64))"),
]

# ===========================================================================
# 9) RASTIZACIÓN / VECTORIAL
# ===========================================================================
CATALOGO += [
    _op("op_rasterizar_poligono", "vector", "rasterizar_poligono",
        "Convierte un polígono a raster (burn).",
        "geo: GeoJSON/GeoSeries, shape, transform", "mask: ndarray",
        "rasterizar_poligono(geo, (64,64), tf)"),
    _op("op_poligonizar_mascara", "vector", "poligonizar_mascara",
        "Convierte máscara a polígonos (vector).",
        "mask: ndarray, transform", "GeoDataFrame", "poligonizar_mascara(m)"),
    _op("op_buffer_bbox", "vector", "buffer_bbox",
        "Expande un bbox por radio en km.",
        "bbox: list, radio_km: float", "bbox: list",
        "buffer_bbox(bbox, 5)"),
    _op("op_buffer_poligono", "vector", "buffer_poligono",
        "Buffer a un polígono (shapely).",
        "poligono, distancia", "poligono", "buffer_poligono(geo, 1000)"),
    _op("op_interseccion_bbox", "vector", "interseccion_bbox",
        "Interseca dos bboxes/polígonos.",
        "a, b", "geom", "interseccion_bbox(a, b)"),
    _op("op_area_poligono", "vector", "area_poligono",
        "Área de un polígono en km².",
        "poligono", "float", "area_poligono(geo)"),
    _op("op_centroide", "vector", "centroide",
        "Centroide de un polígono / zona.",
        "poligono", "punto (lon,lat)", "centroide(geo)"),
]
# ===========================================================================
# 10) SERIE TEMPORAL / CAMBIO
# ===========================================================================
CATALOGO += [
    _op("op_tendencia_serie", "serie", "tendencia_serie",
        "Tendencia lineal sobre serie de rasters.",
        "serie: list[ndarray]", "pendiente, intercept, estado",
        "tendencia_serie(serie)"),
    _op("op_delta_serie", "serie", "delta_serie",
        "Diferencia entre pasos / total.",
        "serie: list, metric: str='media'", "deltas: list, total: float",
        "delta_serie(serie)"),
    _op("op_deteccion_cambio", "serie", "deteccion_cambio",
        "Detecta anomalías/cambios abruptos en la serie.",
        "serie: list", "indices_anomalos: list", "deteccion_cambio(serie)"),
    _op("op_media_movil", "serie", "media_movil",
        "Media móvil para suavizar serie.",
        "serie: list, ventana: int", "ndarray", "media_movil(serie, 7)"),
    _op("op_max_serie", "serie", "max_serie",
        "Máximo por píxel a lo largo de la serie.",
        "serie: list[ndarray]", "ndarray", "max_serie(serie)"),
    _op("op_mean_serie", "serie", "mean_serie",
        "Promedio por píxel de la serie (composite).",
        "serie: list[ndarray]", "ndarray", "mean_serie(serie)"),
]

# ===========================================================================
# 11) CALIDAD / VALIDACIÓN
# ===========================================================================
CATALOGO += [
    _op("op_validar_rango", "calidad", "validar_rango",
        "Verifica que los valores estén dentro de un rango lógico.",
        "arr: ndarray, rango: (min,max)", "ok: bool, %fuera",
        "validar_rango(arr, (-1,1))"),
    _op("op_pct_cobertura", "calidad", "pct_cobertura",
        "% de píxeles válidos (no-NaN).",
        "arr: ndarray", "float 0-100", "pct_cobertura(arr)"),
    _op("op_deteccion_nubes", "calidad", "deteccion_nubes",
        "Máscara de nubes por umbral de brillo/QAPF.",
        "brillo: ndarray, umbral: float", "cloud_mask: ndarray",
        "deteccion_nubes(brillo, 0.35)"),
    _op("op_mse_2rasters", "calidad", "mse_2rasters",
        "Error cuadrático medio entre dos rasters.",
        "a: ndarray, b: ndarray", "float", "mse_2rasters(a, b)"),
    _op("op_rmse_2rasters", "calidad", "rmse_2rasters",
        "Raíz del error cuadrático medio.",
        "a: ndarray, b: ndarray", "float", "rmse_2rasters(a, b)"),
    _op("op_correlacion_2rasters", "calidad", "correlacion_2rasters",
        "Correlación de Pearson entre dos rasters.",
        "a: ndarray, b: ndarray", "float", "correlacion_2rasters(a, b)"),
    _op("op_resumen_estado", "calidad", "resumen_estado",
        "Estado (OK/OBSERVACION/ALERTA) según umbrales.",
        "metricas: dict, umbrales: dict", "estado: str",
        "resumen_estado(m, {'ndvi':0.3})"),
]

# ===========================================================================
# 12) VISUALIZACIÓN / EXPORT
# ===========================================================================
CATALOGO += [
    _op("op_a_rgb", "visualizacion", "a_rgb",
        "Genera vista RGB (normaliza y combina bandas).",
        "bandas: list[ndarray]", "img: ndarray UInt8", "a_rgb([r,g,b])"),
    _op("op_png_export", "visualizacion", "png_export",
        "Exporta un raster como PNG (con colormap).",
        "arr: ndarray, ruta: str, cmap: str='viridis'", "archivo: str",
        "png_export(arr, 'vista.png')"),
    _op("op_folium_tile", "visualizacion", "folium_tile",
        "Overlay de un raster sobre mapa (folium).",
        "arr, bbox, ruta_html: str", "archivo: str",
        "folium_tile(arr, bbox, 'mapa.html')"),
    _op("op_mapa_calor_puntos", "visualizacion", "mapa_calor_puntos",
        "Heatmap de puntos (densidad).",
        "puntos: list, bbox, resolucion", "raster: ndarray",
        "mapa_calor_puntos(p, bbox)"),
]

# ===========================================================================
# 13) ZONAL / AGRUPADO
# ===========================================================================
CATALOGO += [
    _op("op_stats_zona_poligono", "zonal", "stats_zona_poligono",
        "Estadísticas de un raster dentro de un polígono.",
        "arr, transform, poligono", "dict",
        "stats_zona_poligono(arr, tf, pol)"),
    _op("op_extraer_pixeles", "zonal", "extraer_pixeles",
        "Extrae valores del raster en puntos (muestreo).",
        "arr, transform, puntos: list", "valores: list",
        "extraer_pixeles(arr, tf, pts)"),
    _op("op_composite_fechas", "zonal", "composite_fechas",
        "Combina rasters de varias fechas (mediana/media).",
        "serie: list, metodo: str='mediana'", "ndarray",
        "composite_fechas(serie)"),
    _op("op_conteo_pixeles_clase", "zonal", "conteo_pixeles_clase",
        "Conteo de píxeles por clase en un raster clasificado.",
        "arr_clas: ndarray int", "tabla: dict", "conteo_pixeles_clase(c)"),
    _op("op_superficie_clase", "zonal", "superficie_clase",
        "Área en km² por clase (con resolución).",
        "arr_clas, resolucion_m: float", "tabla: dict",
        "superficie_clase(c, 500)"),
]

# ===========================================================================
# 14) MÁS ÍNDICES / CLIMA / FÍSICO
# ===========================================================================
CATALOGO += [
    _op("op_calc_nbr2", "indice", "nbr2",
        "NBR2 (dNBR severidad tras incendio).",
        "swir2: ndarray, swir1: ndarray", "nbr2: ndarray",
        "nbr2(swir2, swir1)"),
    _op("op_calc_mndwi", "indice", "mndwi",
        "MNDWI (agua en zonas urbanas).",
        "verde: ndarray, swir1: ndarray", "mndwi: ndarray",
        "mndwi(verde, swir1)"),
    _op("op_calc_gci", "indice", "gci",
        "Green Chlorophyll Index.",
        "nir: ndarray, verde: ndarray", "gci: ndarray", "gci(nir, verde)"),
    _op("op_calc_msavi", "indice", "msavi",
        "MSAVI2 (suelo desnudo).",
        "nir: ndarray, rojo: ndarray", "msavi: ndarray",
        "msavi(nir, rojo)"),
    _op("op_calc_tci", "indice", "tci",
        "Tasseled Cap wetness (humedad).",
        "azul,verde,rojo,nir,swir1,swir2: ndarray", "tcw: ndarray",
        "tci(b,g,r,n,sw1,sw2)"),
    _op("op_calcular_ndfi", "indice", "ndfi",
        "NDFI (degradación forestal).",
        "nir,swir1,swir2,rojo: ndarray", "ndfi: ndarray",
        "ndfi(nir,sw1,sw2,r)"),
    _op("op_isd_dem", "clima", "sombra_sol",
        "Sombra del sol sobre el terreno (insolación).",
        "dem: ndarray, fecha, hora", "sombra: ndarray 0/1",
        "sombra_sol(dem, '2026-08-11', '12:00')"),
    _op("op_fetch_precip", "clima", "fetch_precip",
        "Descarga de precipitación (openMateo/GEE) → raster.",
        "bbox, fecha_inicio, fecha_fin", "serie_raster",
        "fetch_precip(bbox, '2026-01-01','2026-08-11')"),
    _op("op_fetch_ndvi_satelite", "clima", "fetch_ndvi_satelite",
        "Descarga NDVI real por satélite (GEE).",
        "bbox, fecha, escala_m: int", "ndvi: ndarray",
        "fetch_ndvi_satelite(bbox, '2026-08-01', 500)"),
]

if __name__ == "__main__":
    # diagnóstico rápido
    cats = {}
    for op in CATALOGO:
        cats[op["cat"]] = cats.get(op["cat"], 0) + 1
    print(f"Total operaciones: {len(CATALOGO)}")
    for c, n in sorted(cats.items()):
        print(f"  {c:14s}: {n}")