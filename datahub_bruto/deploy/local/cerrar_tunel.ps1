# cerrar_tunel.ps1 — Cierra cualquier túnel SSH de datahub abierto en tu PC.
Write-Host "=== Cerrando túneles SSH (puestos 8080/9002) ===" -ForegroundColor Cyan
Write-Host "Cerrando procesos ssh con -N (túneles)..."
Get-CimInstance Win32_Process -Filter "Name='ssh.exe'" | Where-Object {
    $_.CommandLine -match '-N'
} | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Write-Host "Listo. localhost:8080 ya no apunta a la nube." -ForegroundColor Green
