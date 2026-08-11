#!/usr/bin/env bash
# detener.sh — Apaga el stack DataHub en el servidor (libera RAM).
echo "=== Deteniendo stack DataHub ==="
# Quickstart (datahub)
docker compose -f /tmp/df-compose.yml down 2>/dev/null || true
# Modo mínimo
docker compose -f /tmp/df-compose-min.yml down 2>/dev/null || true
# Quickstart clásico por nombre de proyecto
docker compose -p datahub down 2>/dev/null || true
echo "=== Contenedores restantes ==="
docker ps --format 'table {{.Names}}\t{{.Status}}'
echo ""
echo "Liberado. Para costo 0 adicional puedes detener la instancia desde la consola OCI."
