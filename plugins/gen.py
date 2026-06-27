import io
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from handlers.card_tools import gen_logic 
from engines.bins_engine import get_bin_dict, get_bin_dict_new

async def get_info_bin_format(cc_number):
    """Consulta el BIN y devuelve un bloque de texto formateado."""
    bin_6 = cc_number[:6]
    data = await get_bin_dict_new(bin_6)
    if data:
        return (f"<b>{data['brand']} - {data['type']} - {data['level']}</b>\n"
                f"<b>{data['bank']}</b>\n"
                f"<b>{data['pais']}</b>")
    return "<i>Info del BIN no encontrada</i>"


async def gen_cmd(update, context):
    if not context.args:
        await update.message.reply_text("❌ **Uso:** `/gen bin|mm|aa|cvv cantidad`", parse_mode="Markdown")
        return

    bin_format = context.args[0]
    quantity = int(context.args[1]) if len(context.args) > 1 else 10
    
    # Generar lista
    cards = [gen_logic(bin_format) for _ in range(min(quantity, 1000))]
    
    # Botón de Regenerar
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Regenerar", callback_data=f"regen_{bin_format}_{quantity}")]
    ])

    if quantity <= 15:
        # Aquí creamos una lista de tarjetas, cada una envuelta en <code>
        tarjetas_formateadas = "\n".join([f"<code>{c}</code>" for c in cards])

        bin_info = await get_info_bin_format(bin_format)

        txt = (
            f"<b>✨ Tarjetas Generadas</b>\n"
            f"<b>━━━━━━━━━━━━━━━━━</b>\n"
            f"{tarjetas_formateadas}\n"  # <--- Cada una es copiable por separado
            f"<b>━━━━━━━━━━━━━━━━━</b>\n"
                f"{bin_info}\n"
                f"<b>━━━━━━━━━━━━━━━━━</b>\n"
            f"<b>Bin:</b> <code>{bin_format[:6]}</code>"
        )
        
        await update.message.reply_text(txt, parse_mode="HTML", reply_markup=keyboard)
    else:
        out = io.BytesIO(("\n".join(cards)).encode())
        out.name = f"{bin_format[:6]}.txt"
        await update.message.reply_document(document=out, caption=f"✨ BIN: `{bin_format[:6]}` | Cant: `{quantity}`", parse_mode="Markdown", reply_markup=keyboard)