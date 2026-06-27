# 📊 Guía de Monitoreo de Logs en VPS

## 🔴 **VER LOGS EN VIVO (La forma más simple)**

### Opción 1: Ver archivo de log en tiempo real
```bash
tail -f /home/bot/apion/logs/bot.log
```

**Resultado en consola:**
```
2026-06-27 10:23:45,123 - root - INFO - 🚀 APION BOT Reestructurado e Iniciado...
2026-06-27 10:23:46,456 - root - INFO - 📝 Logs guardados en: logs/bot.log
2026-06-27 10:24:12,789 - telegram.ext - INFO - Usuario 123456 ejecutó /start
2026-06-27 10:24:35,012 - handlers.gates - ERROR - Error en gate PayPal: Connection timeout
```

### Opción 2: Ver logs del servicio systemd
```bash
# Ver logs en tiempo real
sudo journalctl -u apion.service -f

# Ver últimas 50 líneas
sudo journalctl -u apion.service -n 50

# Ver logs de hoy
sudo journalctl -u apion.service --since today

# Ver logs con timestamps precisos
sudo journalctl -u apion.service -f --output=short-precise
```

---

## 🟡 **DOS TERMINALES SSH (LA FORMA PRÁCTICA)**

Abre **DOS conexiones SSH** simultáneamente:

**Terminal 1 - Monitorear logs:**
```bash
ssh bot@VPS_IP
cd /home/bot/apion
tail -f logs/bot.log
```

**Terminal 2 - Ejecutar comandos:**
```bash
ssh bot@VPS_IP
sudo systemctl restart apion.service
sudo systemctl status apion.service
```

---

## 🟢 **VER LOGS DE LOS TRES SERVICIOS**

### Todo en una terminal
```bash
# Ver logs de bot + PayPal + Promerica simultáneamente
sudo journalctl -u apion.service -u apion-paypal.service -u apion-promerica.service -f
```

### En terminales separadas
```bash
# Terminal 1: Bot
tail -f /home/bot/apion/logs/bot.log

# Terminal 2: PayPal
tail -f /home/bot/apion/logs/paypal.log

# Terminal 3: Promerica
tail -f /home/bot/apion/logs/promerica.log
```

---

## 🔵 **BUSCAR ERRORES EN LOGS**

```bash
# Ver solo errores
grep "ERROR" /home/bot/apion/logs/bot.log

# Ver últimas 20 líneas con errores
grep "ERROR" /home/bot/apion/logs/bot.log | tail -20

# Ver errores en tiempo real
tail -f /home/bot/apion/logs/bot.log | grep "ERROR"

# Ver actividad de un usuario específico
grep "user_id_123" /home/bot/apion/logs/bot.log

# Ver comandos ejecutados
grep "CommandHandler\|ejecutó" /home/bot/apion/logs/bot.log
```

---

## 🟣 **USAR SCREEN PARA SESIÓN PERSISTENTE**

Mantener una sesión abierta que sobrevive desconexiones:

```bash
# Crear sesión "apion-logs"
screen -S apion-logs

# Dentro de screen, ver logs
tail -f /home/bot/apion/logs/bot.log

# Detach (salir sin cerrar): Ctrl+A, luego D

# Reconectar después:
screen -r apion-logs

# Ver sesiones disponibles:
screen -ls

# Eliminar sesión:
screen -X -S apion-logs quit
```

---

## 📊 **MONITOREO AVANZADO**

### Ver estadísticas de logs
```bash
# Contar líneas de log por tipo
grep -c "INFO" /home/bot/apion/logs/bot.log
grep -c "ERROR" /home/bot/apion/logs/bot.log
grep -c "WARNING" /home/bot/apion/logs/bot.log

# Ver resumen
echo "=== Estadísticas de Logs ===" && \
echo "INFO: $(grep -c 'INFO' /home/bot/apion/logs/bot.log)" && \
echo "ERROR: $(grep -c 'ERROR' /home/bot/apion/logs/bot.log)" && \
echo "WARNING: $(grep -c 'WARNING' /home/bot/apion/logs/bot.log)"
```

### Ver tamaño de logs
```bash
# Tamaño total
du -sh /home/bot/apion/logs/

# Tamaño por archivo
ls -lh /home/bot/apion/logs/
```

### Rotación automática
Los logs se rotan automáticamente:
- Máximo 5MB por archivo
- Se guardan 10 backups
- Los antiguos se comprimen

```bash
# Ver archivos rotados
ls -la /home/bot/apion/logs/
```

---

## 🚀 **DASHBOARD EN TIEMPO REAL (BONUS)**

Crear un alias para comando rápido:

```bash
# Agregar a ~/.bashrc
alias apion-logs="tail -f /home/bot/apion/logs/bot.log"
alias apion-status="sudo systemctl status apion.service apion-paypal.service apion-promerica.service"
alias apion-restart="sudo systemctl restart apion.service"

# Luego usar simplemente:
apion-logs      # Ver logs
apion-status    # Ver estado
apion-restart   # Reiniciar
```

---

## 💡 **COMANDOS ÚTILES RÁPIDOS**

| Comando | Propósito |
|---------|-----------|
| `tail -f logs/bot.log` | Ver logs en tiempo real |
| `sudo journalctl -u apion.service -f` | Ver logs del servicio |
| `sudo systemctl status apion.service` | Ver estado del servicio |
| `grep "ERROR" logs/bot.log` | Buscar errores |
| `grep "user_id" logs/bot.log` | Buscar actividad de usuario |
| `tail -n 100 logs/bot.log` | Ver últimas 100 líneas |
| `wc -l logs/bot.log` | Contar líneas totales |
| `sudo systemctl restart apion.service` | Reiniciar bot |
| `sudo systemctl stop apion.service` | Detener bot |
| `sudo systemctl start apion.service` | Iniciar bot |

---

## 📝 **FORMATO DE LOGS**

Los logs ahora incluyen:
```
2026-06-27 10:23:45,123 - nombre_modulo - NIVEL - Mensaje
          ↑              ↑                 ↑      ↑
       Timestamp      Módulo          Nivel   Mensaje
```

**Niveles disponibles:**
- `DEBUG`: Información detallada para debugging
- `INFO`: Información general (inicios, comandos)
- `WARNING`: Advertencias (problemas potenciales)
- `ERROR`: Errores (algo falló)
- `CRITICAL`: Errores críticos (bot puede caerse)

---

## 🔐 **TIPS DE SEGURIDAD**

```bash
# Ver logs sin mostrar IDs sensibles
tail -f logs/bot.log | sed 's/[0-9]\{9,\}/[USER_ID]/g'

# Guardar logs en un archivo para análisis posterior
tail -f logs/bot.log > debug_$(date +%Y%m%d_%H%M%S).log

# Ver solo comandos de usuarios (no sistema)
grep -E "ejecutó|/start|/redeem|/bin" logs/bot.log
```

---

## 🎯 **WORKFLOW RECOMENDADO**

1. **Conectar a VPS:**
   ```bash
   ssh bot@VPS_IP
   ```

2. **Abrir dos terminales SSH:**
   - Terminal 1: `tail -f logs/bot.log`
   - Terminal 2: Ejecutar comandos

3. **Monitorear en tiempo real:**
   ```bash
   tail -f logs/bot.log
   ```

4. **Cuando hay error, buscar contexto:**
   ```bash
   grep -B 5 -A 5 "ERROR" logs/bot.log
   ```

5. **Reiniciar servicios si es necesario:**
   ```bash
   sudo systemctl restart apion.service
   ```

---

**¡Ahora puedes ver todo lo que sucede en tiempo real en la VPS! 🚀**
