"""
Operaciones de análisis espacial sobre rasters.

Incluye:
- estadísticas de raster (media, % bajo umbral, clasificación)
- buffer espacial (expansión de bbox por radio en km)
- interpolación IDW de puntos → raster (para datos tipo estación/openMateo)
- evaluación de NDVI y tendencia
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np

# Limpiar variables geo heredadas
for var in ("PROJ_LIB", "PROJ_DATA", "GDAL_DATA"):
    os.environ.pop(var, None)


# ---------------------------------------------------------------------------
# Estadísticas
# ---------------------------------------------------------------------------
def estadisticas(arr: np.ndarray, vmin=None, vmax=None) -> dict:
    """Estadísticas básicas de un raster (ignorando NaN)."""
    a = arr[~np.isnan(arr)]
    if a.size == 0:
        return {"media": None, "min": None, "max": None, "std": None,
                "nan_pct": 100.0}
    res = {
        "media": float(np.mean(a)),
        "min": float(np.min(a)),
        "max": float(np.max(a)),
        "std": float(np.std(a)),
        "nan_pct": float(np.isnan(arr).mean() * 100),
    }
    if vmin is not None:
        res["pct_bajo_umbral"] = float(np.mean(a < vmin) * 100)
    if vmax is not None:
        res["pct_alto_umbral"] = float(np.mean(a > vmax) * 100)
    return res


def clasificar_ndvi(arr: np.ndarray) -> dict:
    """Clasifica un raster NDVI en categorías de cobertura."""
    a = arr[~np.isnan(arr)]
    if a.size == 0:
        return {}
    return {
        "agua/bare_<0": float(np.mean(a < 0) * 100),
        "baja_0_03": float(np.mean((a >= 0) & (a < 0.3)) * 100),
        "media_0.3_0.6": float(np.mean((a >= 0.3) & (a < 0.6)) * 100),
        "alta_>0.6": float(np.mean(a >= 0.6) * 100),
    }


# ---------------------------------------------------------------------------
# Buffer espacial (aprox. en grados sobre un bbox)
# ---------------------------------------------------------------------------
def buffer_bbox(bbox: list, radio_km: float) -> list:
    """
    Expande un bbox [lon_oeste, lat_sur, lon_este, lat_norte] por un radio
    en kilómetros (aprox, usando 111 km/grado de lat).
    """
    lon_o, lat_s, lon_e, lat_n = bbox
    dlat = radio_km / 111.0
    # grados de longitud dependen de la latitud media
    lat_med = (lat_s + lat_n) / 2.0
    dlon = dlat / max(np.cos(np.radians(lat_med)), 1e-6)
    return [lon_o - dlon, lat_s - dlat, lon_e + dlon, lat_n + dlat]


# ---------------------------------------------------------------------------
# Interpolación IDW (puntos → raster)
# ---------------------------------------------------------------------------
def interpolar_idw(puntos: list, valores: list, bbox: list, shape=(64, 64),
                   potencia: float = 2.0) -> np.ndarray:
    """
    Interpola valores de puntos (estaciones/openMateo) a un raster regular
    usando Ponderación por Distancia Inversa (IDW).

    - puntos: lista de (lon, lat)
    - valores: lista de valores (mismo orden)
    - bbox: [lon_oeste, lat_sur, lon_este, lat_norte]
    - shape: (ny, nx)
    """
    if len(puntos) < 1:
        raise ValueError("Se necesitan puntos para interpolar")
    lon_o, lat_s, lon_e, lat_n = bbox
    ny, nx = shape
    lon_vals = np.linspace(lon_o, lon_e, nx)
    lat_vals = np.linspace(lat_s, lat_n, ny)
    coords = np.array(puntos, dtype=float)
    vals = np.array(valores, dtype=float)

    out = np.full((ny, nx), np.nan)
    for j in range(ny):
        for i in range(nx):
            # distancias a todos los puntos
            d = np.sqrt((coords[:, 0] - lon_vals[i]) ** 2
                        + (coords[:, 1] - lat_vals[j]) ** 2)
            # evitar divisiones por cero (punto exacto)
            if d.min() < 1e-12:
                out[j, i] = vals[int(np.argmin(d))]
                continue
            w = 1.0 / (d ** potencia)
            out[j, i] = np.sum(w * vals) / np.sum(w)
    return out


def puntos_aleatorios(bbox: list, n: int, seed: int = 7,
                      vmin: float = 0.0, vmax: float = 1.0) -> tuple:
    """
    Genera puntos aleatorios con valores (simula estaciones/openMateo).
    Devuelve (coords, valores).
    """
    rng = np.random.default_rng(seed)
    lon_o, lat_s, lon_e, lat_n = bbox
    xs = rng.uniform(lon_o, lon_e, n)
    ys = rng.uniform(lat_s, lat_n, n)
    coords = list(zip(xs.tolist(), ys.tolist()))
    # valores con gradiente espacial suave
    valores = (np.sin(xs * 3) + np.cos(ys * 2) + 2) / 4.0
    valores = vmin + (vmax - vmin) * valores
    return coords, valores.tolist()


# ---------------------------------------------------------------------------
# Evaluación de tendencia (serie temporal)
# ---------------------------------------------------------------------------
def evaluar_tendencia(serie: list, umbral_ndvi: float = 0.3) -> dict:
    """
    Evalúa una serie de rasters NDVI: % bajo umbral por paso, delta y estado.
    - serie: lista de ndarrays (uno por día)
    """
    if not serie:
        return {"estado": "SIN_DATOS"}
    pct_bajo = [float(np.mean((s[~np.isnan(s)]) < umbral_ndvi) * 100)
                for s in serie]
    deltas = [pct_bajo[i + 1] - pct_bajo[i] for i in range(len(pct_bajo) - 1)]
    delta_total = deltas[-1] if deltas else 0.0
    if delta_total >= 3:
        estado = "ALERTA"
    elif delta_total >= 0.5:
        estado = "OBSERVACION"
    else:
        estado = "OK"
    return {
        "pct_bajo_por_paso": pct_bajo,
        "delta_total_pp": float(delta_total),
        "estado": estado,
    }


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    bbox = [-77.5, -12.5, -77.2, -12.2]
    # demo buffer
    for r in [1, 2, 5]:
        print(f"buffer {r}km: {buffer_bbox(bbox, r)}")
    # demo interpolación
    coords, vals = puntos_aleatorios(bbox, 20, seed=7, vmin=0.1, vmax=0.8)
    raster = interpolar_idw(coords, vals, bbox, shape=(32, 32))
    print(f"interp NDVI media={np.nanmean(raster):.3f}")
    print("estadísticas:", estadisticas(raster))