#!/usr/bin/env bash
# estado.sh — Estado del stack DataHub en el servidor
echo "=== Contenedores ==="
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
echo ""
echo "=== GMS health ==="
curl -sf http://localhost:8080/health && echo " <- GMS OK" || echo "GMS sin respuesta"
echo ""
echo "=== RAM ==="
free -h
