"""
Registra el catálogo de operaciones GIS en DataHub como datasets descubribles.

Cada operación (de geo/catalogo_operaciones.py) se registra como un dataset en
la plataforma `geoBrutoOps`, con sus propiedades (categoría, descripción,
entradas, salidas, ejemplo). Así la IA (local o API) consulta DataHub para saber
qué operaciones existen y cómo usarlas → ejecución precisa con casi 0 errores.

Backend dual (igual que el resto del proyecto):
- Si GMS responde → registra en DataHub vía REST /aspects.
- Si no → guarda data/manifest_operaciones.json (fallback). Nunca se rompe.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

# Asegurar que la carpeta que contiene el paquete 'datahub_bruto' esté en path
_RUTA_ENV = Path(__file__).resolve().parents[2]
if str(_RUTA_ENV) not in sys.path:
    sys.path.insert(0, str(_RUTA_ENV))

import requests  # noqa: E402

from datahub_bruto.config import cargar_config  # noqa: E402
from datahub_bruto.geo.catalogo_operaciones import CATALOGO  # noqa: E402

_PLATAFORMA = "geoBrutoOps"
_ENV = "PROD"


def _urn_op(nombre: str) -> str:
    return (f"urn:li:dataset:(urn:li:dataPlatform:{_PLATAFORMA},"
            f"{nombre},{_ENV})")


def _gms_disponible(gms_url: str, token: str) -> bool:
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        r = requests.get(f"{gms_url}/health", headers=headers, timeout=5)
        return r.status_code == 200
    except Exception:  # noqa: BLE001
        return False


def _post_aspect(gms_url: str, token: str, urn: str,
                 aspect: dict) -> bool:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        r = requests.post(
            f"{gms_url}/aspects",
            params={"urn": urn, "aspect": next(iter(aspect))},
            json=next(iter(aspect.values())),
            headers=headers, timeout=30,
        )
        return r.status_code in (200, 201)
    except Exception:  # noqa: BLE001
        return False


def operacion_a_dataset(op: dict) -> tuple[str, dict, dict]:
    """Convierte una op en (urn, datasetProperties, schemaMetadata)."""
    urn = _urn_op(op["id"])
    props = {
        "datasetProperties": {
            "name": op["id"],
            "description": f"[{op['cat']}] {op['nom']} — {op['desc']}",
            "customProperties": {
                "categoria": op["cat"],
                "nombre": op["nom"],
                "descripcion": op["desc"],
                "entradas": op["inp"],
                "salidas": op["out"],
                "ejemplo": op["ej"],
                "proyecto": "datahub_bruto",
                "tipo": "OPERACION_GIS",
            },
        }
    }
    schema = {
        "schemaMetadata": {
            "schemaName": op["id"],
            "platform": f"urn:li:dataPlatform:{_PLATAFORMA}-system",
            "version": 0,
            "created": {"time": int(time.time() * 1000),
                        "actor": "urn:li:corpuser:datahub"},
            "lastModified": {"time": int(time.time() * 1000),
                             "actor": "urn:li:corpuser:datahub"},
            "hash": "",
            "platformSchema": {
                "com.linkedin.schema.JsonSchema": {
                    "document": json.dumps({
                        "nombre": op["nom"],
                        "entradas": op["inp"].split(", "),
                        "salidas": op["out"].split(", "),
                        "ejemplo": op["ej"],
                    })
                }
            },
            "fields": [
                {
                    "fieldPath": "entradas",
                    "type": "STRING",
                    "nativeDataType": "string",
                    "description": op["inp"],
                    "nullable": False,
                },
                {
                    "fieldPath": "salidas",
                    "type": "STRING",
                    "nativeDataType": "string",
                    "description": op["out"],
                    "nullable": True,
                },
            ],
        }
    }
    return urn, props, schema


def registrar(guardar_manifest: bool = True):
    cfg = cargar_config()
    dh = cfg.get("datahub", {})
    gms_url = dh.get("gms_url", "http://localhost:8080").rstrip("/")
    token = dh.get("token", "")
    activado = dh.get("activado", True)

    manifest = []
    ok_total = 0
    for op in CATALOGO:
        urn, props, schema = operacion_a_dataset(op)
        ok = False
        if activado:
            ok = _post_aspect(gms_url, token, urn, props)
            if ok:
                _post_aspect(gms_url, token, urn, schema)
                ok_total += 1
        manifest.append({
            "urn": urn, "id": op["id"], "cat": op["cat"],
            "nombre": op["nom"], "gms_ok": ok,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        })

    if guardar_manifest:
        ruta = Path(__file__).resolve().parents[1] / "data" / \
            "manifest_operaciones.json"
        ruta.parent.mkdir(parents=True, exist_ok=True)
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
        print(f"Manifest: {ruta}")

    print(f"Operaciones en catálogo : {len(CATALOGO)}")
    print(f"Registradas en GMS      : {ok_total}")
    print(f"Fallback local          : {len(CATALOGO) - ok_total}")
    return manifest


if __name__ == "__main__":
    lista = registrar()
    # resumen por categoría
    from collections import Counter
    c = Counter(x["cat"] for x in lista)
    for k, v in sorted(c.items()):
        print(f"  {k:14s}: {v}")
