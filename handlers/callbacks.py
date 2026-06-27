# handlers/callbacks.py
import random
import string
import io
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import GATES_STATUS
from database import load_keys, save_keys, get_rango 
from database import add_chat
from handlers.card_tools import cache_bins # Asegúrate de importar el cache
from handlers.card_tools import gen_logic

async def menu_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data 
    chat_id = update.effective_chat.id # Lo necesitamos para el cache
    try:
        add_chat(chat_id)
    except Exception:
        pass
    await query.answer()

    # Mantenemos el teclado siempre visible para que no desaparezca
    keyboard = [
        [
            InlineKeyboardButton("Gates 🛠", callback_data="main_gates"),
            InlineKeyboardButton("Tools 🎟", callback_data="main_tools"),
            InlineKeyboardButton("Info 👤", callback_data="ver_perfil"),
            InlineKeyboardButton("Gencookies 🍪", callback_data="gencookies")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # --- TUS GATES ---
    if data == "main_gates":
        status_pp = "🟢 ON" if GATES_STATUS.get("pp", True) else "🔴 OFF"
        status_gt = "🟢 ON" if GATES_STATUS.get("gt", True) else "🔴 OFF"
        status_pfw = "🟢 ON" if GATES_STATUS.get("pfw", True) else "🔴 OFF"
        status_stp = "🟢 ON" if GATES_STATUS.get("stp", True) else "🔴 OFF"
        status_clo = "🟢 ON" if GATES_STATUS.get("clo", True) else "🔴 OFF"
        status_neo = "🟢 ON" if GATES_STATUS.get("neo", True) else "🔴 OFF"
        status_b3 = "🟢 ON" if GATES_STATUS.get("braintree1", True) else "🔴 OFF"


        txt = (
            "<b>━━ ━ ━ ━ ━ ━ ━ ━ ━━</b>\n"
            "<b>[                 GATES                 ]</b>\n"
            "<b>━━ ━ ━ ━ ━ ━ ━ ━ ━━</b>\n"
            f"• <code>/gt</code> | <b>Gate Promerica</b> - Status > {status_gt}\n"
            "<i>Uso Exclusivo Para Tarjetas Promerica Guatemala</i>\n\n"
            
            f"• <code>/pp</code> | <b>Gate PayPal</b> - Status > {status_pp}\n"
            "<i>Gate PayPal Auth</i>\n\n"

            f"• <code>/pfw</code> | <b>Gate Payflow CVV</b> - Status > {status_pfw}\n"
            "<i>Gate Payflow CVV Charged</i>\n\n"

            f"• <code>/stp</code> | <b>Gate Stripe Charged</b> - Status > {status_stp}\n"
            "<i>Gate Stripe Charged </i>\n\n"

            f"• <code>/clo</code> | <b>Gate Clover Charged</b> - Status > {status_clo}\n"
            "<i>Gate Clover Charged </i>\n\n"
            
            f"• <code>/neo</code> | <b>Neonet Gate</b> - Status > {status_neo}\n"
            "<i>Gate Neonet </i>\n\n"

            f"• <code>/b3</code> | <b>Braintree Gate</b> - Status > {status_b3}\n"
            "<i>Gate Braintree </i>\n\n"
   
        )
        await query.edit_message_text(txt, reply_markup=reply_markup, parse_mode='HTML')

    # --- TUS TOOLS ---
    elif data == "main_tools":
        txt = (
            "<b>━━ ━ ━ ━ ━ ━ ━ ━ ━━</b>\n"
            "<b>[                 TOOLS                 ]</b>\n"
            "<b>━━ ━ ━ ━ ━ ━ ━ ━ ━━</b>\n"
            "• <code>/bin</code> | <b>Información del Bin</b>\n"
            "<i>Ejemplo:</i> <code>/bin 443019</code>\n\n"
            
            "• <code>/binlook</code> | <b>Búsqueda de Bins</b>\n"
            "<i>Ejemplo:</i> <code>/binlook [Pais] - [Categoría] - [Nivel]</code>\n\n"
            
            "• <code>/extra</code> | <b>Genera una extra</b>\n"
            "<i>Ejemplo:</i> <code>/extra [Bin]</code>\n"
            "<b>━━ ━ ━ ━ ━ ━ ━ ━ ━━</b>\n"

            "• <code>/vbv</code> | <b>Verifica si un bin tiene 3D</b>\n"
            "<i>Ejemplo:</i> <code>/3d [cc|mm|aa|cvv]</code>\n"
            "<b>━━ ━ ━ ━ ━ ━ ━ ━ ━━</b>"
        )
        await query.edit_message_text(txt, reply_markup=reply_markup, parse_mode='HTML')

    # --- TU PERFIL ---
    elif data == "ver_perfil":
        user_id = query.from_user.id
        rango_num = get_rango(user_id)
        
        rangos_nombres = {
            3: "OWNER 👑",
            2: "ADMIN 👨‍✈️",
            1: "PREMIUM 🌟",
            0: "FREE 👤"
        }
        mi_rango = rangos_nombres.get(rango_num, "FREE 👤")

        expira_txt = "N/A"
        if rango_num == 1:
            data_keys = await load_keys()
            exp = data_keys["usuarios"].get(str(user_id), {}).get("expires_at", "N/A")
            expira_txt = f"{exp[:10]}" if exp != "EVER" else "Eterna ♾"
        elif rango_num in [2, 3]:
            expira_txt = "Ilimitada 🛡️"

        txt = (
            "<b>━━ ━ ━ ━ ━ ━ ━ ━ ━━</b>\n"
            "<b>[     PERFIL DE USUARIO     ]</b>\n"
            "<b>━━ ━ ━ ━ ━ ━ ━ ━ ━━</b>\n"
            f"<b>Nombre |</b> {query.from_user.first_name}\n"
            f"<b>ID |</b> <code>{user_id}</code>\n"
            f"<b>Rango |</b> {mi_rango}\n"
            f"<b>Expira |</b> {expira_txt}\n"
            "<b>━━ ━ ━ ━ ━ ━ ━ ━ ━━</b>"
        )
        await query.edit_message_text(txt, reply_markup=reply_markup, parse_mode='HTML')

    # --- COOKIES ---
    elif data == "gencookies":
        status_amz_ca = "🟢 ON" if GATES_STATUS.get("gencookieca", True) else "🔴 OFF"
        status_amz_us = "🟢 ON" if GATES_STATUS.get("gencookieus", True) else "🔴 OFF"
        status_amz_mx = "🟢 ON" if GATES_STATUS.get("gencookiemx", True) else "🔴 OFF"
        status_amz_manusa = "🟢 ON" if GATES_STATUS.get("genmanusa", True) else "🔴 OFF"
        status_amz_manmx = "🟢 ON" if GATES_STATUS.get("genmanmx", True) else "🔴 OFF"
        status_amz_manca = "🟢 ON" if GATES_STATUS.get("genmanca", True) else "🔴 OFF"

        txt = (
            "<b>━━ ━ ━ ━ ━ ━ ━ ━ ━━</b>\n"
            "<b>Generador Automatico de cookies</b>\n"
            "<b>━━ ━ ━ ━ ━ ━ ━ ━ ━━</b>\n"
            f"• <code>/gencookieca</code> | <b>Generador de Cookies Amazon Cánada</b>\n - Status > {status_amz_ca}\n"
            "<i>Genera Cookies exclusivamente de Cánada - Precio 1 CRD</i>\n\n"
            
            f"• <code>/gencookieus</code> | <b>Generador de Cookies Amazon USA</b>\n - Status > {status_amz_us}\n"
            "<i>Genera Cookies exclusivamente de USA - PRECIO 2 CRD</i>\n\n"

            f"• <code>/gencookiemx</code> | <b>Generador de Cookies Amazon México</b>\n - Status > {status_amz_mx}\n"
            "<i>Genera Cookies exclusivamente de México - PRECIO 1 CRD</i>\n\n"

            "<b>━━ ━ ━ ━ ━ ━ ━ ━ ━━</b>\n"
            "<b>Generador Semimanual de Cookies Amazon USA</b>\n"
            "<b>━━ ━ ━ ━ ━ ━ ━ ━ ━━</b>\n"
            f"• <code>/genmanusa</code> | <b>Generador Semimaual de Cookies Amazon USA</b> - Status > {status_amz_manusa}\n"
            "<i>Genera Cookies de USA pero con proceso Semimanual - PRECIO 0.25 CRDS</i>\n\n"
            f"• <code>/genmanmx</code> | <b>Generador Semimanual de Cookies Amazon México</b>\n - Status > {status_amz_manmx}\n"
            "<i>Genera Cookies de México pero con proceso Semimanual - PRECIO 0.25 CRDS</i>\n\n"
            f"• <code>/genmanca</code> | <b>Generador Semimanual de Cookies Amazon Cánada</b>\n - Status > {status_amz_manca}\n"
            "<i>Genera Cookies de Cánada pero con proceso Semimanual - PRECIO 0.25 CRDS</i>\n\n"
            "<b>━━ ━ ━ ━ ━ ━ ━ ━ ━━</b>"
        )
        await query.edit_message_text(txt, reply_markup=reply_markup, parse_mode='HTML')

    # --- KEYS ---
    elif data == "k_eterna":
        rango_key = context.user_data.get('temp_range', 'Premium')
        key = f"APION-{rango_key.upper()}-EVER-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=10))
        
        db_data = await load_keys()
        if "keys" not in db_data: db_data["keys"] = []
        
        db_data["keys"].append({
            "key": key, 
            "used": False, 
            "permanent": True, 
            "range": rango_key 
        })
        await save_keys(db_data)
        await query.edit_message_text(f"♾ **Key {rango_key} Eterna Generada:**\n`{key}`", parse_mode='Markdown')
        context.user_data.pop('temp_range', None)
        
    elif data == "k_dias":
        context.user_data['esperando_dias'] = True
        await query.message.reply_text("🔢 **¿Cuántos días de suscripción deseas asignar?**")

    # 🏦 --- SECCIÓN DE BANCOS CORREGIDA ---
    elif data.startswith("bnk_"):
        banco_id = data.split("_")[1] # Extraemos el ID como string (no int)
        
        if chat_id in cache_bins:
            bin_data = cache_bins[chat_id]["data"]
            keys_list = cache_bins[chat_id]["sorted_keys"]
            query_name = cache_bins[chat_id]["query"]
            
            # Soporte híbrido: Si es un índice numérico viejo o una clave string nueva
            if banco_id.isdigit():
                idx = int(banco_id)
                selected_key = keys_list[idx] if idx < len(keys_list) else None
            else:
                selected_key = banco_id
                
            if not selected_key or selected_key not in bin_data:
                return await query.edit_message_text("⚠️ No se pudo cargar este banco. Realiza la búsqueda de nuevo.")
                
            banco = bin_data[selected_key]
            
            txt = (
                f"🏦 BANCO:  `{banco['nombre']}`\n"
                f"🔍 Resultados para: `{query_name}`\n"
                "━━━━━━━━━━━━━━━━━━\n"
            )
            
            for cat, bins in banco["sub"].items():
                bins_str = ", ".join([f"`{b}`" for b in bins])
                txt += f"• **{cat}:**\n  └ {bins_str}\n"
            
            # Cambiado callback_data para regresar de manera inteligente al abecedario
            kb = [[InlineKeyboardButton("⬅️ Volver a la lista", callback_data="back_bins")]]
            await query.edit_message_text(txt, reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')
        else:
            await query.edit_message_text("⚠️ El buscador expiró o el bot se reinició. Usa `/binlook` de nuevo.")

    elif data == "back_bins":
        # Evitamos reescribir query.data para que Telegram no tire error.
        # Ejecutamos directamente la lógica del abecedario leyendo la caché:
        if chat_id in cache_bins:
            data_cache = cache_bins[chat_id]["data"]
            keys_list = cache_bins[chat_id]["sorted_keys"]
            q = cache_bins[chat_id]["query"]
            
            letras_disponibles = set()
            for k in keys_list:
                nombre_banco = data_cache[k]['nombre'].strip()
                if nombre_banco:
                    primera_letra = nombre_banco[0].upper()
                    if not primera_letra.isalpha():
                        letras_disponibles.add("#")
                    else:
                        letras_disponibles.add(primera_letra)

            lista_letras = sorted(list(letras_disponibles), key=lambda x: (x == "#", x))

            keyboard_letras = []
            row = []
            for letra in lista_letras:
                row.append(InlineKeyboardButton(f"🔤 {letra}", callback_data=f"let_{letra}"))
                if len(row) == 4:
                    keyboard_letras.append(row)
                    row = []
            if row:
                keyboard_letras.append(row)

            await query.edit_message_text(
                f"✅ Resultados para: *{q}*\n"
                f"📂 Selecciona una letra para desplegar los bancos:", 
                reply_markup=InlineKeyboardMarkup(keyboard_letras), 
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text("⚠️ El buscador expiró o el bot se reinició. Usa `/binlook` de nuevo.")

    # 🔤 --- NUEVA FUNCIÓN: SELECCIÓN DE LETRA ---
    elif data.startswith("let_"):
        letra_seleccionada = data.split("_")[1]
        
        if chat_id in cache_bins:
            data_cache = cache_bins[chat_id]["data"]
            keys_list = cache_bins[chat_id]["sorted_keys"]
            q = cache_bins[chat_id]["query"]
            
            kb_filtrado = []
            for k in keys_list:
                nombre_banco = data_cache[k]['nombre']
                primera_letra = nombre_banco[0].upper()
                
                pertenece = (letra_seleccionada == "#" and not primera_letra.isalpha()) or (primera_letra == letra_seleccionada)
                
                if belongs := pertenece:
                    # Guardamos usando la clave única string 'k' para que no falle al pulsar
                    kb_filtrado.append([InlineKeyboardButton(f"🏦 {nombre_banco[:35]}", callback_data=f"bnk_{k}")])
                    
            kb_filtrado.append([InlineKeyboardButton("🔙 Volver al Alfabeto", callback_data="back_to_alphabet")])
            
            await query.edit_message_text(
                f"📂 Bancos que inician con la letra *{letra_seleccionada}*:\n"
                f"🔍 Resultados para: `{q}`",
                reply_markup=InlineKeyboardMarkup(kb_filtrado),
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text("⚠️ El buscador expiró o el bot se reinició. Usa `/binlook` de nuevo.")

    # 🔙 --- NUEVA FUNCIÓN: REGRESAR AL ALFABETO ---
    elif data == "back_to_alphabet":
        if chat_id in cache_bins:
            data_cache = cache_bins[chat_id]["data"]
            keys_list = cache_bins[chat_id]["sorted_keys"]
            q = cache_bins[chat_id]["query"]
            
            letras_disponibles = set()
            for k in keys_list:
                nombre_banco = data_cache[k]['nombre'].strip()
                if nombre_banco:
                    primera_letra = nombre_banco[0].upper()
                    if not primera_letra.isalpha():
                        letras_disponibles.add("NUM")
                    else:
                        letras_disponibles.add(primera_letra)

            lista_letras = sorted(list(letras_disponibles), key=lambda x: (x == "NUM", x))

            keyboard_letras = []
            row = []
            for letra in lista_letras:
                row.append(InlineKeyboardButton(f"🔤 {letra}", callback_data=f"let_{letra}"))
                if len(row) == 4:
                    keyboard_letras.append(row)
                    row = []
            if row:
                keyboard_letras.append(row)

            await query.edit_message_text(
                f"✅ Resultados para: *{q}*\n"
                f"📂 Selecciona una letra para desplegar los bancos:", 
                reply_markup=InlineKeyboardMarkup(keyboard_letras), 
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text("⚠️ El buscador expiró o el bot se reinició. Usa `/binlook` de nuevo.")


# --- MANEJADOR DE TEXTO ---
async def handle_text_input(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if get_rango(u.effective_user.id) < 2: 
        return
        
    if c.user_data.get('esperando_dias'):
        try:
            dias = int(u.message.text)
            rango = c.user_data.get('temp_range', 'Premium')
            key = f"APION-{rango.upper()}-TIME-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=10))
            
            data = await load_keys()
            data["keys"].append({
                "key": key, 
                "used": False, 
                "days": dias, 
                "permanent": False,
                "range": rango 
            })
            await save_keys(data)
            await u.message.reply_text(f"🔑 Key {rango} de {dias} días generada:**\n`{key}`", parse_mode='Markdown')
        except ValueError:
            await u.message.reply_text("❌ Por favor, envía un número válido de días.")
        finally:
            c.user_data['esperando_dias'] = False
            c.user_data.pop('temp_range', None)


# --- REGENERACIÓN ---
async def callback_regen(update, context):
    query = update.callback_query
    _, bin_format, quantity = query.data.split("_")
    quantity = int(quantity)

    await query.answer("Generando nuevas tarjetas... ⏳")
    cards = [gen_logic(bin_format) for _ in range(quantity)]
    
    keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Regenerar", callback_data=f"regen_{bin_format}_{quantity}")]])

    if quantity <= 15:
        tarjetas_formateadas = "\n".join([f"<code>{c}</code>" for c in cards])
        txt = (
            f"<b>✨ Tarjetas Generadas</b>\n"
            f"<b>━━━━━━━━━━━━━━━━━</b>\n"
            f"{tarjetas_formateadas}\n"
            f"<b>━━━━━━━━━━━━━━━━━</b>"
        )
        await query.edit_message_text(txt, parse_mode="HTML", reply_markup=keyboard)
    else:
        out = io.BytesIO(("\n".join(cards)).encode())
        out.name = f"{bin_format[:6]}.txt"
        await context.bot.send_document(chat_id=query.message.chat_id, document=out, caption=f"✨ **Nuevas:** `{quantity}`", parse_mode="Markdown", reply_markup=keyboard)