"""
Dashboard Streamlit — Chat con el agente geoespacial "datahub_bruto".

Pregúntale al agente sobre las zonas, productos y su linaje. Todo respaldado por
la memoria en DataHub (operaciones GIS + linaje de productos) para que no alucine.

Ejecutar:
  streamlit run dashboard/app.py     # -> http://localhost:8501
"""
from __future__ import annotations

import sys
from pathlib import Path

# Asegurar que la carpeta que contiene el paquete 'datahub_bruto' esté en path
_RUTA_ENV = Path(__file__).resolve().parents[2]
if str(_RUTA_ENV) not in sys.path:
    sys.path.insert(0, str(_RUTA_ENV))

import requests  # noqa: E402
import streamlit as st  # noqa: E402

from datahub_bruto.agent.orquestador import consultar, _leer_manifest  # noqa: E402
from datahub_bruto.geo.catalogo_operaciones import CATALOGO  # noqa: E402
from datahub_bruto.zonas.zonas import todas_las_zonas  # noqa: E402
from datahub_bruto.config import cargar_config  # noqa: E402

# ---------------------------------------------------------------------------
# Config / estado
# ---------------------------------------------------------------------------
st.set_page_config(page_title="datahub_bruto · Agente geoespacial",
                   page_icon="🛰️", layout="wide")

_CFG = cargar_config()
_GMS = _CFG.get("datahub", {}).get("gms_url", "http://localhost:8080").rstrip("/")


@st.cache_resource
def _gms_arriba() -> bool:
    try:
        return requests.get(f"{_GMS}/health", timeout=4).status_code == 200
    except Exception:  # noqa: BLE001
        return False


def _estilo():
    st.markdown("""
    <style>
      .bloque { border:1px solid #d0d7de; border-radius:12px; padding:16px;
                background:#ffffff; margin-bottom:10px; }
      .zona-tag { display:inline-block; background:#eef1f6; border-radius:8px;
                  padding:2px 8px; margin:2px; font-size:13px; }
      .chip-ok { background:#d9f7e9; color:#0b7a3b; border-radius:10px;
                 padding:2px 10px; font-size:13px; }
      .chip-err { background:#fde8e8; color:#b01515; border-radius:10px;
                  padding:2px 10px; font-size:13px; }
      .urln { font-family:monospace; font-size:12px; color:#57606a; }
      .upstream { color:#1f6feb; font-family:monospace; font-size:12px; }
    </style>
    """, unsafe_allow_html=True)


_estilo()

# ---------------------------------------------------------------------------
# Sidebar — memoria
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("🛰️ datahub_bruto")
    arriba = _gms_arriba()
    st.markdown("**DataHub (GMS):** "
                + (f"<span class='chip-ok'>● en línea</span>" if arriba
                   else f"<span class='chip-err'>○ local (fallback)</span>"),
                unsafe_allow_html=True)

    st.subheader("🗺️ Zonas")
    zonas = todas_las_zonas()
    st.caption("Haz clic en el nombre para preguntarle al agente")
    for z in zonas:
        if st.button(z.nombre, key=f"zona_{z.id}", use_container_width=True):
            st.session_state["mensaje"] = f"dame el resumen de {z.id}"

    st.subheader("🧠 Memoria en DataHub")
    st.markdown(f"**{len(CATALOGO)} operaciones GIS** listas para la IA.")
    st.markdown(f"**{len(_leer_manifest())} productos** con linaje.")

    st.divider()
    st.caption("Preguntas de ejemplo:")
    for ej in ["¿qué zonas hay?",
               "dame el ndvi de la zona alfa",
               "humedad de selva delta",
               "linaje de producto_ndvi_interpolado_zona_alfa",
               "temperatura de costa epsilon"]:
        if st.button(ej, key=f"ej_{ej}", use_container_width=True):
            st.session_state["mensaje"] = ej
# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
st.title("Agente geoespacial con memoria en DataHub")
st.caption("Pregúntale sobre las 5 zonas ficticias y su linaje. "
           "El agente responde usando los productos catalogados.")


def _render_productos(productos):
    if not productos:
        st.info("Sin productos en esta categoría.")
        return
    st.markdown("##### 📦 Productos")
    for p in productos:
        up = p.get("upstream", [])
        with st.expander(p["nombre"], expanded=bool(up)):
            st.markdown(f"<div class='urln'>{p.get('urn','')}</div>",
                        unsafe_allow_html=True)
            st.markdown(f"*{p.get('descripcion','')}*")
            if up:
                st.markdown("**Linaje (de qué vino):**")
                for u in up:
                    st.markdown(f"<div class='upstream'>↑ {u}</div>",
                                unsafe_allow_html=True)


def _render_respuesta(res: dict):
    tipo = res.get("tipo")
    if tipo == "lista_zonas":
        st.markdown("**Zonas disponibles:**")
        for z in res["zonas"]:
            st.markdown(f"<span class='zona-tag'>{z['id']}</span> "
                        f"**{z['nombre']}** — bbox {z['bbox']}",
                        unsafe_allow_html=True)
    elif tipo == "error":
        st.error(res.get("mensaje", "No entendí."))
    elif tipo in ("resumen_zona", "producto"):
        st.markdown(f"### 🗺️ {res.get('nombre_zona')} "
                    f"<span class='zona-tag'>{res.get('zona')}</span>",
                    unsafe_allow_html=True)
        st.markdown(res.get("rango", ""))
        st.caption(f"Total productos de la zona: {res.get('total_productos_zona')}")
        _render_productos(res.get("productos", []))
    else:
        st.write(res)


chat = st.session_state.setdefault("chat", [])


def _procesar(pregunta: str) -> None:
    chat.append({"role": "user", "texto": pregunta})
    chat.append({"role": "assistant", "texto": consultar(pregunta),
                 "consulta": pregunta})


if "mensaje" in st.session_state:
    preg = st.session_state.pop("mensaje")
    _procesar(preg)
    st.rerun()

# Mostrar conversación
for msg in chat:
    with st.chat_message(msg["role"]):
        if msg["role"] == "user":
            st.markdown(f"**{msg['texto']}**")
        else:
            if isinstance(msg["texto"], dict):
                _render_respuesta(msg["texto"])
            else:
                st.write(msg["texto"])

# Entrada
pregunta = st.chat_input("Pregúntale al agente… "
                         "(ej: 'dame el ndvi de la zona alfa')")
if pregunta:
    _procesar(pregunta)
    st.rerun()

if not chat:
    st.info("👋 Escribe abajo o usa un ejemplo de la barra lateral. "
            "Puedo mostrarte zonas, productos y su linaje.")