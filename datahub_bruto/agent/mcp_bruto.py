"""
Servidor MCP (Model Context Protocol) que conecta a la IA con DataHub.

Expone las operaciones GIS y el linaje registrados en DataHub como herramientas,
para que la IA (local opencode/Ollama o por API) las descubra y ejecute con
precisión (casi sin errores), sin alucinar nombres ni argumentos.

Herramientas:
  - buscar_operaciones(texto)     -> ops GIS que coinciden (en DataHub)
  - detalle_operacion(id)         -> entradas/salidas/ejemplo de una op
  - listar_operaciones()          -> inventario completo agrupado
  - linaje_producto(urn|nombre)   -> de dónde vino un producto
  - consultar_consulta(texto)     -> delega a agent/orquestador (plan JSON)

Arranque (HTTP):
  DATAHUB_GMS_HOST=localhost DATAHUB_GMS_PORT=8080 \
    python agent/mcp_bruto.py --transport http
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Asegurar que la carpeta que contiene el paquete 'datahub_bruto' esté en path
_RUTA_ENV = Path(__file__).resolve().parents[2]
if str(_RUTA_ENV) not in sys.path:
    sys.path.insert(0, str(_RUTA_ENV))

from mcp.server.fastmcp import FastMCP  # noqa: E402

from datahub_bruto.config import cargar_config  # noqa: E402
from datahub_bruto.geo.catalogo_operaciones import CATALOGO  # noqa: E402

mcp = FastMCP("datahub-bruto-mcp")

_DH_URL = os.environ.get(
    "DATAHUB_GMS_URL",
    cargar_config().get("datahub", {}).get("gms_url", "http://localhost:8080"),
).rstrip("/")


# ---------------------------------------------------------------------------
# Acceso a DataHub (GMS) via REST /entities?action=ingest | /entities get
# ---------------------------------------------------------------------------
def _gms_get(urn: str, aspect: str = ""):
    import requests
    url = f"{_DH_URL}/entities?ids=List({urn})"
    if aspect:
        url += f"&aspect={aspect}"
    r = requests.get(url, headers={"Accept": "application/json"}, timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f"GMS {r.status_code}")
    return r.json()


def _buscar_gms(texto: str, fila: int = 0, count: int = 50):
    import requests
    headers = {"Content-Type": "application/json", "X-RestLi-Method": "ACTION"}
    body = {"input": texto, "type": "dataset", "start": fila, "count": count}
    r = requests.post(f"{_DH_URL}/entities?action=search", json=body,
                      headers=headers, timeout=30)
    return r.json() if r.status_code == 200 else {}


# ---------------------------------------------------------------------------
# Herramientas (data source: catálogo local + DataHub)
# ---------------------------------------------------------------------------
@mcp.tool()
def listar_operaciones() -> list[dict]:
    """Inventario completo de operaciones GIS disponibles (categoría, id, nombre)."""
    return [{"id": op["id"], "cat": op["cat"], "nombre": op["nom"]}
            for op in CATALOGO]


@mcp.tool()
def buscar_operaciones(texto: str) -> list[dict]:
    """Busca operaciones GIS por texto (nombre, categoría o descripción)."""
    texto = texto.lower()
    return [{"id": op["id"], "categoria": op["cat"], "nombre": op["nom"],
             "descripcion": op["desc"]}
            for op in CATALOGO
            if (texto in op["nom"].lower() or texto in op["cat"].lower()
                or texto in op["desc"].lower())]


@mcp.tool()
def detalle_operacion(id_operacion: str) -> dict | None:
    """Devuelve entradas, salidas y ejemplo de una operación GIS por su id."""
    for op in CATALOGO:
        if op["id"] == id_operacion:
            return {"id": op["id"], "categoria": op["cat"], "nombre": op["nom"],
                    "descripcion": op["desc"], "entradas": op["inp"],
                    "salidas": op["out"], "ejemplo": op["ej"]}
    return None


@mcp.tool()
def linaje_producto(nombre: str) -> list[str]:
    """Devuelve el linaje (de qué vino) de un producto registrado en DataHub."""
    import json
    manifest = Path(__file__).resolve().parents[1] / "data" / "manifest_completo.json"
    if not manifest.exists():
        return ["Sin manifest local; corre primero scripts/generar_catalogo.py"]
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return ["No se pudo leer el manifest"]
    for item in data:
        if nombre in item["nombre"] or nombre in item["urn"]:
            return item.get("upstream", [])
    return ["Producto no encontrado"]


@mcp.tool()
def listar_memoria_datahub() -> dict:
    """Estado de la memoria: cuántas operaciones y cuántos productos hay en DataHub."""
    import json
    ops = len(CATALOGO)
    prods = 0
    manifest = Path(__file__).resolve().parents[1] / "data" / "manifest_completo.json"
    if manifest.exists():
        try:
            prods = len(json.loads(manifest.read_text(encoding="utf-8")))
        except Exception:  # noqa: BLE001
            prods = -1
    return {"operaciones_gis": ops, "productos_en_datahub": prods,
            "gms": _DH_URL}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MCP DataHub bruto")
    parser.add_argument("--transport", default="http",
                        help="stdio | http")
    args = parser.parse_args()

    if args.transport == "http":
        host = os.environ.get("MCP_HOST", "0.0.0.0")
        port = int(os.environ.get("MCP_PORT", "8000"))
        mcp.run(transport="streamable-http", host=host, port=port)
    else:
        mcp.run(transport="stdio")
