# 🚀 Despliegue de DataHub en máquina gratis (Oracle Cloud)

Saca DataHub de tu PC (que solo tiene 7.65 GB de RAM) y móntalo en una máquina
gratuita de Oracle Cloud. Tu PC queda libre y sigue corriendo el pipeline igual.

## 🧭 Arquitectura

```
Tu PC (Windows)                        Oracle Cloud (Ubuntu)
─────────────────────                  ─────────────────────
pipeline.py ──► localhost:8080         GMS (DataHub) :8080
   │               ▲  ▲                 frontend      :9002
   │               │  └── túnel SSH  ──►│
   │               │      (solo 8080)   │  mysql / opensearch /
   │               └────────────────────┘  kafka / datahub
```

- **No expones puertos públicos** en Oracle: usamos un **túnel SSH**.
- El código NO cambia: `config.yaml` sigue con `http://localhost:8080`.
- Cuando el túnel está arriba → escribe a DataHub en la nube.
- Cuando no hay túnel → usa el fallback local (`manifest_completo.json`).

## ⚠️ Primero: ARQUITECTURA de la instancia (clave)

El plan **Always Free** de Oracle ofrece 2 opciones:

| Shape | CPU | RAM | ¿DataHub completo? |
|---|---|---|---|
| Ampere A1 (ARM) | 4 OCPU/24 GB | ✅ sí | ⚠️ necesita validar imágenes ARM |
| E2.1.Micro (x86) | 1 OCPU/1 GB | ❌ no alcanza | solo idea mínima |

**Recomendación:** crea la **Ampere A1 (ARM, 24 GB)**. El script `deploy_datahub.sh`
detecta si el quickstart arranca; si una imagen no es ARM, incluimos un modo
"DataHub mínimo" (solo mysql + GMS) como respaldo.

## ✅ Paso 1 — Crear la instancia en Oracle Cloud

1. https://cloud.oracle.com → Región (elige la más cercana, p. ej. Frankfurt).
2. Menú ☰ → **Compute → Instances → Create instance**.
3. **Image:** Ubuntu 22.04 (LTS) — ARM o x86 según tu shape.
4. **Shape:** Ampere A1 (deja 4 OCPU / 24 GB si el límite lo permite, o 2/12).
5. **SSH keys:** sube tu clave pública (si no la tienes, pasos al final).
6. **Boot volume:** 100 GB (Always Free no cobra hasta ese límite).
7. Crea la instancia. Espera a que pase a **Running**.
8. Anota la **IP pública** (ej. `152.67.xx.xx`).

## ✅ Paso 2 — Conectarte por SSH desde tu PC

```powershell
ssh -i C:\ruta\a\tu_clave_privada ubuntu@152.67.xx.xx
```

En Oracle, el usuario por defecto de Ubuntu es `ubuntu`.

## ✅ Paso 3 — Subir y ejecutar los scripts del servidor

Desde tu PC (en la carpeta `deploy/servidor`), copia los scripts al servidor:

```bash
# en el servidor (ya conectado por SSH):
sudo apt-get update && sudo apt-get install -y git
```

```powershell
# desde tu PC, en la carpeta: HackSocial 2026\datahub_bruto\deploy\servidor
scp -i C:\ruta\a\clave preflight.sh deploy_datahub.sh estado.sh detener.sh ubuntu@152.67.xx.xx:/home/ubuntu/
```

Luego en el servidor:

```bash
chmod +x preflight.sh deploy_datahub.sh estado.sh detener.sh
./preflight.sh          # instala Docker + Compose + DataHub CLI (1 sola vez)
./deploy_datahub.sh     # levanta el stack y espera a que GMS responda (~5-10 min)
./estado.sh             # verifica contenedores y health
```

## ✅ Paso 4 — Túnel SSH desde tu PC

En tu PC (PowerShell), abre el túnel hacia el GMS:

```powershell
.\deploy\local\conectar_tunel.ps1 -Ip 152.67.xx.xx -Clave C:\ruta\a\clave
```

Deja esa ventana abierta. Ahora `localhost:8080` de tu PC apunta al GMS de la nube.

## ✅ Paso 5 — Probar y correr el pipeline

```powershell
.\deploy\local\probar_gms.ps1        # ¿GMS responde? (túnel arriba)
python scripts/generar_catalogo.py   # escribe los 40 productos + linaje en la nube
python agent/orquestador.py "que zonas hay"
```

Si quieres también la **UI de DataHub** (login `datahub`/`datahub`), abre el túnel
adicional de la puerta 9002 (ver `conectar_tunel.ps1 -ConUi`) y ve a
`http://localhost:9002`.

## 🛑 Detener / liberar

```powershell
.\deploy\local\cerrar_tunel.ps1          # cierra el túnel en tu PC
# en el servidor:
./detener.sh                             # apaga el stack (vuelve a dejarlo con 0.3 GB)
# (opcional) voy a la consola Oracle → detiene la instancia → costo 0
```

## 🔐 Cómo generar una clave SSH (si no tienes)

```powershell
ssh-keygen -t ed25519 -f C:\Users\user\.ssh\oracle_cloud_4096
# tu clave pública es: C:\Users\user\.ssh\oracle_cloud_4096.pub  (ese contenido se sube a Oracle)
# la privada: C:\Users\user\.ssh\oracle_cloud_4096                (esta se usa con -i)
```

## 📝 Resumen de archivos

| Archivo | Rol |
|---|---|
| `servidor/preflight.sh` | instala Docker, Compose, DataHub CLI (1 vez) |
| `servidor/deploy_datahub.sh` | quickstart + espera de salud + modo mínimo ARM |
| `servidor/estado.sh` / `detener.sh` | verificar / apagar |
| `local/conectar_tunel.ps1` | túnel SSH 8080 (y 9002 opcional) |
| `local/cerrar_tunel.ps1` | cierra el túnel |
| `local/probar_gms.ps1` | health check del GMS a través del túnel |