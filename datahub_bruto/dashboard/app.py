"""
Dashboard Streamlit - Chat con el agente geoespacial datahub_bruto.
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import requests
import streamlit as st
from datahub_bruto.agent.orquestador import consultar, _leer_manifest
from datahub_bruto.geo.catalogo_operaciones import CATALOGO
from datahub_bruto.zonas.zonas import todas_las_zonas
from datahub_bruto.config import cargar_config

st.set_page_config(page_title="datahub_bruto", page_icon="sat", layout="wide")

_CFG = cargar_config()
_GMS = _CFG.get("datahub", {}).get("gms_url", "http://localhost:8080").rstrip("/")

@st.cache_resource
def _gms_arriba():
    try:
        return requests.get(f"{_GMS}/health", timeout=4).status_code == 200
    except Exception:
        return False

def _estilo():
    st.markdown("""
    <style>
      .zona-tag { display:inline-block; background:#eef1f6; border-radius:8px;
                  padding:2px 8px; margin:2px; font-size:13px; }
      .chip-ok { background:#d9f7e9; color:#0b7a3b; border-radius:10px;
                 padding:2px 10px; font-size:13px; }
      .chip-err { background:#fde8e8; color:#b01515; border-radius:10px;
                  padding:2px 10px; font-size:13px; }
      .urln { font-family:monospace; font-size:12px; color:#57606a; }
      .upstream { color:#1f6feb; font-family:monospace; font-size:12px; }
    </style>""", unsafe_allow_html=True)

_estilo()

with st.sidebar:
    st.header("datahub_bruto - Agente geoespacial")
    arriba = _gms_arriba()
    st.markdown("**DataHub (GMS):** " +
                ("<span class='chip-ok'>en linea</span>" if arriba
                 else "<span class='chip-err'>local (fallback)</span>"),
                unsafe_allow_html=True)
    st.subheader("Zonas")
    for z in todas_las_zonas():
        if st.button(z.nombre, key=f"zona_{z.id}", use_container_width=True):
            st.session_state["mensaje"] = f"dame el resumen de {z.id}"
    st.subheader("Memoria en DataHub")
    manifest = _leer_manifest()
    st.markdown(f"**{len(CATALOGO)} operaciones GIS** listas para la IA.")
    st.markdown(f"**{len(manifest)} productos** con linaje.")
    st.divider()
    st.caption("Ejemplos:")
    for ej in ["que zonas hay",
               "dame el ndvi de la zona alfa",
               "humedad de selva delta",
               "linaje de producto_ndvi_interpolado_zona_alfa",
               "temperatura de costa epsilon"]:
        if st.button(ej, key=f"ej_{ej}", use_container_width=True):
            st.session_state["mensaje"] = ej

st.title("Agente geoespacial con memoria en DataHub")
st.caption("Pregunta sobre las 5 zonas ficticias y su linaje.")

def _render_productos(productos):
    if not productos:
        st.info("Sin productos en esta categoria.")
        return
    for p in productos:
        up = p.get("upstream", [])
        with st.expander(p["nombre"], expanded=bool(up)):
            st.markdown("<div class='urln'>%s</div>" % p.get("urn", ""), unsafe_allow_html=True)
            st.markdown("*" + p.get("descripcion", "") + "*")
            if up:
                st.markdown("**Linaje:**")
                for u in up:
                    st.markdown("<div class='upstream'> + %s</div>" % u, unsafe_allow_html=True)

def _render_respuesta(res):
    tipo = res.get("tipo")
    if tipo == "lista_zonas":
        st.markdown("**Zonas disponibles:**")
        for z in res["zonas"]:
            st.markdown("<span class='zona-tag'>%s</span> **%s** - bbox %s"
                        % (z["id"], z["nombre"], z["bbox"]), unsafe_allow_html=True)
    elif tipo == "error":
        st.error(res.get("mensaje", "No entendi."))
    elif tipo in ("resumen_zona", "producto"):
        st.markdown("## %s <span class='zona-tag'>%s</span>"
                    % (res.get("nombre_zona"), res.get("zona")), unsafe_allow_html=True)
        st.markdown(res.get("rango", ""))
        st.caption("Productos en la zona: %s" % res.get("total_productos_zona"))
        _render_productos(res.get("productos", []))
    else:
        st.write(res)

chat = st.session_state.setdefault("chat", [])

if "mensaje" in st.session_state:
    preg = st.session_state.pop("mensaje")
    chat.append({"role": "user", "texto": preg})
    chat.append({"role": "assistant", "texto": consultar(preg), "consulta": preg})
    st.rerun()

for msg in chat:
    with st.chat_message(msg["role"]):
        if msg["role"] == "user":
            st.markdown("**" + msg["texto"] + "**")
        else:
            if isinstance(msg["texto"], dict):
                _render_respuesta(msg["texto"])
            else:
                st.write(msg["texto"])

pregunta = st.chat_input("Pregunta... (ej: dame el ndvi de la zona alfa)")
if pregunta:
    chat.append({"role": "user", "texto": pregunta})
    chat.append({"role": "assistant", "texto": consultar(pregunta), "consulta": pregunta})
    st.rerun()

if not chat:
    st.info("Selecciona una zona en la barra lateral o pregunta algo.")
