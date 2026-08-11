# arranque.ps1 — datahub_bruto
# Genera el catálogo y verifica el estado de DataHub.

# 1) Limpiar CA del entorno (falla HTTPS: GEE, pip, etc.)
Remove-Item Env:CURL_CA_BUNDLE -ErrorAction SilentlyContinue

# 2) Verificar DataHub (GMS)
Write-Host ""
Write-Host "=== Estado de DataHub ===" -ForegroundColor Cyan
try {
    $health = Invoke-RestMethod http://localhost:8080/health -TimeoutSec 5
    Write-Host "  GMS: OK ($($health.Message))" -ForegroundColor Green
} catch {
    Write-Host "  GMS: NO DISPONIBLE (se usará fallback local)" -ForegroundColor Yellow
}

# 3) Generar el catálogo completo
Write-Host ""
Write-Host "=== Generando catálogo (5 zonas) ===" -ForegroundColor Cyan
python scripts/generar_catalogo.py

Write-Host ""
Write-Host "=== Listo! Consultas de ejemplo ===" -ForegroundColor Cyan
Write-Host '  python agent/orquestador.py "que zonas hay"'
Write-Host '  python agent/orquestador.py "dame el ndvi de la zona alfa"'
Write-Host '  python agent/orquestador.py "lluvia interpolada de selva delta"'
Write-Host '  python agent/orquestador.py --linaje producto_lluvia_interpolada_zona_epsilon'