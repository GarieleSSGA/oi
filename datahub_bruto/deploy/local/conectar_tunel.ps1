# conectar_tunel.ps1 — Abre el túnel SSH hacia el GMS de DataHub en Oracle Cloud.
# Uso:
#   .\deploy\local\conectar_tunel.ps1 -Ip 152.67.xx.xx -Clave C:\ruta\clave
#   .\deploy\local\conectar_tunel.ps1 -Ip 152.67.xx.xx -Clave ... -ConUi   # + UI :9002
#   .\deploy\local\conectar_tunel.ps1 -Ip 152.67.xx.xx -Clave ... -Solo 9002
param(
    [Parameter(Mandatory=$true)][string]$Ip,
    [Parameter(Mandatory=$true)][string]$Clave,
    [switch]$ConUi = $false,
    [int]$Solo = 0  # 0=8080, 9002=solo UI, 1=ambos (usa ConUi)
)

$usuario = "ubuntu"
if (-not $Clave.EndsWith("\")) { }

Write-Host ""
Write-Host "=== Abriendo túnel SSH -> $Ip ===" -ForegroundColor Cyan

if ($Solo -eq 0 -or $Solo -eq 1) {
    Write-Host "  GMS  : http://localhost:8080  (DataHub API)" -ForegroundColor Green
}
if ($Solo -eq 9002 -or $Solo -eq 1) {
    Write-Host "  UI   : http://localhost:9002   (login datahub/datahub)" -ForegroundColor Green
}

if ($Solo -eq 9002) {
    $argsTunel = @("-N", "-L", "9002:localhost:9002", "-i", $Clave, "$usuario@$Ip")
} elseif ($ConUi -or $Solo -eq 1) {
    $argsTunel = @("-N", "-L", "8080:localhost:8080", "-L", "9002:localhost:9002", "-i", $Clave, "$usuario@$Ip")
} else {
    $argsTunel = @("-N", "-L", "8080:localhost:8080", "-i", $Clave, "$usuario@$Ip")
}

ssh @argsTunel
