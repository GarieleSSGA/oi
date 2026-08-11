"""
Generador de rasters sintéticos (falsos pero realistas) para cada zona.

Genera GeoTIFFs con variación espacial usando funciones periódicas + ruido,
de modo que cada zona se vea distinta según su 'perfil'.

Tipos de raster soportados:
- ndvi      : índice de vegetación (-1 a 1)
- ndwi      : índice de agua (-1 a 1)
- humedad   : humedad de suelo en % (0-100)
- lluvia    : precipitación acumulada en mm
- dem       : elevación en metros
- lst       : temperatura superficial en °C
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np

# Limpiar variables geo heredadas que rompen rasterio (ver skill 08/10)
for var in ("PROJ_LIB", "PROJ_DATA", "GDAL_DATA"):
    os.environ.pop(var, None)

import rasterio  # noqa: E402
from rasterio.transform import from_origin  # noqa: E402

# Rango de valores por tipo de índice (para escalar el ruido/patrón)
_RANGOS = {
    "ndvi": (-0.2, 0.9),
    "ndwi": (-0.3, 0.5),
    "humedad": (0, 100),
    "lluvia": (0, 120),
    "dem": (0, 3500),
    "lst": (-5, 45),
}


def _generar_mosaico(shape, seed: int) -> np.ndarray:
    """Genera un patrón espacial con gradientes + 'manchas' (variación real)."""
    rng = np.random.default_rng(seed)
    ny, nx = shape
    xx = np.linspace(0, 2 * np.pi, nx)
    yy = np.linspace(0, 2 * np.pi, ny)
    X, Y = np.meshgrid(xx, yy)

    # gradiente base en dos frecuencias
    base = (
        np.sin(X * 1.3 + Y * 0.7) * 0.5
        + np.cos(X * 0.4 - Y * 1.1) * 0.3
        + np.sin(X * 2.7 + Y * 2.3) * 0.2
    )
    # manchas aleatorias (para simular zonas homogéneas: cultivos, bosques)
    manchas = np.zeros(shape)
    for _ in range(6):
        cx = rng.integers(0, nx)
        cy = rng.integers(0, ny)
        radio = rng.integers(5, 20)
        yy_, xx_ = np.ogrid[:ny, :nx]
        mask = (xx_ - cx) ** 2 + (yy_ - cy) ** 2 < radio ** 2
        manchas[mask] += rng.uniform(-0.6, 0.6)
    # ruido fino
    ruido = rng.normal(0, 0.6, size=shape)
    return (base + manchas + ruido) / 2.0


def generar_raster(tipo: str, zona_perfil: dict, shape=(64, 64),
                   seed: int = 42, base_valor: float | None = None) -> np.ndarray:
    """
    Genera un raster sintético para un tipo de índice.

    - tipo: 'ndvi' | 'ndwi' | 'humedad' | 'lluvia' | 'dem' | 'lst'
    - zona_perfil: dict con la clave base (p.ej. {'ndvi': 0.28})
    - base_valor: si se pasa, sobreescribe el valor base (útil para series)
    """
    if tipo not in _RANGOS:
        raise ValueError(f"Tipo de raster no soportado: {tipo}. "
                         f"Usa: {list(_RANGOS)}")
    vmin, vmax = _RANGOS[tipo]

    # valor base de la zona (con fallback al centro del rango)
    base = base_valor if base_valor is not None else float(
        zona_perfil.get(tipo, (vmin + vmax) / 2.0))

    mosaico = _generar_mosaico(shape, seed=seed)
    # amplitud proporcional al rango del índice
    amplitud = (vmax - vmin) * 0.15
    raster = base + mosaico * amplitud
    # asegurar rango válido
    return np.clip(raster, vmin, vmax)


def guardar_geotiff(arr: np.ndarray, ruta: Path, bbox: list,
                    crs: str = "EPSG:4326") -> Path:
    """Guarda un ndarray como GeoTIFF con el bbox dado."""
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ny, nx = arr.shape
    lon_oeste, lat_sur, lon_este, lat_norte = bbox
    # resolución en grados
    res_lon = (lon_este - lon_oeste) / nx
    res_lat = (lat_norte - lat_sur) / ny
    transform = from_origin(lon_oeste, lat_norte, res_lon, res_lat)
    with rasterio.open(
        ruta, "w", driver="GTiff", height=ny, width=nx,
        count=1, dtype=arr.dtype, crs=crs, transform=transform,
    ) as dst:
        dst.write(arr.astype(np.float32), 1)
    return ruta


def generar_serie_ndvi(zona_perfil: dict, dias: int, shape=(64, 64),
                       seed: int = 42, declive: float = 0.01) -> list[np.ndarray]:
    """
    Genera una serie temporal de NDVI con declive progresivo (degradación).
    Devuelve lista de rasters, uno por día.
    """
    serie = []
    for d in range(1, dias + 1):
        base = zona_perfil.get("ndvi", 0.4) - declive * d
        arr = generar_raster("ndvi", zona_perfil, shape=shape, seed=seed + d,
                             base_valor=base)
        serie.append(arr)
    return serie


if __name__ == "__main__":
    # demo: generar NDVI para todas las zonas
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from zonas.zonas import todas_las_zonas  # noqa: E402
    for z in todas_las_zonas():
        arr = generar_raster("ndvi", z.perfil, seed=42)
        print(f"{z.id:12s} NDVI media={arr.mean():.3f} min={arr.min():.3f} max={arr.max():.3f}")