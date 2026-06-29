# 📋 Migración Apion Bot: Windows RDP → Linux VPS

**Fecha:** 2026-06-28  
**Estado:** En progreso - Resolviendo compatibilidad DrissionPage/Chromium  
**VPS IP:** 38.247.141.48

---

## 🎯 Objetivo
Migrar el bot Apion de Windows Server RDP a Linux VPS para funcionamiento 24/7 con auto-reinicio automático via systemd.

---

## ✅ Pasos Completados

### 1. Configuración de Variables de Entorno
- ✅ Creado `.env.template` con todas las credenciales necesarias
- ✅ Implementado `python-dotenv` en `config.py`
- ✅ Eliminadas credenciales hardcodeadas de:
  - `amz/datos.py` (GRIZZLYSMS_API_KEY, CAPSOLVER_API_KEY)
  - `amz/awf.py` (CAPSOLVER_API_KEY)
  - `amz_us.py`, `amz_mx.py`, `amz_ca.py` (CAPSOLVER_API_KEY)
  - `apis_ext/promerica.py` (TOKEN JWT)
  - `apis_ext/pp.py` (PAYPAL_CLIENT_ID)

### 2. Detección Automática de Chromium
- ✅ Creado `browser_utils.py` con función `find_chromium_path()`
- ✅ Detecta Chromium/Chrome automáticamente en Linux, macOS, Windows
- ✅ Rutas actualizadas en:
  - `amz/amz_us.py`
  - `amz/amz_mx.py`
  - `amz/amz_ca.py`
  - `amzmanual/amzmanualusa.py`
  - `amzmanual/amzmanualca.py`
  - `amzmanual/amzmanuelmx.py`

### 3. Configuración de Proxies
- ✅ Reemplazados proxies hardcodeados con variables de entorno
- ✅ Variables: `AMAZON_PROXY`, `PAYPAL_PROXY_URL`

### 4. APIs Externas
- ✅ **promerica.py**: HOST cambió de `127.0.0.1` a `0.0.0.0`
- ✅ **pp.py**: HOST cambió de `127.0.0.1` a `0.0.0.0`
- ✅ Puertos desde `.env`: `PAYPAL_PORT=8000`, `PROMERICA_PORT=5000`

### 5. Estructura de Directorios
- ✅ Carpeta `data/` para archivos persistentes
- ✅ Carpeta `logs/` para logs con rotación automática
- ✅ `database.py` actualizado con rutas relativas

### 6. Servicios Systemd
- ✅ `systemd/apion.service` - Bot principal
- ✅ `systemd/apion-paypal.service` - PayPal API
- ✅ `systemd/apion-promerica.service` - Promerica API
- ✅ `systemd/apion-logs-viewer.service` - Dashboard de logs en vivo

### 7. Herramientas de Deployment
- ✅ `setup.sh` - Instalación automática en VPS
- ✅ `deploy.py` - Deployment automático con git push + SSH
- ✅ `requirements.txt` - Todas las dependencias

### 8. Web Dashboard de Logs
- ✅ `logs_viewer.py` - Flask app con Server-Sent Events (SSE)
- ✅ Dashboard en vivo: `http://38.247.141.48:8080`
- ✅ Tabs para ver logs de: Bot, PayPal API, Promerica API

### 9. Parámetros Headless Mode
- ✅ Agregados `--headless` y `--no-sandbox` a todos los amzmanual:
  - `amzmanualusa.py`
  - `amzmanualca.py`
  - `amzmanuelmx.py`

---

## 🔧 Problemas Encontrados & Soluciones

### Problema 1: Chromium/Chrome en Headless Mode
**Error:** DrissionPage no puede conectarse a Chromium en puerto local  
**Causa:** Snapcraft vs APT, dependencias faltantes, falta de display virtual  
**Solución:**
1. Desinstalar snap: `sudo snap remove chromium --purge`
2. Instalar Google Chrome desde APT
3. Instalar Xvfb para display virtual
4. Actualizar `.env`: `CHROMIUM_PATH=/usr/bin/google-chrome`

### Problema 2: Snap de Chromium Conflictivo
**Error:** `/usr/bin/chromium-browser` apuntaba a snap  
**Solución:** Eliminar snap e instalar versión APT real

### Problema 3: Falta de Utilidades en Systemd
**Error:** `xvfb-run: awk: not found`  
**Solución:** Instalar `gawk` y `util-linux` o usar script bash directo en systemd

### Problema 4: PayPal API - 407 Proxy Auth
**Error:** GUEST_PAYMENT_INTEGRITY_VALIDATION_FAILED  
**Causa Raíz:** Credenciales proxy incorrectas (qaxtdvtr-GT-rotate vs qaxtdvtr-US-rotate)  
**Solución:** Actualizar `.env` con credenciales correctas

---

## 📝 Variables de Entorno Requeridas (.env)

```env
# Telegram
TELEGRAM_TOKEN=8634302949:AAE...

# APIs Externas
CAPSOLVER_API_KEY=CAP-...
GRIZZLYSMS_API_KEY=de98b845...

# Proxies
AMAZON_PROXY=31.56.127.193:7684
PAYPAL_PROXY_URL=http://qaxtdvtr-US-rotate:cpyp473gyvje@p.webshare.io:80

# Promerica
PROMERICA_TOKEN=eyJhbGc...

# PayPal
PAYPAL_CLIENT_ID=Aen29VHH...

# Database
DATABASE_PATH=data/database_apion.json
KEYS_FILE=data/keys.json
GATES_CONFIG_FILE=data/gates_config.json

# Sistema
CHROMIUM_PATH=/usr/bin/google-chrome

# Puertos
PAYPAL_PORT=8000
PROMERICA_PORT=5000

# Environment
ENVIRONMENT=production
```

---

## 🚀 Instalación en VPS

### Automática
```bash
bash setup.sh
```

### Manual
```bash
# 1. Clonar código
git clone https://github.com/rosbe6/apion.git /home/bot/apion
cd /home/bot/apion

# 2. Crear .env
cp .env.template .env
nano .env  # Agregar credenciales reales

# 3. Venv e instalar
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Instalar dependencias del sistema
sudo apt install -y chromium-browser xvfb gawk util-linux

# 5. Crear estructura
mkdir -p data logs

# 6. Instalar servicios
sudo cp systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable apion.service apion-paypal.service apion-promerica.service apion-logs-viewer.service

# 7. Iniciar
sudo systemctl start apion.service apion-paypal.service apion-promerica.service apion-logs-viewer.service

# 8. Verificar
sudo systemctl status apion.service
tail -f logs/bot.log
```

---

## 📊 Estado Actual (2026-06-28)

### ✅ Funcionando
- Bot principal corriendo en VPS
- APIs externas (PayPal, Promerica) activas
- Dashboard de logs en vivo
- Servicios con auto-reinicio systemd
- Telegram bot respondiendo comandos

### ⚠️ En Resolución
- **DrissionPage + Chromium Headless:** Requiere Xvfb para funcionar
- **Gates de Amazon:** Necesitan conexión Chromium exitosa
- **PayPal Gate:** Credenciales proxy actualizadas, testing en progreso

### ❌ No Resuelto
- Validación de PayPal (GUEST_PAYMENT_INTEGRITY_VALIDATION_FAILED) - puede ser IP bloqueada por PayPal

---

## 🔄 Deployment Automático

```bash
# Desde Windows/Local
python deploy.py
# Sigue los pasos interactivos
```

Esto:
1. Hace git add/commit/push localmente
2. SSH a VPS
3. git pull en VPS
4. Reinicia todos los servicios
5. Muestra estado

---

## 📚 Estructura Post-Migración

```
/home/bot/apion/
├── main.py
├── config.py
├── database.py
├── browser_utils.py
├── requirements.txt
├── setup.sh
├── deploy.py
├── logs_viewer.py
├── CLAUDE.md
├── MIGRACION_LINUX.md
├── .env                    # ⚠️ No commitear
├── .env.template           # Sí commitear
├── .gitignore
├── data/
│   ├── keys.json
│   ├── gates_config.json
│   └── database_apion.json
├── logs/
│   ├── bot.log
│   ├── paypal.log
│   ├── promerica.log
│   └── logs_viewer.log
├── venv/
├── systemd/
│   ├── apion.service
│   ├── apion-paypal.service
│   ├── apion-promerica.service
│   └── apion-logs-viewer.service
├── handlers/
├── gates/
├── amz/
├── amzmanual/
├── apis_ext/
├── engines/
├── plugins/
└── data-files/
```

---

## 🐛 Troubleshooting

### Chromium No Inicia
```bash
# Verificar que está instalado
google-chrome --version

# Probar manualmente
sudo -u bot google-chrome --headless --no-sandbox about:blank

# Verificar Xvfb
ps aux | grep Xvfb
```

### Bot No Responde
```bash
# Ver logs
tail -f /home/bot/apion/logs/bot.log

# Ver estado del servicio
sudo systemctl status apion.service

# Reiniciar
sudo systemctl restart apion.service
```

### API No Accesible
```bash
# Verificar puertos
sudo lsof -i :8000  # PayPal
sudo lsof -i :5000  # Promerica

# Ver logs
tail -f /home/bot/apion/logs/paypal.log
tail -f /home/bot/apion/logs/promerica.log
```

---

## 🎓 Lecciones Aprendidas

### Sobre Linux VPS vs Windows Server
1. **Windows es más simple para web scraping** - Chromium/Chrome funciona directamente
2. **Linux requiere más configuración** - Display virtual (Xvfb), permisos, dependencias
3. **Costo:** Linux VPS es más barato (~$5/mes vs $20+/mes Windows)
4. **Alternativa:** Para próximos proyectos, considerar Playwright o Selenium en lugar de DrissionPage

### Cambios Críticos Realizados
1. Variables de entorno para TODO (seguridad + portabilidad)
2. Detección automática de paths (Windows + Linux + macOS)
3. Systemd para auto-reinicio (mejor que RDP manual)
4. Dashboard web para monitoreo (mejor que RDP remote)

---

## 🚀 Próximos Pasos

### Inmediato
- [ ] Verificar que Xvfb funciona con DrissionPage
- [ ] Probar gates de Amazon (/genmanca, /genmanusa, /genmanmx)
- [ ] Resolver error de PayPal si persiste

### Futuro
- [ ] Migrar a Playwright si DrissionPage sigue problemático
- [ ] Agregar monitoreo uptime (UptimeRobot)
- [ ] Backups automáticos de `data/`
- [ ] Logging centralizado (ELK Stack opcional)

---

## 📞 Comandos Útiles Diarios

```bash
# Ver estado
sudo systemctl status apion.service apion-paypal.service apion-promerica.service

# Ver logs en vivo
tail -f /home/bot/apion/logs/bot.log

# Reiniciar todo
sudo systemctl restart apion.service apion-paypal.service apion-promerica.service

# Cambiar .env
sudo nano /home/bot/apion/.env

# Deployar cambios
python deploy.py  # Desde Windows/local
```

---

**Última actualización:** 2026-06-28  
**Versión:** 1.0 (Migración en progreso)
