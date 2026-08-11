#!/usr/bin/env bash
# levantar_datahub.sh — Levanta el stack DataHub completo en el Codespace
# (o en cualquier máquina con Docker) y espera a que GMS responda en :8080.
#
# Uso:  bash levantar_datahub.sh
set -euo pipefail

# la CLI de datahub puede no estar en PATH
export PATH="$PATH:/usr/local/python/3.12.1/bin:/home/codespace/.local/bin"

echo "=== [1/3] Bajando cualquier quickstart previo ==="
datahub docker quickstart --stop >/dev/null 2>&1 || true

echo "=== [2/3] Levantando DataHub (quickstart) — descarga imágenes la 1ª vez ==="
datahub docker quickstart || echo "  (quickstart devolvió avisos; seguimos)"

echo "=== [3/3] Esperando GMS en http://localhost:8080/health ==="
OK=0
for i in $(seq 1 60); do
  if curl -sf http://localhost:8080/health >/dev/null 2>&1; then OK=1; break; fi
  printf "."
  sleep 10
done
echo ""

if [ "$OK" = "1" ]; then
  echo ">>> GMS OK ✓ — DataHub está arriba."
else
  echo ">>> GMS sin responder. Para diagnóstico:"
  echo "  docker logs \$(docker ps -q | head -1) --tail 50"
fi

echo ""
echo "=== Contenedores ==="
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
