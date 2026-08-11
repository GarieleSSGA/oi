"""
Carga central de configuración para datahub_bruto.
Prioridad: variables de entorno > config.yaml > defaults.
"""
from __future__ import annotations

import os
from pathlib import Path

import yaml

# RUTA_CONFIG apunta a la raíz del repo (datahub_bruto/)
RUTA_REPO = Path(__file__).resolve().parents[1]
RUTA_CONFIG = RUTA_REPO / "config" / "config.yaml"

# Valores por defecto (si no hay config.yaml o faltan claves)
DEFAULTS: dict = {
    "datahub": {
        "gms_url": "http://localhost:8080",
        "frontend_url": "http://localhost:9002",
        "token": "",
        "plataforma": "geoBruto",
        "activado": True,
    },
    "geo": {"crs": "EPSG:4326", "resolucion_m": 500, "seed": 42},
    "zonas": {"activas": True},
    "alertas": {
        "umbral_ndvi": 0.3,
        "umbral_ndwi": 0.2,
        "umbral_humedad": 30,
        "umbral_lluvia_mm": 50,
    },
    "interpolacion": {"metodo": "idw", "puntos_max": 200},
    "buffer": {"radios_km": [1, 2, 5]},
    "llm": {
        "api_base": "https://api.deepseek.com/v1",
        "api_key": "",
        "model": "deepseek-chat",
        "timeout_s": 60,
        "activado": False,
    },
    "ollama": {
        "model": "gemma3:1b",
        "base_url": "http://localhost:11434",
        "timeout_s": 90,
        "activado": False,
    },
    "opencode": {"comando": "opencode", "activado": False, "timeout_s": 90},
    "dashboard": {"host": "0.0.0.0", "puerto": 8501},
}

# Mapeo de variables de entorno -> clave de config
_ENV_MAP = {
    "DATAHUB_GMS_TOKEN": ("datahub", "token"),
    "DATAHUB_GMS_URL": ("datahub", "gms_url"),
    "DATAHUB_ACTIVADO": ("datahub", "activado"),
    "LLM_API_KEY": ("llm", "api_key"),
    "LLM_API_BASE": ("llm", "api_base"),
    "LLM_API_MODEL": ("llm", "model"),
    "OLLAMA_MODEL": ("ollama", "model"),
    "OPENCODE_ACTIVADO": ("opencode", "activado"),
}


def _merge(base: dict, override: dict) -> dict:
    """Fusión profunda de dicts (override gana)."""
    out = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


def _aplicar_env(config: dict) -> dict:
    """Sobrescribe claves desde variables de entorno si existen."""
    for var, (seccion, clave) in _ENV_MAP.items():
        valor = os.environ.get(var)
        if valor is not None:
            config.setdefault(seccion, {})
            config[seccion][clave] = valor
            # convertir "true"/"false"/número si aplica
            if clave == "activado":
                config[seccion][clave] = valor.lower() in ("1", "true", "yes")
    return config


def cargar_config() -> dict:
    """Carga y devuelve la configuración completa (merged)."""
    config = _merge(DEFAULTS, {})
    if RUTA_CONFIG.exists():
        try:
            with open(RUTA_CONFIG, "r", encoding="utf-8") as f:
                file_cfg = yaml.safe_load(f) or {}
            config = _merge(config, file_cfg)
        except Exception as exc:  # noqa: BLE001
            print(f"[config] aviso: no se pudo leer config.yaml ({exc}); usando defaults")
    return _aplicar_env(config)


if __name__ == "__main__":
    c = cargar_config()
    print("datahub.gms_url   =", c["datahub"]["gms_url"])
    print("datahub.plataforma=", c["datahub"]["plataforma"])
    print("datahub.activado  =", c["datahub"]["activado"])
    print("geo.resolucion_m  =", c["geo"]["resolucion_m"])
    print("geo.seed          =", c["geo"]["seed"])
    print("alertas.umbral_ndvi=", c["alertas"]["umbral_ndvi"])
    print("llm.model         =", c["llm"]["model"])
    print("OK config cargada")