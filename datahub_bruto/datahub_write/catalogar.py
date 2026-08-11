"""
Write-back de productos a DataHub con linaje.

Cada producto (raster crudo, producto de análisis, serie) se cataloga como un
dataset en DataHub con su `upstreamLineage` (de qué datos vino).

Backend dual:
1. **acryl-datahub** (DatahubRestEmitter) — si está instalado. Mismo mecanismo
   robusto que Terra Cognita, con gobernanza (ownership + tags). Es el
   recomendado cuando se corre con el venv de Terra Cognita.
2. **REST GMS + manifest local** — fallback si no está acryl-datahub o si
   DataHub está apagado. La demo nunca se rompe y el linaje queda trazable.

Plataforma por defecto: `geoBruto` (configurable en config.yaml).
"""
from __future__ import annotations

import json
import os
import sys
import time
import uuid
from pathlib import Path

# Asegurar que la carpeta que contiene el paquete 'datahub_bruto' esté en el
# path (para ejecutar como script). parents[2] = HackSocial 2026.
_RUTA_ENV = Path(__file__).resolve().parents[2]
if str(_RUTA_ENV) not in sys.path:
    sys.path.insert(0, str(_RUTA_ENV))

import requests

from datahub_bruto.config import cargar_config

_ENV = "PROD"


# ---------------------------------------------------------------------------
# Detección de backend
# ---------------------------------------------------------------------------
def _disponible_acryl() -> bool:
    """True si el paquete acryl-datahub está instalado en este intérprete."""
    try:
        import datahub  # noqa: F401
        return True
    except Exception:  # noqa: BLE001
        return False


# ---------------------------------------------------------------------------
# Utilidades de URN
# ---------------------------------------------------------------------------
def urn_dataset(plataforma: str, nombre: str) -> str:
    """Construye la URN de un dataset DataHub."""
    return f"urn:li:dataset:(urn:li:dataPlatform:{plataforma},{nombre},{_ENV})"


def urn_flow(plataforma: str, nombre: str) -> str:
    """Construye la URN de un dataFlow (proceso) DataHub."""
    return f"urn:li:dataFlow:({plataforma},{nombre},{_ENV})"


# ---------------------------------------------------------------------------
# Cuerpos de aspecto (aspects) para GMS REST
# ---------------------------------------------------------------------------
def _aspect_dataset_properties(nombre: str, descripcion: str, etiquetas=None) -> dict:
    return {
        "datasetProperties": {
            "customProperties": {
                "proyecto": "datahub_bruto",
                **(etiquetas or {}),
            },
            "name": nombre,
            "description": descripcion,
        }
    }


def _aspect_upstream_lineage(upstream_urns: list) -> dict:
    return {
        "upstreamLineage": {
            "upstreams": [
                {"dataset": urn, "type": "TRANSFORMED"} for urn in upstream_urns
            ]
        }
    }


def _aspect_schema(nombre: str, ruta: str) -> dict:
    """Aspect de schema con un campo que apunta al archivo del producto."""
    return {
        "schemaMetadata": {
            "schemaName": nombre,
            "platform": "urn:li:dataPlatform:geoBruto-system",
            "version": 0,
            "created": {"time": int(time.time() * 1000), "actor": "urn:li:corpuser:datahub"},
            "lastModified": {"time": int(time.time() * 1000), "actor": "urn:li:corpuser:datahub"},
            "hash": "",
            "platformSchema": {"com.linkedin.schema.JsonSchema": {"document": "{}"}},
            "fields": [
                {
                    "fieldPath": "ruta_archivo",
                    "type": {"type": "STRING"},
                    "nativeDataType": "string",
                    "description": f"Ruta del producto: {ruta}",
                }
            ],
        }
    }


# ---------------------------------------------------------------------------
# Cliente con backend dual (acryl-datahub | REST GMS + manifest local)
# ---------------------------------------------------------------------------
class Catalogador:
    """Cataloga productos en DataHub con fallback a manifest local.

    Usa acryl-datahub si está instalado (gobernanza completa: ownership +
    tags), si no cae a REST GMS; y siempre guarda el manifest local para que
    el linaje quede trazable aunque DataHub esté apagado.
    """

    def __init__(self, config: dict | None = None):
        self.config = config or cargar_config()
        dh = self.config.get("datahub", {})
        self.gms_url = dh.get("gms_url", "http://localhost:8080").rstrip("/")
        self.token = dh.get("token", "")
        self.plataforma = dh.get("plataforma", "geoBruto")
        self.activado = bool(dh.get("activado", True))
        self.manifest = []  # registro local de productos catalogados
        self._gms_ok = None  # cache del estado del GMS
        self.backend = "acryl" if _disponible_acryl() else "rest"
        self._emitter = None  # cache del emitter acryl

    # -- helpers ------------------------------------------------------------
    def _gms_disponible(self) -> bool:
        """Comprueba si el GMS responde (con caché)."""
        if self._gms_ok is not None:
            return self._gms_ok
        try:
            r = requests.get(f"{self.gms_url}/health", timeout=5)
            self._gms_ok = r.status_code == 200
        except Exception:  # noqa: BLE001
            self._gms_ok = False
        return self._gms_ok

    def _emitter_acryl(self):
        """Devuelve (y cachea) un DatahubRestEmitter de acryl-datahub."""
        if self._emitter is None:
            from datahub.emitter.rest_emitter import DatahubRestEmitter
            self._emitter = DatahubRestEmitter(gms_server=self.gms_url)
        return self._emitter

    def _aspectos_gobernanza(self, descripcion: str):
        """Ownership (agente) + tag del proyecto, como Terra Cognita."""
        from datetime import datetime, timezone
        from datahub.metadata.schema_classes import (
            AuditStampClass, GlobalTagsClass, OwnerClass, OwnershipClass,
            OwnershipTypeClass, TagAssociationClass)
        timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)
        actor = "urn:li:corpuser:datahub-bruto"
        ownership = OwnershipClass(
            owners=[OwnerClass(owner=actor, type=OwnershipTypeClass.DATAOWNER)],
            lastModified=AuditStampClass(time=timestamp, actor=actor),
        )
        tags = GlobalTagsClass(tags=[TagAssociationClass(tag="urn:li:tag:datahub-bruto")])
        return [ownership, tags]

    # -- operaciones de envío ----------------------------------------------
    def _enviar_acryl(self, urn: str, propiedades: dict,
                      upstream_urns: list | None, ruta: str) -> bool:
        """Emite un MCE con acryl-datahub (props + linaje + gobernanza)."""
        from datahub.metadata.schema_classes import (
            DatasetPropertiesClass, DatasetSnapshotClass, MetadataChangeEventClass,
            UpstreamClass, UpstreamLineageClass)
        aspectos = []
        props_cls = DatasetPropertiesClass(
            name=propiedades["name"],
            qualifiedName=urn,
            description=propiedades["description"],
            customProperties=propiedades.get("custom", {}),
        )
        aspectos.append(props_cls)
        if upstream_urns:
            aspectos.append(UpstreamLineageClass(
                upstreams=[UpstreamClass(dataset=u, type="TRANSFORMED")
                           for u in upstream_urns]))
        aspectos += self._aspectos_gobernanza(propiedades["description"])
        snapshot = DatasetSnapshotClass(urn=urn, aspects=aspectos)
        try:
            self._emitter_acryl().emit_mce(
                MetadataChangeEventClass(proposedSnapshot=snapshot))
            return True
        except Exception:  # noqa: BLE001
            self._gms_ok = False
            return False

    def _post_aspect(self, urn: str, aspect: dict) -> bool:
        """Envía un aspect a la URN vía API GMS REST. Devuelve True si OK."""
        if not self.activado or not self._gms_disponible():
            return False
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        try:
            r = requests.post(
                f"{self.gms_url}/aspects",
                params={"urn": urn, "aspect": next(iter(aspect))},
                json=next(iter(aspect.values())),
                headers=headers,
                timeout=30,
            )
            return r.status_code in (200, 201)
        except Exception:  # noqa: BLE001
            self._gms_ok = False
            return False

    # -- operaciones públicas ------------------------------------------------
    def catalogar(self, nombre: str, descripcion: str,
                  upstream_urns: list | None = None,
                  ruta_archivo: str = "", etiquetas: dict | None = None) -> str:
        """
        Cataloga un producto como dataset. Devuelve la URN.
        Relaciona `upstream_urns` (linaje) si se pasan.
        """
        urn = urn_dataset(self.plataforma, nombre)
        props = {
            "name": nombre,
            "description": descripcion,
            "custom": {"proyecto": "datahub_bruto", **(etiquetas or {})},
        }
        ok = False
        if self.activado and self.backend == "acryl" and self._gms_disponible():
            ok = self._enviar_acryl(urn, props, upstream_urns, ruta_archivo)
        elif self.activado:
            ok = self._post_aspect(urn, _aspect_dataset_properties(
                nombre, descripcion, etiquetas))
            if ruta_archivo:
                self._post_aspect(urn, _aspect_schema(nombre, ruta_archivo))
            if upstream_urns:
                self._post_aspect(urn, _aspect_upstream_lineage(upstream_urns))
        # registrar en manifest local (siempre, para trazabilidad)
        self.manifest.append({
            "urn": urn,
            "nombre": nombre,
            "ruta_archivo": ruta_archivo,
            "upstream": upstream_urns or [],
            "descripcion": descripcion,
            "backend": self.backend,
            "gms_ok": ok,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        })
        return urn

    def guardar_manifest(self, ruta: Path | str) -> Path:
        """Guarda el manifest local de lo catalogado (fallback + trazabilidad)."""
        ruta = Path(ruta) if not isinstance(ruta, Path) else ruta
        ruta.parent.mkdir(parents=True, exist_ok=True)
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(self.manifest, f, ensure_ascii=False, indent=2)
        return ruta


if __name__ == "__main__":
    cat = Catalogador()
    print("Backend:", cat.backend)
    urn = cat.catalogar("ndvi_zona_alfa", "NDVI crudo de la zona Alfa",
                        ruta_archivo="data/sinteticos/ndvi_zona_alfa.tif")
    print("URN:", urn)
    print("GMS disponible:", cat._gms_disponible())
    print("Manifest:", len(cat.manifest), "productos")
    cat.guardar_manifest("data/manifest_demo.json")
    print("Manifest guardado en data/manifest_demo.json")