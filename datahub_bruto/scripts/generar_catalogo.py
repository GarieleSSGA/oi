"""
Script de arranque: genera el catálogo completo de rasters y productos
para las 5 zonas, los cataloga en DataHub (con fallback local) y muestra
un resumen del linaje.

Uso:
  python scripts/generar_catalogo.py            # genera todo
"""
from __future__ import annotations

import sys
from pathlib import Path

_RUTA_ENTORNO = Path(__file__).resolve().parents[2]
if str(_RUTA_ENTORNO) not in sys.path:
    sys.path.insert(0, str(_RUTA_ENTORNO))

from datahub_bruto.agent.pipeline import procesar_todas  # noqa: E402


def main():
    print("Generando catálogo de rasters y productos para las 5 zonas...\n")
    resumen = procesar_todas(catalogo=True, shape=(48, 48))
    print("\n=== RESUMEN FINAL ===")
    print(f"Zonas procesadas  : {len(resumen['zonas'])}")
    print(f"Productos catálogo: {resumen['total_productos']}")
    print(f"Manifest linaje   : {resumen.get('manifest', 'N/A')}")
    print("\nDistribución de NDVI por zona:")
    for z in resumen["zonas"]:
        print(f"  {z['nombre']:18s} NDVI={z['stats_ndvi']['media']:.3f} "
              f"bajo_umbral={z['stats_ndvi'].get('pct_bajo_umbral', 0):.1f}%")
    print("\nListo. Usá el orquestador para consultar:")
    print("  python agent/orquestador.py \"dame el ndvi de la zona alfa\"")


if __name__ == "__main__":
    main()