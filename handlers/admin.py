# handlers/admin.py
import asyncio
from datetime import datetime
import random
import string
import httpx
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import ADMINS, GATES_STATUS
from database import load_keys, save_keys, get_all_users, get_all_chats
from database import get_rango
from config import GATES_STATUS, save_gates_status
import os
# handlers/admin.py

async def genkey_cmd(u: Update, c: ContextTypes.DEFAULT_TYPE):
    user_id = u.effective_user.id
    rango_creador = get_rango(user_id)

    # 1. Si no es ni Admin ni Owner, fuera.
    if rango_creador < 2:
        return await u.message.reply_text("❌ No tienes rango suficiente.")

    # 2. Verificar qué rango quiere generar
    rango_solicitado = "Premium"
    if c.args and c.args[0].lower() == "admin":
        # Si intenta crear un ADMIN pero él solo es ADMIN (Nivel 2), se lo prohibimos
        if rango_creador < 3:
            return await u.message.reply_text("⚠️ Solo el Owner puede generar keys de rango ADMIN.")
        rango_solicitado = "Admin"

    # Guardamos en la memoria temporal para el callback
    c.user_data['temp_range'] = rango_solicitado
    
    kb = [[
        InlineKeyboardButton("Días 📅", callback_data="k_dias"),
        InlineKeyboardButton("Eterna ♾", callback_data="k_eterna")
    ]]
    
    await u.message.reply_text(
        f"✨ **Generador de Keys ({rango_solicitado.upper()})**\nSelecciona la duración:", 
        reply_markup=InlineKeyboardMarkup(kb), 
        parse_mode='Markdown'
    )

    
async def users_cmd(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if u.effective_user.id not in ADMINS: return
    data = await load_keys()
    msg = "👥 **Usuarios Premium Activos:**\n\n"
    count = 0
    for k in data.get("keys", []):
        if k.get("used"):
            count += 1
            user_id = str(k['user'])
            expires = k.get('expires_at', 'Eterna')[:10]
            credits = data.get("usuarios", {}).get(user_id, {}).get("credits", 0)
            msg += f"• `{k['user']}` | {expires} | Créditos: `{credits}`\n"
    
    if count == 0: msg = "∅ No hay usuarios premium activos."
    await u.message.reply_text(msg, parse_mode='Markdown')



async def delmem(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if u.effective_user.id not in ADMINS: return
    if not c.args: return await u.message.reply_text("❌ Uso: `/delmem [ID]`")
    
    try:
        uid = int(c.args[0])
        data = await load_keys()
        data["keys"] = [k for k in data["keys"] if k.get("user") != uid]
        await save_keys(data)
        await u.message.reply_text(f"El usuario {uid} ha sido eliminado de los usuarios premium.")
    except:
        await u.message.reply_text("❌ ID inválido.")

async def editgate(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if u.effective_user.id not in ADMINS: return
    if len(c.args) < 2: return await u.message.reply_text("❌ Uso: `/editgate [gate] [on/off]`")
    
    gate = c.args[0].lower()
    status = c.args[1].lower()
    
    if gate in GATES_STATUS:
        # Actualizamos la variable en memoria
        GATES_STATUS[gate] = (status == "on")
        
        # --- NUEVO: Guardamos el cambio en el archivo JSON ---
        save_gates_status(GATES_STATUS)
        # ----------------------------------------------------
        
        estado_txt = "ENCENDIDO 🟢" if GATES_STATUS[gate] else "APAGADO 🔴"
        await u.message.reply_text(f"✅ Gate **{gate.upper()}** actualizado permanentemente a: `{estado_txt}`", parse_mode='Markdown')
    else:
        await u.message.reply_text(f"❌ El gate `{gate}` no existe en la configuración.")


async def setrank_cmd(u: Update, c: ContextTypes.DEFAULT_TYPE):
    # SOLO EL OWNER (Nivel 3)
    if get_rango(u.effective_user.id) < 3:
        return # Ni siquiera le contestamos para que no sepa que el comando existe

    if len(c.args) < 2:
        return await u.message.reply_text("💡 Uso: `/setrank [ID] [PREMIUM/ADMIN/FREE]`")

    target_id = c.args[0]
    nuevo_rango = c.args[1].upper()
    
    if nuevo_rango not in ["PREMIUM", "ADMIN", "FREE"]:
        return await u.message.reply_text("❌ Rango inválido. Usa: PREMIUM, ADMIN o FREE.")

    data = await load_keys()
    
    # Si el rango es FREE, lo quitamos de la lista de usuarios
    if nuevo_rango == "FREE":
        if target_id in data.get("usuarios", {}):
            del data["usuarios"][target_id]
    else:
        # Asignamos el rango con duración eterna por defecto
        if "usuarios" not in data: data["usuarios"] = {}
        data["usuarios"][target_id] = {
            "rango": nuevo_rango,
            "expires_at": "EVER"
        }

    await save_keys(data)
    await u.message.reply_text(f"✅ Usuario `{target_id}` actualizado a **{nuevo_rango}**.")



OWNER_ID = 5651880136  # Reemplaza con tu ID de Telegram
ADMINS = [5651880136, 5133617831]
IPROYAL_TOKEN = "033069d19075109d8910507be0d31ce95bdc497e9fb50f4dcc423978810f"
CAPSOLVER_KEY = "CAP-E628130ED40FD0A0BBC180D0C7822D2C3B13D9BAAE3152A7F7A15F473A4F852F"
CAPMONSTER_KEY = "9cba4e66a26ee99a90df4a526c41f005"

async def status_api_cmd(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if u.effective_user.id != OWNER_ID:
        return

    status_msg = await u.message.reply_text("<b>🔍 Consultando estados de servicios...</b>", parse_mode="HTML")
    
    results = {
        "iproyal": "Error ❌",
        "capsolver": "Error ❌",
        "capmonster": "Error ❌"
    }

    async with httpx.AsyncClient(timeout=15) as client:
        # 1. CONSULTA IPROYAL (Actualizado según la doc)
        try:
            # Endpoint correcto para residenciales
            url_ipr = 'https://resi-api.iproyal.com/v1/residential/subscription'
            headers_ipr = {
                'Authorization': f'Bearer {IPROYAL_TOKEN}',
            }
            res = await client.get(url_ipr, headers=headers_ipr)
            
            if res.status_code == 200:
                data = res.json()
                
                # IPRoyal devuelve un DICCIONARIO con quantity, amount, status, etc.
                quantity = data.get('quantity', 0)
                amount = data.get('amount', 0)
                status = data.get('status', 'N/A')
                
                # Mostramos quantity (MB), amount ($) y status
                results["iproyal"] = f"{quantity} MB | ${amount} ({status})"
            else:
                results["iproyal"] = f"Error {res.status_code}"
        except Exception as e:
            print(f"Error IPRoyal: {e}")
            results["iproyal"] = f"Error: {str(e)[:40]}"

        # 2. CONSULTA CAPSOLVER
        try:
            res = await client.post("https://api.capsolver.com/getBalance", json={"clientKey": CAPSOLVER_KEY})
            if res.status_code == 200:
                results["capsolver"] = f"${res.json().get('balance', 0):.2f}"
        except: pass

        # 3. CONSULTA CAPMONSTER
        try:
            res = await client.post("https://api.capmonster.cloud/getBalance", json={"clientKey": CAPMONSTER_KEY})
            if res.status_code == 200:
                results["capmonster"] = f"${res.json().get('balance', 0):.2f}"
        except: pass

    # --- DISEÑO DEL MENSAJE FINAL ---
    txt = (
        "<b>━━ ━ ━ ━ ━ ━ ━ ━ ━━</b>\n"
        "<b>[ 🛡️ PANEL DE RECURSOS ]</b>\n"
        "<b>━━ ━ ━ ━ ━ ━ ━ ━ ━━</b>\n"
        f"<b>🌐 IPRoyal:</b> <code>{results['iproyal']}</code>\n"
        f"<b>🧩 CapSolver:</b> <code>{results['capsolver']}</code>\n"
        f"<b>👾 CapMonster:</b> <code>{results['capmonster']}</code>\n"
        "<b>━━ ━ ━ ━ ━ ━ ━ ━ ━━</b>\n"
        f"<i>Actualizado: {datetime.now().strftime('%H:%M:%S')}</i>"
    )
    
    await status_msg.edit_text(txt, parse_mode="HTML")


async def addcredits_cmd(u: Update, c: ContextTypes.DEFAULT_TYPE):
    # Solo el Owner puede dar créditos
    if u.effective_user.id not in ADMINS:
        return await u.message.reply_text("❌ No tienes permiso para usar este comando.")

    if len(c.args) < 2:
        return await u.message.reply_text("💡 Uso: `/addcredits [ID] [CANTIDAD]`")

    target_id = str(c.args[0])
    try:
        cantidad = int(c.args[1])
    except ValueError:
        return await u.message.reply_text("❌ La cantidad debe ser un número entero.")

    data = await load_keys()
    
    if target_id not in data.get("usuarios", {}):
        return await u.message.reply_text(f"❌ El usuario `{target_id}` no está registrado como Premium/Admin.")

    # Sumar créditos
    current_credits = data["usuarios"][target_id].get("credits", 0)
    data["usuarios"][target_id]["credits"] = current_credits + cantidad

    await save_keys(data)
    await u.message.reply_text(
        f"✅ Créditos actualizados.\n"
        f"👤 Usuario: {target_id}\n"
        f"💰 Nuevos créditos: {data['usuarios'][target_id]['credits']}"
    )


async def delcredits_cmd(u: Update, c: ContextTypes.DEFAULT_TYPE):
    # Solo el Owner puede quitar créditos
    if u.effective_user.id not in ADMINS:
        return await u.message.reply_text("❌ No tienes permiso para usar este comando.")

    if len(c.args) < 2:
        return await u.message.reply_text("💡 Uso: `/delcredits [ID] [CANTIDAD|all]`")

    target_id = str(c.args[0])
    cantidad_arg = str(c.args[1]).lower()

    data = await load_keys()
    
    if target_id not in data.get("usuarios", {}):
        return await u.message.reply_text(f"❌ El usuario `{target_id}` no está registrado como Premium/Admin.")

    current_credits = data["usuarios"][target_id].get("credits", 0)

    if cantidad_arg == "all":
        new_credits = 0
    else:
        try:
            cantidad = int(cantidad_arg)
        except ValueError:
            return await u.message.reply_text("❌ La cantidad debe ser un número entero o 'all' para eliminar todos los créditos.")
        new_credits = max(current_credits - cantidad, 0)

    data["usuarios"][target_id]["credits"] = new_credits

    await save_keys(data)
    await u.message.reply_text(
        f"✅ Créditos actualizados.\n"
        f"👤 Usuario: {target_id}\n"
        f"💰 Créditos restantes: {new_credits}"
    )


    
import html  # Asegúrate de tener este import al inicio del archivo
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import re
AKIRO = 5133617831
async def broadcast(u: Update, c: ContextTypes.DEFAULT_TYPE):
    user_id = u.effective_user.id
    OWNER_ID = 5651880136  # Tu ID de Telegram
    AKIRO = 5133617831

    if user_id != OWNER_ID and user_id != AKIRO:
        await u.message.reply_text("❌ No tienes permiso para usar este comando.")
        return


    # 1. Capturar el texto original con las etiquetas HTML nativas
    texto_completo = u.message.text_html if u.message.text_html else ""
    
    # Remover el comando inicial (/broadcast o /mglobal)
    match_comando = re.match(r"^/\w+\s*", texto_completo)
    if match_comando:
        mensaje = texto_completo[match_comando.end():].strip()
    else:
        mensaje = " ".join(c.args).strip()

    if not mensaje:
        await u.message.reply_text("❌ Uso: /broadcast <mensaje>")
        return

    # 2. LIMPIEZA MULTILÍNEA: Remueve 'mensaje = """' o similares incluso si hay saltos de línea previos
    # Quitamos la declaración inicial si existe
    mensaje = re.sub(r"^(mensaje\s*=\s*['\"]{3})\s*", "", mensaje, flags=re.IGNORECASE | re.MULTILINE)
    # Quitamos las comillas triples de cierre al final
    mensaje = re.sub(r"\s*(['\"]{3})$", "", mensaje, flags=re.MULTILINE)
    
    # Limpieza final de espacios sobrantes al inicio y final del anuncio limpio
    mensaje = mensaje.strip()

    # Guardar el mensaje limpio para el envío masivo definitivo
    c.user_data['pending_broadcast'] = mensaje

    # 3. Mostrar la previsualización con el formato nativo aplicado
    preview = (
        f"📣 <b>Previsualización del broadcast (Así lo verán los usuarios):</b>\n"
        f"____________________________________\n\n"
        f"{mensaje}\n"
        f"____________________________________\n\n"
    )

    kb = [[
        InlineKeyboardButton("✅ Enviar", callback_data="broadcast_send"),
        InlineKeyboardButton("❌ Cancelar", callback_data="broadcast_cancel")
    ]]

    try:
        await u.message.reply_text(
            preview,
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode="HTML"
        )
    except Exception as e:
        # Fallback por si hay etiquetas mal cerradas
        mensaje_plano = html.escape(mensaje)
        await u.message.reply_text(
            f"❌ <b>Error de sintaxis HTML en tu mensaje:</b>\n"
            f"Revisa que todas tus etiquetas HTML estén correctamente cerradas.\n\n"
            f"<b>Tu código enviado:</b>\n<code>{mensaje_plano}</code>",
            parse_mode="HTML"
        )


async def broadcast_callback(u: Update, c: ContextTypes.DEFAULT_TYPE):
    """Maneja los callbacks para enviar o cancelar el broadcast."""
    query = u.callback_query
    await query.answer()

    user_id = u.effective_user.id
    OWNER_ID = 5651880136

    if user_id != OWNER_ID and user_id != AKIRO:
        return await query.edit_message_text("❌ No tienes permiso para confirmar este broadcast.")

    action = query.data
    if action == 'broadcast_cancel':
        c.user_data.pop('pending_broadcast', None)
        return await query.edit_message_text("❌ Broadcast cancelado.")

    if action == 'broadcast_send':
        mensaje = c.user_data.pop('pending_broadcast', None)
        if not mensaje:
            return await query.edit_message_text("⚠️ No hay mensaje pendiente para enviar.")

        users = set(get_all_users())
        chats = set(get_all_chats())
        targets = users.union(chats)

        if not targets:
            return await query.edit_message_text("⚠️ No hay destinatarios registrados.")

        await query.edit_message_text("🚀 Difundiendo mensaje, por favor espera...")

        success = 0
        failed = 0
        MAX_LENGTH = 4000  # Límite de seguridad para Telegram

        for target in targets:
            try:
                # ❌ AQUÍ QUITAMOS EL html.escape() PARA QUE TELEGRAM INTERPRETE LAS ETIQUETAS
                if len(mensaje) > MAX_LENGTH:
                    for x in range(0, len(mensaje), MAX_LENGTH):
                        chunk = mensaje[x:x+MAX_LENGTH]
                        await c.bot.send_message(
                            chat_id=target,
                            text=chunk,
                            parse_mode="HTML"  # ✅ Formato nativo interpretado
                        )
                        await asyncio.sleep(0.05)
                    success += 1
                else:
                    await c.bot.send_message(
                        chat_id=target,
                        text=mensaje,
                        parse_mode="HTML"  # ✅ Formato nativo interpretado
                    )
                    success += 1
                    await asyncio.sleep(0.05) # Delay prudente anti-flood

            except Exception as e:
                failed += 1
                print(f"❌ Error al enviar a {target}: {e}")

        return await query.edit_message_text(
            f"✅ <b>Broadcast completado</b>\n\n"
            f"📊 Enviado a: <b>{success}</b> chats\n"
            f"❌ Fallidos: <b>{failed}</b> chats",
            parse_mode="HTML"
        )