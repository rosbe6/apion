from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import get_rango, load_keys, save_keys, add_chat
from datetime import datetime, timedelta

async def start_cmd(u: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Gates 🛠", callback_data="main_gates"), InlineKeyboardButton("Tools 🎟", callback_data="main_tools"), InlineKeyboardButton("Info 👤", callback_data="ver_perfil"),InlineKeyboardButton("Gencookies 🍪", callback_data="gencookies")]]
    await u.message.reply_text("<b>━━ ━ ━ ━ ━ ━ ━ ━ ━━</b>\n<b>[ APION BOT MENÚ ]</b>\n<b>━━ ━ ━ ━ ━ ━ ━ ━ ━━</b>\nBienvenido...", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
    try:
        add_chat(u.effective_chat.id)
    except Exception:
        pass

async def me_cmd(u: Update, c: ContextTypes.DEFAULT_TYPE):
    user_id = u.effective_user.id
    rango_num = get_rango(user_id)

    data = await load_keys()
    user_data = data.get("usuarios", {}).get(str(user_id), {})

    creditos = user_data.get("credits", 0)
    exp = user_data.get("expires_at", "N/A")

    if rango_num >= 2:
        creditos_display = "Ilimitados ♾"
    else:
        creditos_display = f"{creditos} 💰"

    rangos = {3: "OWNER 👑", 2: "ADMIN 👨‍✈️", 1: "PREMIUM 🌟", 0: "FREE 👤"}
    rango_txt = rangos.get(rango_num, "FREE")
    exp = data["usuarios"].get(str(user_id), {}).get("expires_at", "N/A")
    msg = (
        "<b>━━ ━ ━ ━ ━ ━ ━ ━ ━━</b>\n"
        "<b>[ 👤 MI PERFIL APION ]</b>\n"
        "<b>━━ ━ ━ ━ ━ ━ ━ ━ ━━</b>\n"
        f"<b>🆔 ID:</b> <code>{user_id}</code>\n"
        f"<b>⭐ Rango:</b> <code>{rango_txt}</code>\n"
        f"<b>💰 Créditos:</b> <code>{creditos_display}</code>\n"
        f"<b>🕳️ Expira:</b> <code>{exp}</code>\n"
    )


    
    await u.message.reply_text(msg, parse_mode='HTML')

    
async def redeem_cmd(u: Update, c: ContextTypes.DEFAULT_TYPE):
    args = u.message.text.split()
    if len(args) < 2: return
    key_in, user_id = args[1], str(u.effective_user.id)
    data = await load_keys()
    for k in data["keys"]:
        if k["key"] == key_in and not k.get("used"):
            k["used"], k["user"] = True, u.effective_user.id
            rango_key = k.get("range", "Premium")
            exp = "EVER" if k.get("permanent") else (datetime.now() + timedelta(days=k.get("days", 30))).isoformat()
            if "usuarios" not in data: data["usuarios"] = {}
            data["usuarios"][user_id] = {"rango": rango_key.upper(), "expires_at": exp}
            await save_keys(data)
            return await u.message.reply_text(f"✅ Activado: **{rango_key.upper()}**")
    await u.message.reply_text("❌ Key inválida.")


async def precios_cmd(u: Update, c: ContextTypes.DEFAULT_TYPE):
    msg = (
        "<b>PLANES COOKIES</b>\n\n"
        "• PREMIUM 1: 6.5 USDT - 7 días de duración - 10 Cookies diarias\n"
        "• PREMIUM 2: 10 USDT - 15 días de duración - 10 cookies diarias\n"
        "• PREMIUM 3: 15 USDT - 30 días de duración - 10 cookies diarias\n\n"
        "Para comprar, contacta a:.\n\n"
        "• Owner - @locionn\n"
        "• Admin - @Akihirox\n"
    )
    await u.message.reply_text(msg, parse_mode='HTML')

