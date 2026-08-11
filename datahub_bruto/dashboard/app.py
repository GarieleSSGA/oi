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

st.set_page_config(page_title="datahub_bruto - Agente geoespacial", page_icon="sat", layout="wide")

_CFG = cargar_config()
_GMS = _CFG.get("datahub", {}).get("gms_url", "http://localhost:8080").rstrip("/")

st.sidebar.title("datahub_bruto - Agente geoespacial")
manifest = _leer_manifest()
st.sidebar.markdown(f"**{len(CATALOGO)} operaciones GIS** catalogadas")
st.sidebar.markdown(f"**{len(manifest)} productos** con linaje")
st.sidebar.subheader("Zonas")
for z in todas_las_zonas():
    if st.button(z.nombre):
        st.session_state["mensaje"] = f"dame el resumen de {z.id}"

st.title("Agente geoespacial con memoria en DataHub")
st.caption("Haz clic en una zona o escribe en el chat.")

if "mensaje" in st.session_state:
    r = consultar(st.session_state.pop("mensaje"))
    st.write(r)
else:
    st.info("Selecciona una zona en la barra lateral o pregunta algo.")
