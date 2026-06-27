from telegram.ext import ConversationHandler, CommandHandler, MessageHandler, filters, ContextTypes, Application
from telegram import Update
import asyncio
import os
import uuid
import shutil
from curl_cffi import requests
from DrissionPage import Chromium, ChromiumOptions
import psutil
import time
import random
from dotenv import load_dotenv

from amz.datos import generar_nombre, generar_direccion_real, generar_password
from amz.awf import CAPSOLVER_API_KEY, solve_captcha
from browser_utils import get_chromium_or_env
from config import GATES_STATUS
from database import tengo_creditos, usar_creditoman, check_antispam, OWNER_ID, ADMINS

load_dotenv()

def escritura_humana(elemento, texto):
    for caracter in texto:
        elemento.input(caracter)
        time.sleep(random.uniform(0.07, 0.35))

# Estados para el flujo de /genman
WAITING_FOR_NUMBERSUSA = 0
WAITING_FOR_OTPUSA = 1

# Diccionario para guardar el estado de cada usuario
user_data = {}

# --- Funciones para /genman ---
async def genmanusa(u: Update, c: ContextTypes.DEFAULT_TYPE):
    user_id = u.effective_user.id

    if not GATES_STATUS.get("genmanusa", True):
        await u.message.reply_text("⚠️ Genmanusa está temporalmente en mantenimiento")
        return ConversationHandler.END
    
    tengo_creditoss = tengo_creditos(user_id)
    if not tengo_creditoss:
        await u.message.reply_text("❌ No tienes créditos disponibles.", parse_mode="HTML")
        return ConversationHandler.END
    
    puedo, espera = check_antispam(user_id, OWNER_ID, ADMINS)
    if not puedo:
        await u.message.reply_text(f"⚠️ Espera {espera}s.", parse_mode="HTML")
        return ConversationHandler.END
    
    """Inicia el proceso de generación de cookie manual."""

    # Inicializar datos del usuario
    user_data[user_id] = {
        "numeros": [],
        "otp": None,
        "cookie": None,
        "passw": None,
        "numero_exitoso": None,
        "event": asyncio.Event()  # Para pausar/reanudar la ejecución
    }

    await u.message.reply_text(
        "Proceso de generación de cookie manual (Amazon USA 🇺🇸 )\n\n"
        "Envía <b>3 números de teléfono de USA</b> (uno por mensaje) con el formato:\n"
        "\n+1XXXXXXXXXX\n+1XXXXXXXXXX\n+1XXXXXXXXXX\n\n"
        "Espera a que el bot confirme cada número antes de enviar el siguiente.\n"
        "0.25 CRD se descontaran una vez que ingreses el tercer número", parse_mode="HTML"
    )
    return WAITING_FOR_NUMBERSUSA

async def receive_numberusa(u: Update, c: ContextTypes.DEFAULT_TYPE):
    """Recibe los números de teléfono del usuario."""
    user_id = u.effective_user.id
    text = u.message.text.strip()

    # Validar el formato del número


    # Guardar el número
    user_data[user_id]["numeros"].append(text)
    await u.message.reply_text(f"✅ Número {len(user_data[user_id]['numeros'])} recibido: {text}")

    # Si ya tenemos 3 números, iniciar el proceso y esperar OTP
    if len(user_data[user_id]["numeros"]) == 3:

        descontarcrd = usar_creditoman(user_id)
        if not descontarcrd:
            await u.message.reply_text("❌ No se pudo descontar el crédito. Intenta de nuevo.", parse_mode="HTML")
            return None
        

        await u.message.reply_text(
            "⏳ Iniciando proceso de registro en Amazon USA 🇺🇸 ...\n"
            "🔐 Cuando recibas el OTP, envíalo aquí."
        )
        asyncio.create_task(run_amazon_process(u, c, user_id))
        return WAITING_FOR_OTPUSA
    else:
        return WAITING_FOR_NUMBERSUSA

async def receive_otpusa(u: Update, c: ContextTypes.DEFAULT_TYPE):
    """Recibe el OTP del usuario y reanuda el proceso."""
    user_id = u.effective_user.id
    text = u.message.text.strip()

    if user_id in user_data and "event" in user_data[user_id]:
        if not text.isdigit():
            await u.message.reply_text("❌ OTP inválido. Envía solo números, por ejemplo: `123456`.")
            return WAITING_FOR_OTPUSA

        user_data[user_id]["otp"] = text
        user_data[user_id]["event"].set()
        await u.message.reply_text("✅ OTP recibido. Continuando con el registro...")
        return ConversationHandler.END
    else:
        await u.message.reply_text("❌ No hay un proceso de registro en curso. Usa /genman para empezar.")
        return ConversationHandler.END

async def cancelusa(u: Update, c: ContextTypes.DEFAULT_TYPE):
    """Cancela el proceso actual."""
    user_id = u.effective_user.id
    if user_id in user_data:
        data = user_data[user_id]
        if len(data.get("numeros", [])) < 3:
            # Si no se alcanzaron los 3 números, borrar inmediatamente
            del user_data[user_id]
        else:
            # Si el proceso ya comenzó, marcar cancelado y despertar el evento
            data["cancelled"] = True
            if "event" in data:
                data["event"].set()
    await u.message.reply_text("❌ Proceso cancelado.")
    return ConversationHandler.END

# --- Función principal para ejecutar el proceso de Amazon ---
async def run_amazon_process(u: Update, c: ContextTypes.DEFAULT_TYPE, user_id):
    """Ejecuta el proceso de Amazon con los números proporcionados."""
    try:
        # Obtener los números del usuario
        numeros = user_data[user_id]["numeros"]
        cookie = await registro_high_score_us_telegram(u, c, user_id, numeros)

        if cookie:

            descontarcrd = usar_creditoman(user_id)
            if not descontarcrd:
                return await u.message.reply_text("❌ No se pudo descontar el crédito. Intenta de nuevo.", parse_mode="HTML")
            await c.bot.send_message(
                chat_id=user_id,
                text=f"Cookie generada con éxito: \n\n<code>{cookie}</code>\n\n"
                        f"Cookie US | GENERADA  | 🇺🇸 "
                     f"Contraseña: {user_data[user_id]['passw']}\n"
                     f"Número usado: {user_data[user_id]['numero_exitoso']}",
                parse_mode="HTML"
            )
        else:
            await c.bot.send_message(
                chat_id=user_id,
                text="❌ **Error:** Todos los números ya están usados. Cancélalos y vuelve a intentar."
            )

    except Exception as e:
        await c.bot.send_message(
            chat_id=user_id,
            text=f"❌ **Error durante el proceso:** {str(e)}"
        )
    finally:
        # Limpiar datos del usuario
        if user_id in user_data:
            del user_data[user_id]

# --- Función adaptada de registro_high_score_us para Telegram ---
async def registro_high_score_us_telegram(u: Update, c: ContextTypes.DEFAULT_TYPE, user_id, numeros):
    """Versión adaptada para Telegram."""
    from DrissionPage import Chromium, ChromiumOptions
    import uuid
    import time
    import random

    # 1. Configuración inicial
    base_path = os.path.dirname(os.path.abspath(__file__))

    session_id = f"session_{uuid.uuid4().hex[:10]}"
    perfil_dir = os.path.join(base_path, "temp_profiles", session_id)
    os.makedirs(perfil_dir, exist_ok=True)

    chromium_path = get_chromium_or_env()
    print(f"[*] Usando Chromium: {chromium_path}")

    co = ChromiumOptions()
    co.set_browser_path(chromium_path)
    co.set_user_data_path(perfil_dir)
    co.set_argument('--disable-features=OptimizationGuideModelDownloading,OptimizationHints,OptimizationTargetPrediction,OptimizationGuide')
    co.set_argument('--disable-component-update')
    co.set_argument('--disable-background-networking')
    co.set_argument('--no-first-run')
    co.set_pref('intl.accept_languages', 'en-US,en')
    co.set_argument('--disable-blink-features=AutomationControlled')
    co.set_argument('--disable-webrtc')
    co.set_argument('--disable-dev-shm-usage')
    co.set_argument('--disable-extensions')

    # Proxy
    proxy_server = os.getenv("AMAZON_PROXY", "p.webshare.io:9999")
    print(f"[*] Usando proxy: {proxy_server}")
    co.set_proxy(f"http://{proxy_server}")


    def bloquear_recursos_no_esenciales(page):
        page.set.blocked_urls([
            '*.png', '*.jpg', '*.jpeg', '*.gif', '*.webp', '*.svg', '*.ico',
            '*.woff', '*.woff2', '*.ttf', '*.eot',
            '*analytics*', '*ads*', '*doubleclick*',
            '*optimizationguide-pa.googleapis.com*'
        ])

    co.auto_port()


    net_inicio = psutil.net_io_counters()
    browser = Chromium(co)
    
    

    try:
        page = browser.latest_tab
        bloquear_recursos_no_esenciales(page)
        
        url_inicio = "https://www.amazon.com/wallet"
        page.get(url_inicio)
        page.get(url_inicio)

        # Intentar con cada número
        numero_exitoso = None
        for intento, numero in enumerate(numeros, 1):
            try:
                page.get(url_inicio)
                page.wait.ele_displayed('#ap_email_login', timeout=15)
                await asyncio.sleep(random.uniform(1, 2))

                escritura_humana(page.ele('#ap_email_login'), numero)
                await asyncio.sleep(random.uniform(0.8, 1.5))

                page.ele('#continue').click()
                await asyncio.sleep(1.5)

                error_div = page.ele('#passkey-error-alert', timeout=4)
                if error_div:
                    print(f"⚠️ Número {numero} ya usado, reintentando...")
                    continue
                else:
                    print(f"✅ Número {numero} disponible!")
                    numero_exitoso = numero
                    user_data[user_id]["numero_exitoso"] = numero
                    break
            except Exception as e:
                print(f"❌ Error con número {numero}: {e}")
                continue

        if not numero_exitoso:
            return None  # Todos los números fallaron

        # Continuar con el registro
        passw = generar_password()
        user_data[user_id]["passw"] = passw

        page.ele('#intention-submit-button').click()
        await asyncio.sleep(1.6)

        escritura_humana(page.ele('#ap_customer_name'), generar_nombre())
        await asyncio.sleep(random.uniform(0.8, 1.5))

        escritura_humana(page.ele('#ap_password'), passw)
        await asyncio.sleep(random.uniform(0.5, 1))

        escritura_humana(page.ele('#ap_password_check'), passw)
        await asyncio.sleep(1)

        page.ele('#continue').click()
        page.set.blocked_urls([])
        await asyncio.sleep(1.6)

        # Resolver CAPTCHA
        print("[*] Resolviendo CAPTCHA...")
        solve_captcha(page, CAPSOLVER_API_KEY)

        # Esperar a que aparezca el campo de OTP
        if page.wait.ele_displayed('#cvf-input-code', timeout=60):
            time.sleep(3)
            print("[SUCCESS] ¡Pantalla de OTP detectada!")

       
            print("[+] Proceso Chrome suspendido - Sin consumo de proxy ni recursos")

            # Esperar a que el usuario envíe el OTP
            user_data[user_id]["event"].clear()  # Limpiar el evento
            try:
                await c.bot.send_message(
                    chat_id=user_id,
                    text="OTP REQUERIDO - ⏳ Esperando OTP... (Tiempo límite: 6 minutos)"
                )
                await asyncio.wait_for(user_data[user_id]["event"].wait(), timeout=360)  # ✅ Timeout de 5 minutos (300 segundos)
            except asyncio.TimeoutError:
                await c.bot.send_message(
                    chat_id=user_id,
                    text="⏰ **Tiempo de espera agotado.** El proceso fue cancelado por inactividad."
                )
                return None  # Termina la función si el tiempo se agota


            print("[+] Proceso Chrome reanudado")

            otp = user_data[user_id]["otp"]
            if otp:
                page.ele('#cvf-input-code').input(otp)
                page.ele('#cvf-submit-otp-button').click()
                await asyncio.sleep(4)

        # Rellenar dirección
        print("[*] Paso 1: Navegando y esperando generación de tokens (WAF/Akamai)...")
        page.get("https://www.amazon.com/a/addresses/add?ref=ya_address_book_add_button")

        # Espera activa para que el WAF de Amazon se cocine
        time.sleep(3) 

        direccion = generar_direccion_real()
        nombre = generar_nombre()
        street = direccion['calle']

        city = direccion['ciudad']
        state = direccion['estado']
        postal_code = direccion['zip']

        try:
            f_data = {
                'csrfToken': page.ele('@name=csrfToken').attr('value'),
                'widget_csrf': page.ele('@name=address-ui-widgets-csrfToken').attr('value'),
                'prev_token': page.ele('@name=address-ui-widgets-previous-address-form-state-token').attr('value'),
                'interaction_id': page.ele('@name=address-ui-widgets-address-wizard-interaction-id').attr('value'),
                'customer_id': page.ele('@name=address-ui-widgets-obfuscated-customerId').attr('value'),
                'form_time': page.ele('@name=address-ui-widgets-form-load-start-time').attr('value'),
                'click_id': page.ele('@name=address-ui-widgets-clickstream-related-request-id').attr('value')
            }
            
            # CAPTURA TOTAL: Aquí robamos TODO lo que el navegador ya validó
            cookies_navegador = {c['name']: c['value'] for c in page.cookies()}
            ua = page.user_agent
            
            # Verificamos si ya tenemos el WAF token en las cookies
            if 'aws-waf-token' in cookies_navegador:
                print("💎 AWS WAF Token detectado y capturado.")
            else:
                print("⚠️ WAF Token no encontrado en cookies base, se generará en el siguiente paso.")
                
        except Exception as e:
            print(f"❌ Error en extracción: {e}")
            browser.quit()

        print("[*] Pasando a TLS Pro (curl_cffi + chrome124)...")

        # 2. Motor TLS con Firma Real (JA3)
        # Usamos chrome124 ya que chrome128 no está mapeado aún, pero la firma es igual de efectiva
        session = requests.Session(impersonate="chrome124")
        session.cookies.update(cookies_navegador)

        headers_base = {
            'host': 'www.amazon.com',
            'user-agent': ua,
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'accept-language': 'en-US,en;q=0.9',
            'accept-encoding': 'gzip, deflate, br, zstd',
            
            # --- METADATOS DE SEGURIDAD CRÍTICOS (Client Hints) ---
            'sec-ch-ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"', # Ajusta los números si usas Chrome 128
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
        }

        # 3. PASO: AGREGAR DIRECCIÓN
        payload_address = {
            'csrfToken': f_data['csrfToken'],
            'address-ui-widgets-countryCode': 'US',
            'address-ui-widgets-enterAddressFullName': nombre, 
            'address-ui-widgets-enterAddressPhoneNumber': numero_exitoso, 
            'address-ui-widgets-enterAddressLine1': street,
            'address-ui-widgets-enterAddressCity': city,
            'address-ui-widgets-enterAddressStateOrRegion': state, 
            'address-ui-widgets-enterAddressPostalCode': postal_code,
            'address-ui-widgets-previous-address-form-state-token': f_data['prev_token'],
            'address-ui-widgets-csrfToken': f_data['widget_csrf'],
            'address-ui-widgets-form-load-start-time': f_data['form_time'],
            'address-ui-widgets-clickstream-related-request-id': f_data['click_id'],
            'address-ui-widgets-address-wizard-interaction-id': f_data['interaction_id'],
            'address-ui-widgets-obfuscated-customerId': f_data['customer_id'],
            'address-ui-widgets-clientName': 'YourAccountAddressBook',
            'address-ui-widgets-addressFormButtonText': 'save',
            'address-ui-widgets-enableAddressWizardForm': 'true',
        }

        print("[*] Guardando dirección...")
        session.post(
            'https://www.amazon.com/a/addresses/add?ref=ya_address_book_add_post',
            data=payload_address,
            headers={**headers_base, 'referer': 'https://www.amazon.com/a/addresses/add?ref=ya_address_book_add_button'},
            allow_redirects=False
        )
        # Extraer cookie
        print("[*] Calentando sesión para Akamai...")
        page.get('https://www.amazon.com/haul/store?ref_=nav_cs_hul_disb')
        time.sleep(1)

        # Petición a Wallet para forzar la actualización de at-main y sess-at-main
        res_wallet = session.get(
            'https://www.amazon.com/cpe/yourpayments/wallet',
            headers={**headers_base, 'referer': 'https://www.amazon.com/a/addresses'},
            timeout=15
        )

        if res_wallet.status_code == 200:
            # 5. EXTRACCIÓN FINAL (FULL STACK)
            final_cookies = session.cookies.get_dict()
            
            # Lista de cookies críticas que SÍ o SÍ deben estar para durar +50 usos
            # criticas = ['session-id', 'ubid-main', 'at-main', 'ak_bmsc', 'x-main', 'aws-waf-token']
            criticas = ['at-main', 'i18n-prefs', 'lc-main', 'sess-at-main', 'session-id-time', 'sst-main',
                        'ubid-main', 'session-id', 'session-token', 'x-main', 'csm-hit']
            
            encontradas = [c for c in criticas if c in final_cookies]
            
            cookie_final_str = "; ".join([f"{k}={v}" for k, v in final_cookies.items()])
            
            print("\n" + "="*80)
            print(f"📊 SALUD DE LA COOKIE: {len(encontradas)}/{len(criticas)} campos críticos encontrados")
            print("-" * 80)
            print(cookie_final_str)
            print("="*80)
            
            with open("cookie_inmortal_amazon.txt", "w") as f:
                f.write(cookie_final_str)
                print(f"[+] Guardada con éxito en cookie_inmortal_amazon.txt")
        else:
            print(f"❌ Falló el acceso a Wallet. Status: {res_wallet.status_code}")


        return cookie_final_str
    except Exception as e:
        print(f"Error: {e}")
        return None
    finally:
        browser.quit()
        if os.path.exists(perfil_dir):
            shutil.rmtree(perfil_dir)