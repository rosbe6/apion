# Apion Reestructurado v3 — Esquema del Proyecto

## 📋 Descripción General

Bot de Telegram (`@apion_bot`) que automatiza procesos de **generación de cookies**, **validación de tarjetas** (BIN checking, VBV), y **gating** (simulación de flujos de compra en sitios de e-commerce y servicios).

**Arquitectura:**
- Core: Telegram bot + gestor de comandos
- Backends: Gates (flujos de pago/registro), APIs externas, engines (BIN, etc)
- Datos: SQLite database, créditos por usuario
- Workers: Colas asíncronas para procesamiento paralelo

---

## 📁 Estructura del Proyecto

```
apion reestrucutrado v3/
├── main.py                    # Punto de entrada del bot
├── config.py                  # Variables globales (tokens, keys, URLs)
├── database.py                # SQLite: usuarios, créditos, logs
├── utils.py                   # Utilidades generales
├── paises.py                  # Metadata de países
│
├── handlers/                  # Handlers de Telegram (comandos + callbacks)
│   ├── admin.py              # /editgate, /genkey, /setrank, /broadcast, etc
│   ├── user.py               # /start, /me, /redeem, /precios
│   ├── gates.py              # Comandos principales: /b3, /dressage, /clover, /neonet, etc
│   ├── callbacks.py          # Callbacks de botones (menús interactivos)
│   ├── card_tools.py         # /bin, /vbv, /extra (validación de tarjetas)
│
├── gates/                     # Gates principales (flujos de pago en sitios)
│   ├── b3m.py                # Braintree (rwcpulse.com) - ACTIVO
│   ├── clover.py             # Clover payment processor
│   ├── dressage.py           # Gate genérico (flujo de checkout)
│   ├── neonet.py             # Neo commerce
│   ├── payflow1.py           # PayFlow processor
│   ├── vbv.py                # Verified by Visa simulation
│   ├── wrenchmonkey.py       # Auto parts ecommerce
│
├── gatestest/                # Gates en desarrollo/testing
│   ├── strip.py              # Stripe gate (cooksmarts.com) - NUEVO
│   ├── oja.py                # Stripe (pencilboxsolutions.org)
│   ├── b3.py                 # Braintree test
│   ├── b3ccn.py              # Braintree CCN test
│
├── amz/                       # Generación de cookies Amazon (APIs)
│   ├── amz_us.py             # Amazon USA (sin Playwright)
│   ├── amz_mx.py             # Amazon México
│   ├── amz_ca.py             # Amazon Canadá
│   ├── awf.py                # WAF handling + CAPTCHA solver
│   ├── datos.py              # Generador de datos fake (nombres, direcciones)
│
├── amzmanual/                # Generación de cookies Amazon (manual con DrissionPage)
│   ├── amzmanualusa.py       # USA - usa navegador Chromium + OTP interactivo
│   ├── amzmanualmx.py        # México
│   ├── amzmanualca.py        # Canadá
│
├── apis_ext/                 # Integraciones con APIs externas
│   ├── pp.py                 # PayPal (genera cookies, simula compra)
│   ├── promerica.py          # Promerica Bank (validación de tarjetas)
│   ├── calarstarbucks.py     # Starbucks (si existe)
│
├── engines/                  # Herramientas especializadas
│   ├── bins_engine.py        # Motor BIN: chequea bins, valida formato
│   ├── amzcode.py            # Amazon codes
│   ├── amzcodeus.py          # Amazon codes USA
│   ├── amzcodemx.py          # Amazon codes México
│
├── plugins/                  # Funcionalidades extra
│   ├── gen.py                # /gen command (generador de datos)
│
└── HAR files (análisis)
    ├── striper.har           # Captura: registro en cooksmarts.com
    ├── striper2.har          # Captura: pago en cooksmarts.com
```

---

## 🔧 Módulos Principales

### **main.py** — Núcleo del Bot
- Inicializa `ApplicationBuilder` de telegram.ext
- Registra handlers por categoría (admin, user, gates, callbacks, card tools)
- Lanza **10 workers asíncronos** para colas de Promerica (`worker_bot`)
- Loop infinito de polling Telegram

**Comandos raíz:**
```
/start          → Menú principal (user)
/me             → Info del usuario + créditos (user)
/redeem         → Canjear keys (user)
/precios        → Ver precios de gates (user)

/b3             → Braintree (Ravenwood) (gates)
/dressage       → Dressage payment (gates)
/clover         → Clover processor (gates)
/neonet         → Neo commerce (gates)
/genman*        → Generar cookie Amazon manual (gates)
/gt             → Cola de Promerica (gates)

/bin            → Chequear BIN (card_tools)
/vbv            → VBV check (card_tools)
/extra          → Extra card tools (card_tools)

/editgate       → Admin: activar/desactivar gates (admin)
/genkey         → Admin: generar keys (admin)
/setrank        → Admin: cambiar rank usuario (admin)
/broadcast      → Admin: enviar mensaje a todos (admin)
```

---

### **config.py** — Variables Globales

```python
TELEGRAM_TOKEN          # Token del bot
DATABASE_PATH           # Ruta SQLite
CAPSOLVER_KEY           # API Capsolver (reCAPTCHA solver)
STRIPE_PK               # Stripe public key
```

### **database.py** — SQLite

**Tablas:**
- `users` — id, telegram_id, rank, creditos, premium
- `keys` — key, rank, usado_por, usado_en
- `logs` — comando, usuario, resultado, timestamp

**Funciones:**
- `tengo_creditos(user_id)` — Checkea si usuario tiene créditos
- `usar_creditoman(user_id)` — Decrementa 0.25 CRD
- `check_antispam(user_id, owner_id, admins)` — Rate limit
- `add_user()`, `add_key()`, `update_rank()`, etc.

---

## 🚀 Gates Principales

### **b3m.py** — Braintree (rwcpulse.com)
**Flujo:**
1. GET página de registro → extrae `authenticity_token` + `csrf_token`
2. Resuelve reCAPTCHA v3 (Capsolver)
3. POST `/subscribe` con datos usuario + captcha
4. Genera token Braintree → POST GraphQL para tokenizar tarjeta
5. Completa suscripción

**Status:** ✅ ACTIVO (token dinámico extraído del HTML)

---

### **strip.py** — Stripe (cooksmarts.com)
**Flujo:**
1. GET `/trial_subscription/new` → extrae `authenticity_token` + `csrf_token`
2. Resuelve reCAPTCHA v2 (Capsolver)
3. POST `/trial_subscription` con usuario + captcha → Turbo Stream response
4. GET `/trial_subscription/payment` → nuevo `authenticity_token`
5. POST `api.stripe.com/v1/tokens` → genera `tok_...` con guid/muid/sid
6. POST `/trial_subscription/charge` con stripe_token → redirect `/welcome` (éxito)

**Status:** ⚙️ TESTING (completado, sin validar en servidor real)

---

### **amzmanual/** — Amazon Manual (Chromium + OTP)
**Flujo:**
1. Usuario envía 3 números telefónicos USA (+1XXXXXXXXXX)
2. Abre navegador Chromium → Amazon.com/wallet
3. Intenta cada número, espera error "número ya usado"
4. Completa registro (nombre, password)
5. Resuelve CAPTCHA (Capsolver)
6. Bot espera a que usuario envíe OTP recibido en el teléfono
7. Completa OTP
8. Agrega dirección
9. Extrae cookies finales (at-main, ubid-main, session-id, etc.)

**Status:** ✅ ACTIVO (usa DrissionPage + Chromium local)

---

### **amz/** — Amazon (Solo APIs, sin navegador)
Alternativa a `amzmanual` pero sin interfaz OTP interactiva. Usa requests puro.

---

### **apis_ext/** — APIs Externas

#### **pp.py** — PayPal
- Simula login + checkout
- Captura cookies de sesión
- Genera fake transaction

#### **promerica.py** — Promerica Bank
- Valida tarjetas de crédito
- Procesa pagos (requiere 10 workers en paralelo)
- Cola con timeout

---

## 🎯 Handlers

### **handlers/gates.py** — Orquestación de Comandos

Contiene los handlers principales que enlazan:
- `/b3` → `b31()` (llama `b3m.b3run()`)
- `/dressage` → `dressage_handler()`
- `/clover` → `clovervariable_handler()`
- `/neonet` → `neonet()`
- `/genman*` → `genmanusa()`, `genmanmx()`, `genmanca()`
- `/gt` → Cola Promerica (`gate_promerica()`)

Cada handler:
1. Valida créditos
2. Chequea antispam
3. Ejecuta flujo de gate
4. Reporta resultado al usuario

---

### **handlers/card_tools.py** — Validación de Tarjetas

- `/bin <numero>` — Chequea BIN (banco, país, tipo)
- `/vbv <numero>` — Simula VBV check
- `/extra <numero>` — Herramientas adicionales

---

### **handlers/admin.py** — Comandos Admin

- `/editgate <gate> <on|off>` — Activa/desactiva gate
- `/genkey <rank>` — Genera key de acceso
- `/setrank <user_id> <rank>` — Cambia rank usuario
- `/status_api` — Ver estado de todas las APIs
- `/broadcast <mensaje>` — Enviar a todos los usuarios

---

## 🔌 Dependencias Principales

```
telegram-bot-api          # Telegram
requests / curl_cffi      # HTTP + browser fingerprinting
DrissionPage              # Web automation (Amazon manual)
Faker                     # Generador de datos fake
psutil                    # Monitor de recursos
asyncio                   # Programación asíncrona
sqlite3                   # Base de datos
```

---

## 🚦 Flujo de Operación

```
Usuario envía comando → Handler valida → Chequea créditos/antispam
                                          ↓
                                    Ejecuta gate/API
                                          ↓
                        [API externa] — [reCAPTCHA] — [Proxy]
                                          ↓
                                Extrae datos/cookies
                                          ↓
                            Reporta resultado al usuario
                                          ↓
                            Decrementa crédito (si aplica)
```

---

## 📊 Status de Gates (2026-06-16)

| Gate | Sitio | Status | Notas |
|------|-------|--------|-------|
| b3m | rwcpulse.com | ✅ Activo | Token dinámico |
| strip | cooksmarts.com | ⚙️ Testing | Sin validar real |
| amzmanual | amazon.com | ✅ Activo | Requiere OTP manual |
| clover | — | ✅ Activo | — |
| dressage | — | ✅ Activo | — |
| neonet | — | ✅ Activo | — |
| paypal | paypal.com | ✅ Activo | PP.py |
| promerica | promerica.com | ✅ Activo | 10 workers paralelos |

---

## 🛠️ Setup & Run

**Instalación:**
```bash
pip install -r requirements.txt
python main.py
```

**En RDP (deployment 24/7):**
```bash
# Task Scheduler
pythonw.exe main.py      # Inicia sin ventana
pythonw.exe pp.py        # PayPal worker (background)
pythonw.exe promerica.py # Promerica worker (background)
```

**Auto-update desde GitHub:**
```python
# Script auto_pull.py
while True:
    git pull origin main
    if cambios:
        restart_bots()
    sleep(600)  # 10 min
```

---

## 🔐 Seguridad

- **Tokens:** Guardados en `.env` (no en repo)
- **Keys:** SQLite con encriptación básica
- **Rate limiting:** Antispam por usuario + cooldown
- **Proxy rotation:** Webshare.io (cuando activo)
- **CAPTCHA:** Capsolver API (reCAPTCHA v2/v3)

---

## 📝 Notas Técnicas

- **JWT Braintree:** Antes hardcodeado, ahora dinámico
- **Stripe tokens:** guid/muid/sid generados client-side (UUID + 6 hex)
- **Amazon WAF:** Requiere navegador real (DrissionPage)
- **Turbo Stream:** Rails 7 Hotwire — respuestas HTML fragmentadas
- **reCAPTCHA:** v3 (invisible), v2 (checkbox) — ambas soportadas

---

## 🚀 Next Steps

1. ✅ Validar `strip.py` en servidor real
2. ✅ Encontrar nuevos sitios con "trial + pago"
3. ✅ Implementar auto-update desde GitHub
4. ✅ Migrar a VPS/Docker para 24/7 sin RDP

---

**Última actualización:** 2026-06-16  
**Versión:** 3.0 (Reestructurado)
