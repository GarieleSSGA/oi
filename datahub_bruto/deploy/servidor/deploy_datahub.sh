#!/usr/bin/env bash
# deploy_datahub.sh — Arranca el stack DataHub en el servidor y espera a que GMS
# responda. Incluye modo "mínimo" (solo mysql + GMS) si el quickstart ARM falla.
set -uo pipefail

# Tolerancia al fallo
if command -v sudo >/dev/null 2>&1; then D="sudo -E"; else D=""; fi

echo "=== Arquitectura: $(uname -m) ==="
echo "=== Libre actual: $(free -h | awk '/Mem:/{print $2}') ==="

# datahub puede no estar en PATH tras el venv; buscamos alternativas
DATAHUB_BIN="$(command -v datahub || true)"
if [ -z "$DATAHUB_BIN" ] && [ -f /opt/datahub-venv/bin/datahub ]; then
  DATAHUB_BIN=/opt/datahub-venv/bin/datahub
fi

echo "=== [1/3] Quickstart (DataHub completo) ==="
if [ -n "$DATAHUB_BIN" ]; then
  $D "$DATAHUB_BIN" docker quickstart --stop >/dev/null 2>&1 || true
  $D "$DATAHUB_BIN" docker quickstart --quickstart-compose-file >/dev/null 2>&1 || true
fi

# Esperar health del GMS
echo "=== [2/3] Esperando GMS (http://localhost:8080/health) ==="
OK=0
for i in $(seq 1 60); do
  if curl -sf http://localhost:8080/health >/dev/null 2>&1; then OK=1; break; fi
  printf "."
  sleep 10
done
echo ""

if [ "$OK" = "1" ]; then
  echo ">>> GMS RESPONDE ✓ (sta completo arriba)"
  exit 0
fi

echo ""
echo ">>> El quickstart no respondió a tiempo (¿imagen ARM?)."
echo ">>> Se intentará el modo MÍNIMO: solo mysql + GMS."
echo "=== [3/3] Modo mínimo DataHub ==="

# Stop de cualquier intento anterior
$D docker compose -f /tmp/df-compose.yml down >/dev/null 2>&1 || true

cat > /tmp/df-compose.yml <<'YAML'
name: datahub-min
services:
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: datahub
      MYSQL_DATABASE: datahub
      MYSQL_USER: datahub
      MYSQL_PASSWORD: datahub
    command: --character-set-server=utf8mb4 --collation-server=utf8mb4_bin
    ports: ["3306:3306"]
    volumes: ["dh-min-mysql:/var/lib/mysql"]
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-udatahub", "-pdatahub"]
      interval: 10s
      timeout: 5s
      retries: 12
  gms:
    image: acryldata/datahub-gms:latest
    depends_on:
      mysql:
        condition: service_healthy
    environment:
      EBEAN_DATASOURCE_USERNAME: datahub
      EBEAN_DATASOURCE_PASSWORD: datahub
      EBEAN_DATASOURCE_HOST: mysql:3306
      EBEAN_DATASOURCE_URL: "jdbc:mysql://mysql:3306/datahub?verifyServerCertificate=false&useSSL=true&useUnicode=yes&characterEncoding=UTF-8&enabledTLSProtocols=TLSv1.2"
      EBEAN_DATASOURCE_DRIVER: com.mysql.cj.jdbc.Driver
      ENTITY_REGISTRY_CONFIG_PATH: /datahub/datahub-gms/resources/entity-registry.yml
      ELASTICSEARCH_HOST: mysql
      ELASTICSEARCH_PORT: 9200
    ports: ["8080:8080"]
volumes:
  dh-min-mysql: {}
YAML

$D docker compose -f /tmp/df-compose.yml up -d

for i in $(seq 1 60); do
  if curl -sf http://localhost:8080/health >/dev/null 2>&1; then
    echo ">>> GMS (mínimo) RESPONDE ✓"
    echo ">>> PIPELINE NO PROBARÁ la UI web; solo el write-back de linaje vía :8080."
    exit 0
  fi
  printf "."
  sleep 10
done

echo ""
echo ">>> No se pudo levantar GMS. Revisa:"
echo "   docker logs \$(docker ps -q | head -1) --tail 50"
echo "   O elige una instancia x86 con más RAM."
exit 1
