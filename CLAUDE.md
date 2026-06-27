# Apion Bot - Documentación de Migración a Linux VPS

## 📋 Resumen
Este documento contiene la configuración y guía de migración del bot Apion de Windows RDP a VPS Linux.

## 🔄 Cambios Realizados (Críticos)

### 1. Variables de Entorno (.env)
- ✅ Creado `.env.template` con todas las credenciales
- ✅ Actualizado `config.py` para cargar desde `.env` con `python-dotenv`
- ✅ Eliminadas credenciales hardcodeadas de:
  - `amz/datos.py` (GRIZZLYSMS_API_KEY, CAPSOLVER_API_KEY)
  - `amz/awf.py` (CAPSOLVER_API_KEY)
  - `amz_us.py`, `amz_mx.py`, `amz_ca.py` (CAPSOLVER_API_KEY)
  - `apis_ext/promerica.py` (TOKEN JWT)
  - `apis_ext/pp.py` (PAYPAL_CLIENT_ID)

### 2. Detección Automática de Chromium
- ✅ Creado `browser_utils.py` con función `find_chromium_path()`
- ✅ Detecta automáticamente Chromium en Linux, macOS y Windows
- ✅ Actualizado en:
  - `amz/amz_us.py`
  - `amz/amz_mx.py`
  - `amz/amz_ca.py`
  - `amzmanual/amzmanualusa.py`
  - `amzmanual/amzmanuelmx.py`
  - `amzmanual/amzmanualca.py`

### 3. Configuración de Proxies
- ✅ Reemplazados proxies hardcodeados con variables de entorno
- ✅ Variable: `AMAZON_PROXY` (ej: "31.56.127.193:7684")

### 4. APIs Externas
- ✅ **promerica.py**: HOST cambió de `127.0.0.1` a `0.0.0.0` (acepta conexiones remotas)
- ✅ **pp.py**: HOST cambió de `127.0.0.1` a `0.0.0.0`
- ✅ Puertos desde `.env`: `PAYPAL_PORT=8000`, `PROMERICA_PORT=5000`

### 5. Estructura de Archivos
- ✅ Creada carpeta `data/` para archivos persistentes
- ✅ Creada carpeta `logs/` para logs
- ✅ Actualizado `database.py` para usar rutas relativas

### 6. Dependencies
- ✅ Creado `requirements.txt` con todas las dependencias

### 7. Servicios Systemd
- ✅ `systemd/apion.service` - Bot principal
- ✅ `systemd/apion-paypal.service` - PayPal API
- ✅ `systemd/apion-promerica.service` - Promerica API

### 8. Setup Automático
- ✅ Creado `setup.sh` para instalación en VPS Linux

## 📝 Cómo Usar

### En Windows (Antes de migrar)
1. Asegúrate de que todo funciona localmente
2. Copia tus datos a la VPS

### En VPS Linux

#### Instalación automática (recomendado)
```bash
# Como usuario normal (no root)
bash setup.sh
```

#### O instalación manual

**1. Clonar/copiar código**
```bash
git clone https://github.com/tu_usuario/apion.git /home/bot/apion
cd /home/bot/apion
```

**2. Crear .env**
```bash
cp .env.template .env
nano .env
# Agregar credenciales reales
```

**3. Crear venv e instalar**
```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**4. Instalar servicios**
```bash
sudo cp systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable apion.service apion-paypal.service apion-promerica.service
sudo systemctl start apion.service apion-paypal.service apion-promerica.service
```

**5. Verificar**
```bash
sudo systemctl status apion.service
tail -f logs/bot.log
```

## 🔑 Variables de Entorno (.env)

```env
# Telegram
TELEGRAM_TOKEN=8634302949:AAE...

# APIs
CAPSOLVER_API_KEY=CAP-...
GRIZZLYSMS_API_KEY=de98b845...

# Proxies
AMAZON_PROXY=31.56.127.193:7684
PAYPAL_PROXY_URL=http://p.webshare.io:9999

# Promerica
PROMERICA_TOKEN=eyJhbGciOiJIUzI1NiIs...

# PayPal
PAYPAL_CLIENT_ID=Aen29VHHiwicell...

# Database
DATABASE_PATH=data/database_apion.json
KEYS_FILE=data/keys.json
GATES_CONFIG_FILE=data/gates_config.json

# System
CHROMIUM_PATH=/usr/bin/chromium

# Ports
PAYPAL_PORT=8000
PROMERICA_PORT=5000
```

## 🐛 Troubleshooting

### "Chromium not found"
```bash
sudo apt install chromium-browser -y
```

### "TELEGRAM_TOKEN not configured"
```bash
# Editar .env
nano /home/bot/apion/.env
# Agregar TELEGRAM_TOKEN
```

### "Permission denied"
```bash
sudo chown -R bot:bot /home/bot/apion
```

### Bot no responde
```bash
# Ver logs
journalctl -u apion.service -f

# O desde el archivo
tail -f /home/bot/apion/logs/bot.log
```

### API no accesible
- Verificar que está escuchando en `0.0.0.0`
- Verificar puertos: `sudo lsof -i :5000` y `sudo lsof -i :8000`
- Revisar logs de las APIs en `logs/paypal.log` y `logs/promerica.log`

## 📊 Estructura Post-Migración

```
/home/bot/apion/
├── main.py
├── config.py
├── database.py
├── browser_utils.py
├── requirements.txt
├── setup.sh
├── .env                    # ⚠️ No commitear
├── .gitignore
├── .env.template           # Template para .env
├── data/                   # Archivos persistentes
│   ├── keys.json
│   ├── gates_config.json
│   └── database_apion.json
├── logs/                   # Logs (rotación automática)
│   ├── bot.log
│   ├── paypal.log
│   └── promerica.log
├── venv/                   # Entorno virtual
├── systemd/
│   ├── apion.service
│   ├── apion-paypal.service
│   └── apion-promerica.service
├── handlers/
├── gates/
├── amz/
├── amzmanual/
├── apis_ext/
│   ├── pp.py              # ✅ Actualizado
│   ├── promerica.py       # ✅ Actualizado
│   └── (starbucks eliminado)
├── engines/
├── plugins/
└── data-files/
    ├── bins_all.csv
    ├── database_apion.json
    └── ...
```

## ✅ Checklist Final

- [ ] Crear `.env` con todas las credenciales
- [ ] Instalar Chromium en VPS: `apt install chromium-browser`
- [ ] Probar bot en manual: `python main.py`
- [ ] Instalar servicios systemd
- [ ] Iniciar servicios: `systemctl start apion.service`
- [ ] Verificar logs: `tail -f logs/bot.log`
- [ ] Habilitar autostart: `systemctl enable apion.service`
- [ ] Configurar firewall (si aplica): `ufw allow 22/tcp`
- [ ] Hacer backup de datos antes

## 📞 Comandos Útiles

```bash
# Ver estado de servicios
sudo systemctl status apion.service apion-paypal.service apion-promerica.service

# Reiniciar servicios
sudo systemctl restart apion.service

# Ver logs en tiempo real
tail -f /home/bot/apion/logs/bot.log

# Ver últimas 100 líneas
tail -n 100 /home/bot/apion/logs/bot.log

# Buscar error en logs
grep "ERROR" /home/bot/apion/logs/bot.log

# Ver conexiones de red
sudo lsof -i -P -n | grep LISTEN

# Ver consumo de recursos
htop
```

## 🔐 Seguridad

- ✅ `.env` incluido en `.gitignore`
- ✅ Tokens NO están en código, solo en `.env`
- ✅ Credenciales desde variables de entorno
- ✅ Usuario `bot` sin permisos de sudo innecesarios

## 📈 Monitoreo (Futuro)

Considerar agregar:
- Monitoring con Prometheus + Grafana
- Alertas con uptime checkers
- Backups automáticos de `data/`
- Logs centralizados con ELK Stack

---

**Última actualización**: 2026-06-27  
**Versión**: 1.0 (Migración a Linux completada)
