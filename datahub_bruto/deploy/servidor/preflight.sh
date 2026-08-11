#!/usr/bin/env bash
# preflight.sh — Instala Docker + Compose + DataHub CLI en el servidor (1 sola vez)
# Uso:  sudo apt-get update && sudo apt-get install -y git
#       ./preflight.sh
set -euo pipefail

echo "=== [1/4] Instalando dependencias base ==="
sudo apt-get update -y
sudo apt-get install -y ca-certificates curl gnupg lsb-release jq

echo "=== [2/4] Instalando Docker (engine + compose plugin) ==="
if ! command -v docker >/dev/null 2>&1; then
  sudo install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
    sudo tee /etc/apt/sources.list.d/docker.list >/dev/null
  sudo apt-get update -y
  sudo apt-get install -y docker-ce docker-ce-cli containerd.io \
    docker-buildx-plugin docker-compose-plugin
  sudo usermod -aG docker "$USER"
else
  echo "  docker ya estaba instalado."
fi

echo "=== [3/4] Python + pip para DataHub CLI ==="
sudo apt-get install -y python3 python3-pip python3-venv >/dev/null 2>&1 || true

echo "=== [4/4] DataHub CLI (datahub) ==="
if ! command -v datahub >/dev/null 2>&1; then
  python3 -m venv /opt/datahub-venv || true
  # CUIDADO: instalar en relativo si el venv no se crea perfecto.
  sudo -H python3 -m pip install --upgrade pip >/dev/null 2>&1 || true
  sudo -H python3 -m pip install "acryl-datahub[datahub-rest]" >/dev/null 2>&1 && {
    sudo ln -sf "$(which datahub)" /usr/local/bin/datahub || true
  }
fi

echo ""
echo "=== Listo. Reinicia la sesión para usar docker sin sudo (logout/login). ==="
echo "Ejecuta luego:  ./deploy_datahub.sh"
echo "Architectura de la instancia: $(uname -m)"
