"""
Definición de las 5 zonas ficticias de análisis.

Cada zona tiene:
- id: identificador estable (para URNs en DataHub)
- nombre: nombre humano
- bbox: [lon_oeste, lat_sur, lon_este, lat_norte] (EPSG:4326)
- perfil: parámetros que modelan sus rasters sintéticos (para que cada zona
          se vea distinta: unas más secas, otras más húmedas, etc.)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class Zona:
    id: str
    nombre: str
    descripcion: str
    bbox: List[float]  # [lon_oeste, lat_sur, lon_este, lat_norte]
    # perfil sintético: valores base de cada índice
    perfil: Dict[str, float] = field(default_factory=dict)


# Las 5 zonas ficticias (nombres inventados, coordenadas imaginarias)
ZONAS: Dict[str, Zona] = {
    "zona_alfa": Zona(
        id="zona_alfa",
        nombre="Distrito Alfa",
        descripcion="Zona semiárida costera ficticia",
        bbox=[-77.5, -12.5, -77.2, -12.2],
        perfil={"ndvi": 0.28, "ndwi": 0.05, "humedad": 25, "lluvia_mm": 12,
                "dem_m": 30, "lst": 34},
    ),
    "zona_beta": Zona(
        id="zona_beta",
        nombre="Valle Beta",
        descripcion="Zona agrícola de valle ficticia (húmeda)",
        bbox=[-76.8, -11.9, -76.5, -11.6],
        perfil={"ndvi": 0.62, "ndwi": 0.12, "humedad": 55, "lluvia_mm": 45,
                "dem_m": 120, "lst": 26},
    ),
    "zona_gamma": Zona(
        id="zona_gamma",
        nombre="Altiplano Gamma",
        descripcion="Zona andina alta ficticia (fría)",
        bbox=[-71.5, -15.5, -71.2, -15.2],
        perfil={"ndvi": 0.40, "ndwi": 0.08, "humedad": 38, "lluvia_mm": 30,
                "dem_m": 3200, "lst": 12},
    ),
    "zona_delta": Zona(
        id="zona_delta",
        nombre="Selva Delta",
        descripcion="Zona amazónica húmeda ficticia",
        bbox=[-75.0, -9.0, -74.7, -8.7],
        perfil={"ndvi": 0.78, "ndwi": 0.18, "humedad": 70, "lluvia_mm": 80,
                "dem_m": 200, "lst": 28},
    ),
    "zona_epsilon": Zona(
        id="zona_epsilon",
        nombre="Costa Epsilon",
        descripcion="Zona costera desértica ficticia",
        bbox=[-78.5, -7.5, -78.2, -7.2],
        perfil={"ndvi": 0.15, "ndwi": 0.02, "humedad": 15, "lluvia_mm": 3,
                "dem_m": 60, "lst": 38},
    ),
}

# Orden por defecto (para determinismo)
ORDEN = ["zona_alfa", "zona_beta", "zona_gamma", "zona_delta", "zona_epsilon"]


def todas_las_zonas() -> List[Zona]:
    """Devuelve las 5 zonas en orden estable."""
    return [ZONAS[zid] for zid in ORDEN]


def get_zona(zid: str) -> Zona:
    """Devuelve una zona por id (o por nombre en minúsculas)."""
    zid = zid.strip().lower()
    if zid in ZONAS:
        return ZONAS[zid]
    # buscar por nombre
    for z in ZONAS.values():
        if z.nombre.lower() == zid or zid in z.nombre.lower():
            return z
    raise KeyError(f"No existe la zona: {zid}. Disponibles: {list(ZONAS)}")


if __name__ == "__main__":
    for z in todas_las_zonas():
        print(f"{z.id:12s} {z.nombre:20s} bbox={z.bbox} ndvi_base={z.perfil['ndvi']}")