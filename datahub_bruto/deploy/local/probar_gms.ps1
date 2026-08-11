# probar_gms.ps1 — Verifica que el GMS responde a través del túnel SSH.
# Uso:  .\deploy\local\probar_gms.ps1
Write-Host "=== Probando GMS en localhost:8080 (túnel) ===" -ForegroundColor Cyan
try {
    $r = Invoke-RestMethod "http://localhost:8080/health" -TimeoutSec 8
    Write-Host "  GMS OK -> $($r | ConvertTo-Json -Compress)" -ForegroundColor Green
} catch {
    Write-Host "  GMS sin respuesta en :8080." -ForegroundColor Yellow
    Write-Host "  ¿Tienes el túnel arriba? ¿Corrió deploy_datahub.sh en el servidor?"
}
