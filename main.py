import asyncio
import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from telegram.ext import Application, ConversationHandler, CommandHandler, MessageHandler, filters
from telegram.request import HTTPXRequest

# Configuración y Tokens
from config import TELEGRAM_TOKEN

# Importación de Handlers por responsabilidad
from handlers.admin import editgate, genkey_cmd, setrank_cmd, users_cmd, delmem,status_api_cmd,addcredits_cmd,delcredits_cmd, broadcast
from handlers.user import start_cmd, me_cmd, redeem_cmd,precios_cmd
from handlers.gates import wrenchmonkey_handler,gencookiemx,gencookieus,gencookieca, stripecharged_handler
from handlers.callbacks import menu_callbacks, callback_regen, handle_text_input
from handlers.card_tools import bin_master_handler, bin_cmd, vbv_command_handler, extra_cmd
from handlers.gates import dressage_handler, clovervariable_handler,neonet,b31
from amzmanual.amzmanualusa import WAITING_FOR_NUMBERSUSA, WAITING_FOR_OTPUSA, genmanusa, receive_numberusa,receive_otpusa ,cancelusa

from amzmanual.amzmanualmx import genmanmx, receive_number_mx, receive_otp_mx , cancel_mx , WAITING_FOR_NUMBERSMX , WAITING_FOR_OTPMX
from amzmanual.amzmanualca import genmanca, receive_number_ca, receive_otp_ca , cancel_ca , WAITING_FOR_NUMBERSCA , WAITING_FOR_OTPCA


# Importación de Gates (Nuevas funciones individuales)
from handlers.gates import (
    gate_paypal,
    gate_promerica,
    prophecy_handler,
    moneris_handler,
    worker_bot
)

from plugins.gen import gen_cmd

# ================= CONFIGURACIÓN DE LOGGING =================
def setup_logging():
    """Configura logging para escribir en archivo Y consola simultáneamente"""

    # Crear carpeta logs si no existe
    os.makedirs("logs", exist_ok=True)

    # Formato detallado
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    log_formatter = logging.Formatter(log_format, datefmt='%Y-%m-%d %H:%M:%S')

    # Logger raíz
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # 1. Handler para consola (stdout)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(log_formatter)
    root_logger.addHandler(console_handler)

    # 2. Handler para archivo con rotación (máx 5MB, 10 backups)
    file_handler = RotatingFileHandler(
        'logs/bot.log',
        maxBytes=5*1024*1024,  # 5MB
        backupCount=10,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(log_formatter)
    root_logger.addHandler(file_handler)

    return root_logger

logger = setup_logging()

async def post_init(application):
    """
    Se ejecuta al iniciar el bot.
    Lanza los 10 workers que procesan las colas de /gt (Promerica).
    """
    for i in range(1, 11):
        asyncio.create_task(worker_bot(i, application))
    logger.info(f"🚀 10 Workers de Gates (Promerica) iniciados correctamente.")

def main():
    request = HTTPXRequest(
        connect_timeout=30.0,
        read_timeout=30.0,
        write_timeout=30.0,
        pool_timeout=30.0,
    )
    # Inicialización de la Aplicación
    app = (
        ApplicationBuilder()
        .token(TELEGRAM_TOKEN)
        .request(request)
        .post_init(post_init)
        .concurrent_updates(True) # Manejo de múltiples usuarios a la vez
        .build()
    )

    # --- COMANDOS DE USUARIO ---
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("cmds", start_cmd))
    app.add_handler(CommandHandler("me", me_cmd))
    app.add_handler(CommandHandler("redeem", redeem_cmd))
    app.add_handler(CommandHandler("precios", precios_cmd))

    # --- COMANDOS DE ADMINISTRACIÓN ---
    app.add_handler(CommandHandler("delcrd", delcredits_cmd))
    app.add_handler(CommandHandler("addcrd", addcredits_cmd))
    app.add_handler(CommandHandler("apistatus", status_api_cmd))
    app.add_handler(CommandHandler("users", users_cmd))
    app.add_handler(CommandHandler("delmem", delmem))
    app.add_handler(CommandHandler("editgate", editgate))
    app.add_handler(CommandHandler("genkey", genkey_cmd))
    app.add_handler(CommandHandler("setrank", setrank_cmd))
    app.add_handler(CommandHandler("mglobal", broadcast))

    # --- COMANDOS DE HERRAMIENTAS (TOOLS) ---
    app.add_handler(CommandHandler("bin", bin_cmd))
    app.add_handler(CommandHandler("binlook", bin_master_handler))
    app.add_handler(CommandHandler("binbank", bin_master_handler))
    app.add_handler(CommandHandler("extra", extra_cmd))
    app.add_handler(CommandHandler("gen", gen_cmd))
    app.add_handler(CommandHandler("vbv", vbv_command_handler))

    # --- COMANDOS DE GENCOOKIE  ---
    app.add_handler(CommandHandler("gencookieca", gencookieca))  
    app.add_handler(CommandHandler("gencookiemx", gencookiemx))
    app.add_handler(CommandHandler("gencookieus", gencookieus))

    # --- COMANDOS DE GENCOOKIEMANUAL ---
    

    # USA
    conv_handler_usa = ConversationHandler(
        entry_points=[CommandHandler("genmanus", genmanusa)],
        states={
            WAITING_FOR_NUMBERSUSA: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_numberusa)],
            WAITING_FOR_OTPUSA: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_otpusa)],
        },
        fallbacks=[CommandHandler("cancel", cancelusa)],
    )
    app.add_handler(conv_handler_usa)

    # MEXICO
    conv_handler_mx = ConversationHandler(
        entry_points=[CommandHandler("genmanmx", genmanmx)],
        states={
            WAITING_FOR_NUMBERSMX: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_number_mx)],
            WAITING_FOR_OTPMX: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_otp_mx)],
        },
        fallbacks=[CommandHandler("cancel", cancel_mx)],
    )
    app.add_handler(conv_handler_mx)

    # CANADA
    conv_handler_ca = ConversationHandler(
        entry_points=[CommandHandler("genmanca", genmanca)],
        states={
            WAITING_FOR_NUMBERSCA: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_number_ca)],
            WAITING_FOR_OTPCA: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_otp_ca)],
        },
        fallbacks=[CommandHandler("cancel", cancel_ca)],
    )
    app.add_handler(conv_handler_ca)


    # --- COMANDOS DE GATES (MIGRACIÓN FINAL) ---
    # Ahora cada gate tiene su propia función dedicada
    app.add_handler(CommandHandler("wm", wrenchmonkey_handler))
    app.add_handler(CommandHandler("stp", stripecharged_handler))
    app.add_handler(CommandHandler("pp", gate_paypal))      # Gate PayPal
    app.add_handler(CommandHandler("gt", gate_promerica))  # Gate Promerica (Usa Workers)
    app.add_handler(CommandHandler("pfw", prophecy_handler)) # Gate Payflow (Migrado)
    app.add_handler(CommandHandler("mn", moneris_handler))   # Gate Moneris (Migrado, pero requiere ajustes finales)
    app.add_handler(CommandHandler("ka", dressage_handler))
    app.add_handler(CommandHandler("clo", clovervariable_handler))
    app.add_handler(CommandHandler("neo", neonet))
    app.add_handler(CommandHandler("b3", b31))




    # --- MANEJO DE CALLBACKS Y ENTRADAS DE TEXTO ---
    # Botón de regenerar tarjetas
    app.add_handler(CallbackQueryHandler(callback_regen, pattern="^regen_"))
    # Broadcast confirmation callbacks
    from handlers.admin import broadcast_callback
    app.add_handler(CallbackQueryHandler(broadcast_callback, pattern="^broadcast_"))
    # Menú principal y navegación
    app.add_handler(CallbackQueryHandler(menu_callbacks))
    # Maneja texto suelto (como cuando el bot pide los días para una key)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))

    logger.info("🚀 APION BOT Reestructurado e Iniciado...")
    logger.info(f"📝 Logs guardados en: logs/bot.log")
    app.run_polling()

if __name__ == '__main__':
    main()