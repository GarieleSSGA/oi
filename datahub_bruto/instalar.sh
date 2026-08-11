#!/usr/bin/env bash
# instalar.sh — Prepara datahub_bruto en Codespaces en un solo comando.
# Uso:  bash instalar.sh
set -e

cd "$(dirname "$0")"   # situarse en datahub_bruto/

echo "=== [1/3] Instalando dependencias (requirements.txt) ==="
python -m pip install -r requirements.txt

echo "=== [2/3] Creando config/config.yaml desde el ejemplo (si no existe) ==="
if [ ! -f config/config.yaml ]; then
  cp config/config.example.yaml config/config.yaml
  echo "  -> config/config.yaml creado."
else
  echo "  -> config/config.yaml ya existe, se deja igual."
fi

echo ""
echo "=== [3/3] Listo! Ahora corre: ==="
echo "  python scripts/generar_catalogo.py"
echo "  python agent/orquestador.py \"que zonas hay\""
echo "  python agent/orquestador.py \"dame el ndvi de la zona alfa\""
