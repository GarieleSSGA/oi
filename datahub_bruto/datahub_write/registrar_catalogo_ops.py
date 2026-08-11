"""
Registra el catálogo de operaciones GIS en DataHub como datasets descubribles.

Cada operación (de geo/catalogo_operaciones.py) se registra como un dataset en
la plataforma `geoBrutoOps`, con sus propiedades (categoría, descripción,
entradas, salidas, ejemplo). Así la IA (local o API) consulta DataHub para saber
qué operaciones existen y cómo usarlas → ejecución precisa con casi 0 errores.

Usa el mismo mecanismo robusto que catalogar.py: `DatahubRestEmitter.emit_mce`
(snapshot MCE). Backend dual:
- Si GMS responde → registra en DataHub.
- Si no → guarda data/manifest_operaciones.json (fallback). Nunca se rompe.
"""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Asegurar que la carpeta que contiene el paquete 'datahub_bruto' esté en path
_RUTA_ENV = Path(__file__).resolve().parents[2]
if str(_RUTA_ENV) not in sys.path:
    sys.path.insert(0, str(_RUTA_ENV))

from datahub.emitter.mce_builder import make_dataset_urn  # noqa: E402

from datahub_bruto.config import cargar_config  # noqa: E402
from datahub_bruto.geo.catalogo_operaciones import CATALOGO  # noqa: E402

_PLATAFORMA = "geoBrutoOps"
_ACTOR = "urn:li:corpuser:datahub-bruto"


def _timestamp() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def _mce_operacion(op: dict, platform: str):
    """Construye el MCE (snapshot) para una operación; devuelve (urn, mce)."""
    from datahub.metadata.schema_classes import (
        DatasetPropertiesClass, DatasetSnapshotClass,
        MetadataChangeEventClass)

    urn = make_dataset_urn(platform, op["id"], "PROD")
    props = DatasetPropertiesClass(
        name=op["id"],
        qualifiedName=urn,
        description=f"[{op['cat']}] {op['nom']} — {op['desc']}",
        customProperties={
            "categoria": op["cat"],
            "nombre": op["nom"],
            "descripcion": op["desc"],
            "entradas": op["inp"],
            "salidas": op["out"],
            "ejemplo": op["ej"],
            "proyecto": "datahub_bruto",
            "tipo": "OPERACION_GIS",
        },
    )
    snapshot = DatasetSnapshotClass(urn=urn, aspects=[props])
    return urn, MetadataChangeEventClass(proposedSnapshot=snapshot)


def registrar(guardar_manifest: bool = True) -> list:
    cfg = cargar_config()
    dh = cfg.get("datahub", {})
    gms_url = dh.get("gms_url", "http://localhost:8080").rstrip("/")
    token = dh.get("token", "")
    activado = dh.get("activado", True)

    emitter = None
    if activado:
        try:
            from datahub.emitter.rest_emitter import DatahubRestEmitter
            emitter = DatahubRestEmitter(gms_server=gms_url, token=token)
            emitter.test_connection()  # lanza excepción si no hay GMS
        except Exception:  # noqa: BLE001
            emitter = None

    manifest = []
    ok_total = 0
    for op in CATALOGO:
        urn, mce = _mce_operacion(op, _PLATAFORMA)
        ok = False
        if emitter is not None:
            try:
                emitter.emit_mce(mce)
                ok = True
                ok_total += 1
            except Exception:  # noqa: BLE001
                ok = False
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
    from collections import Counter
    c = Counter(x["cat"] for x in lista)
    for k, v in sorted(c.items()):
        print(f"  {k:14s}: {v}")