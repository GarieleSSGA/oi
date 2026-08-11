"""
Orquestador de consultas: responde a peticiones sobre cada zona usando los
productos generados y el linaje catalogado en DataHub.

Interpreta consultas como:
  - "dame el NDVI de la zona alfa"
  - "estado de la vegetación en selva delta"
  - "lluvia interpolada de costa epsilon"
  - "que zonas hay?"
  - "linaje de producto_ndvi_interpolado_zona_alfa"

Devuelve un resumen estructurado con los productos y (si DataHub está arriba)
el linaje consultado.
"""
from __future__ import annotations

import sys
import json
from pathlib import Path

_RUTA_ENTORNO = Path(__file__).resolve().parents[2]
if str(_RUTA_ENTORNO) not in sys.path:
    sys.path.insert(0, str(_RUTA_ENTORNO))
RUTA_RAIZ = Path(__file__).resolve().parents[1]

from datahub_bruto.zonas.zonas import todas_las_zonas, get_zona, ZONAS  # noqa: E402
from datahub_bruto.datahub_write.catalogar import Catalogador  # noqa: E402

# Mapa de sinónimos de índices -> tipo real
SINONIMOS = {
    "ndvi": ["ndvi", "vegetacion", "verdor", "cobertura"],
    "ndwi": ["ndwi", "agua"],
    "humedad": ["humedad", "humedad suelo", "suelo"],
    "lluvia": ["lluvia", "precipitacion", "pluviometria"],
    "dem": ["dem", "elevacion", "altitud"],
    "lst": ["lst", "temperatura", "calor"],
}


def _normalizar(texto: str) -> str:
    return texto.lower().strip().replace("á", "a").replace("é", "e") \
        .replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ñ", "n")


def _buscar_zona(texto: str):
    """Devuelve la zona mencionada en el texto o None."""
    t = _normalizar(texto)
    for z in todas_las_zonas():
        # buscar por id ("zona_alfa") o por id sin guión ("zona alfa")
        id_sin_guion = z.id.replace("_", " ")
        if z.id in t or id_sin_guion in t or _normalizar(z.nombre) in t:
            return z
    return None


def _buscar_tipo(texto: str):
    """Devuelve el tipo de índice mencionado (ndvi, lluvia...) o None."""
    t = _normalizar(texto)
    for tipo, sinonimos in SINONIMOS.items():
        for s in sinonimos:
            if _normalizar(s) in t:
                return tipo
    return None


def _leer_manifest() -> list:
    """Lee el manifest local (fallback de linaje si DataHub apagado)."""
    ruta = RUTA_RAIZ / "data" / "manifest_completo.json"
    if not ruta.exists():
        return []
    with open(ruta, "r", encoding="utf-8") as f:
        return json.load(f)


def consultar(consulta: str) -> dict:
    """
    Procesa una consulta y devuelve un resumen de la zona/producto pedido.
    """
    consulta = consulta.strip()

    # --- ayuda: listar zonas ---
    if any(k in _normalizar(consulta) for k in ["que zonas", "listar zonas",
                                                 "zonas hay", "lista zonas"]):
        return {"tipo": "lista_zonas",
                "zonas": [{"id": z.id, "nombre": z.nombre,
                           "bbox": z.bbox} for z in todas_las_zonas()]}

    # --- buscar zona y tipo ---
    zona = _buscar_zona(consulta)
    tipo = _buscar_tipo(consulta)

    if zona is None:
        return {"tipo": "error",
                "mensaje": "No reconozco la zona. Usa: " +
                           ", ".join(z.id for z in todas_las_zonas())}

    # cargar manifest para mostrar linaje
    manifest = _leer_manifest()
    productos_zona = [p for p in manifest if zona.id in p["nombre"]]

    # si piden un tipo específico, filtrar
    filtrados = productos_zona
    if tipo:
        filtrados = [p for p in productos_zona if tipo in p["nombre"]]

    return {
        "tipo": "producto" if tipo else "resumen_zona",
        "zona": zona.id,
        "nombre_zona": zona.nombre,
        "bbox": zona.bbox,
        "tipo": tipo,
        "productos": filtrados,
        "total_productos_zona": len(productos_zona),
        "rango": "Selecciona un tipo para ver detalle" if not tipo else
                 f"Productos {tipo.upper()} de {zona.nombre}",
    }


def mostrar_linaje(nombre_producto: str) -> dict:
    """Consulta el linaje de un producto por nombre en el manifest."""
    manifest = _leer_manifest()
    for p in manifest:
        if p["nombre"] == nombre_producto:
            return {"producto": p["nombre"], "urn": p["urn"],
                    "upstream": p.get("upstream", []),
                    "ruta": p.get("ruta_archivo", "")}
    return {"error": f"Producto '{nombre_producto}' no encontrado en manifest"}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Orquestador de consultas")
    parser.add_argument("consulta", nargs="?", default="dame el ndvi de la zona alfa",
                        help="Consulta sobre una zona/producto")
    parser.add_argument("--linaje", help="Nombre de producto para ver linaje")
    args = parser.parse_args()

    if args.linaje:
        print(json.dumps(mostrar_linaje(args.linaje), indent=2, ensure_ascii=False))
    else:
        res = consultar(args.consulta)
        print(json.dumps(res, indent=2, ensure_ascii=False))
        # si es resumen de zona, mostrar linaje de productos clave
        if res.get("tipo") == "resumen_zona":
            print("\n--- Linaje de productos de la zona ---")
            for p in res["productos"]:
                print(f"  {p['nombre']}  <-  upstream={p.get('upstream')}")