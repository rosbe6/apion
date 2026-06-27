from DrissionPage import Chromium, ChromiumOptions
from amz.datos import generar_nombre, generar_direccion_real, generar_password, generar_email
from amz.datos import obtener_numero_mx, esperar_sms, saldo_numeros, cancelar_numero
from amz.awf import get_captcha_hint, get_canvas_base64, split_canvas_into_9, send_to_capsolver, click_captcha_cells, solve_captcha, CAPSOLVER_API_KEY
from browser_utils import get_chromium_or_env

import random
import string
import os
import time
import shutil
import uuid
import psutil
from dotenv import load_dotenv

load_dotenv()

def bytes_usados_por_chrome():
    """Retorna MB transferidos por el proceso Chrome"""
    try:
        # En Windows puedes usar el monitor de red de psutil
        net_antes = psutil.net_io_counters()
        return net_antes
    except:
        return None





## Función para simular escritura humana

def escritura_humana(elemento, texto):
    for caracter in texto:
        elemento.input(caracter)
        time.sleep(random.uniform(0.07, 0.35))


### Funcion para generar instancia de chromium con perfil temporal y extensión cargada

def registro_high_score_mx():
    print("=== Iniciando Módulo: Registro con Sesión Única y Aislada ===")

    # 1. Configuración de Rutas y Sesión Única
    base_path = os.path.dirname(os.path.abspath(__file__))

    # Creamos un ID único para que esta sesión sea irreconocible de la anterior
    session_id = f"session_{uuid.uuid4().hex[:10]}"
    perfil_dir = os.path.join(base_path, "temp_profiles", session_id)
    os.makedirs(perfil_dir, exist_ok=True)

    # 2. Configuración de Opciones del Navegador
    chromium_path = get_chromium_or_env()
    print(f"[*] Usando Chromium: {chromium_path}")

    co = ChromiumOptions()
    co.set_browser_path(chromium_path)
    
    # AISLAMIENTO: Definir la carpeta de datos de usuario única
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



    # 4. Flags de Anonimato y Proxy
    proxy_server = os.getenv("AMAZON_PROXY", "p.webshare.io:10000")
    print(f"[*] Usando proxy: {proxy_server}")
    co.set_proxy(f"http://{proxy_server}")
    
    co.set_argument('--force-timezone=America/Cancun')

    co.set_argument('--no-first-run')
    co.set_argument('--lang=es-MX')
    co.set_argument('--disable-blink-features=AutomationControlled')
    co.set_argument('--disable-webrtc')
    co.set_argument('--disable-dev-shm-usage')
    co.set_argument('--disable-extensions')
    co.set_pref('intl.accept_languages', 'es-MX,es;q=0.9')  # Preferencias de idioma





    def bloquear_recursos_no_esenciales(page):
        """Bloquea imágenes, fuentes y recursos no esenciales para ahorrar ancho de banda."""
        page.set.blocked_urls([
            '*.png', '*.jpg', '*.jpeg', '*.gif', '*.webp', '*.svg', '*.ico',
            '*.woff', '*.woff2', '*.ttf', '*.eot',
            '*analytics*', '*ads*', '*doubleclick*',
            '*optimizationguide-pa.googleapis.com*'
        ])
 
    co.auto_port()

    # Iniciar Navegador


    #### Aca comienza a correr la instancia de Chromium con el perfil temporal y la extensión cargada. Todo lo que se haga aquí dentro quedará aislado en esa carpeta de perfil, y al finalizar se borra toda la carpeta para no dejar rastro.
    net_inicio = psutil.net_io_counters()


    browser = Chromium(co)
    
    try:
        page = browser.latest_tab
        bloquear_recursos_no_esenciales(page)

        
        print(f"[*] Perfil temporal activo: {session_id}")
        print("[*] Verificando panel de extensiones...")

        # Aqui va el codigo qud borre
        
        #aqui termina

         # 5. Navegación a Amazon
        url_inicio = "https://www.amazon.com.mx/wallet"
        
        print("[*] Navegando a Amazon...")
        page.get(url_inicio)

        print("paso1")
        
        MAX_INTENTOS = 5
        intento = 0

        # Aca comienza el proceso de llenado
        print("paso2")

        print("Tu saldo de números es:", saldo_numeros())

        while intento < MAX_INTENTOS:
            datosnumyid = obtener_numero_mx()
            if datosnumyid is None:
                print("❌ No se pudo obtener el número.")
                return
          
            numero = datosnumyid['numero']
            order_id = datosnumyid['order_id']
            print(f"✅ Numero obtenido: {numero} | Order ID: {order_id}")

            page.get(url_inicio)
            page.wait.ele_displayed('#ap_email_login', timeout=15)
            time.sleep(random.uniform(1, 2))

            escritura_humana(page.ele('#ap_email_login'), f"+{numero}")
            time.sleep(random.uniform(0.8, 1.5))

            page.ele('#continue').click()
            time.sleep(1.5)

            error_div = page.ele('#passkey-error-alert', timeout=4)
            if error_div:
                print(f"⚠️ Número ya usado, reintentando... (intento {intento + 1}/{MAX_INTENTOS})")
                intento += 1
                continue  # Vuelve al inicio del while con un número nuevo

            

            print("✅ Número aceptado, continuando...")
            break


        else:
            print("❌ Se agotaron los intentos, todos los números ya tenían cuenta.")
            return




       
        print("paso2.5")
        passw = generar_password()

        page.ele('#intention-submit-button').click()
        #.sleep(3)

        escritura_humana(page.ele('#ap_customer_name'), generar_nombre())
        time.sleep(random.uniform(0.8, 1.5))

        

        escritura_humana(page.ele('#ap_password'), passw)
        time.sleep(random.uniform(0.5, 1))

        escritura_humana(page.ele('#ap_password_check'), passw)
        time.sleep(1)

        print("Contraseña generada: ", passw)

        print("[>] Click en continuar...")
        page.ele('#continue').click()
        page.set.blocked_urls([])
        time.sleep(1.6)

        
        ### Aca se espera resolver el captcha y recibir el otp
        # # 7. Espera de Captcha / OTP
        print("[*] Verificando y resolviendo captcha...")
        time.sleep(3)
        solve_captcha(page, CAPSOLVER_API_KEY)


        try:
            textwsp = page.wait.ele_displayed('#whatsapp_header', timeout=4)
            if textwsp:
                print("✅ WhatsApp detectado, cambiando a SMS...")
                try:
                    # Esperar a que el botón esté disponible
                    sms_button = page.wait.ele_displayed('#secondary_channel_button', timeout=5)
                    sms_button.click()
                    time.sleep(1.5)
                except Exception as e:
                    print(f"⚠️ No se pudo hacer clic en el botón de SMS: {e}")
        except Exception as e:
            print(f"⚠️ No se detectó opción de WhatsApp: {e}")

        # Verificar si aparece el campo de OTP (SMS) (solo una vez, sin duplicación)
        if page.wait.ele_displayed('#cvf-input-code', timeout=60):
            print("[SUCCESS] ¡Pantalla de OTP detectada!")
            try:
                otp = esperar_sms(order_id)
                status = otp.get('codigo')  # Usar .get() para evitar KeyError
                if status:
                    print(f"OTP recibido: {status}")
                    page.ele('#cvf-input-code').input(status)
                    page.ele('#cvf-submit-otp-button').click()
                    time.sleep(4)
                else:
                    print(f"❌ No se recibió OTP. Respuesta: {otp}")
            except Exception as e:
                print(f"❌ Error al procesar el OTP: {e}")
        else:
            print("⚠️ No se detectó el campo de OTP en 60 segundos.")





    
        

        
        ### Aca comienza    el proceso de llenado de dirección
        bloquear_recursos_no_esenciales(page)

        direccion = generar_direccion_real()

        street = direccion['calle']
        nombre = generar_nombre()
        city = direccion['ciudad']
        state = direccion['estado']
        postal_code = direccion['zip']
        
        print(f"Generando dirección coherente: {street}, {city}, {state}, {postal_code}")

       

        page.get("https://www.amazon.com.mx/a/addresses/add?ref=ya_address_book_add_button")
        time.sleep(1)  # Espera para que la página cargue completamente

        print("[*] Llenando formulario de dirección...")

        page.ele('#address-ui-widgets-countryCode').click()
        time.sleep(0.5)
        usa_option = page.ele('#address-ui-widgets-countryCode-dropdown-nativeId_64')
        usa_option.click()  # Haz clic en la opción de USA
        time.sleep(2)  

        escritura_humana(page.ele('#address-ui-widgets-enterAddressFullName'), nombre)
        time.sleep(0.5)

        escritura_humana(page.ele('#address-ui-widgets-enterAddressPhoneNumber'), "+15815951108")
        time.sleep(0.5)


        escritura_humana(page.ele('#address-ui-widgets-enterAddressLine1'), str(street))
        time.sleep(0.5)

        print("Street rellenado")

        escritura_humana(page.ele('#address-ui-widgets-enterAddressCity'), str(city))
        time.sleep(0.5)

        print("City rellenado")

        page.ele('#address-ui-widgets-enterAddressStateOrRegion-dropdown-nativeId').select(state)
        time.sleep(0.5)
        print("State rellenado")

        escritura_humana(page.ele('#address-ui-widgets-enterAddressPostalCode'), str(postal_code))
        time.sleep(0.5)
        print("Postal Code rellenado")

        nombre_field = page.ele('#address-ui-widgets-enterAddressFullName', timeout=10)
        nombre_field.clear()  

        escritura_humana(page.ele('#address-ui-widgets-enterAddressFullName'), nombre)
        time.sleep(0.5)


        page.ele('#address-ui-widgets-form-submit-button-announce').click()
        time.sleep(10)
        ### Aqui inicia la funcion de extraer la cookie de session-id

        page.listen.start('wallet')
        print("Navegando a Amazon Wallet...")
        

        page.get("https://www.amazon.com.mx/cpe/yourpayments/wallet")

        print("Esperando estabilización de carga (5s)...")
        time.sleep(2.5)


        docs_encontrados = []
        start_time = time.time()

        # 2. Capturamos los requests durante 15 segundos o hasta tener 3
        while time.time() - start_time < 15:
            res = page.listen.wait(timeout=1)
            if res:
                docs_encontrados.append(res)
                print(f"📦 Capturado documento wallet #{len(docs_encontrados)} | Tipo: {res.request.method}")
                
                if len(docs_encontrados) >= 3:
                    break

        cookie_final = None
        doc_indice = 0

        print("\nRevisando headers...")
        
        for i, doc in enumerate(docs_encontrados):
            headers = doc.request.headers
            c = headers.get('Cookie') or headers.get('cookie')
            
            if c and 'session-id=' in c:
                # LOCALIZAR Y RECORTAR:
                # Buscamos dónde empieza 'session-id='
                posicion = c.find('session-id=')
                # Cortamos el string desde esa posición hasta el final
                cookie_limpia = c[posicion:]
                
                cookie_final = cookie_limpia
                doc_indice = i + 1
                break # Usamos el primero que cumpla la condición

        if cookie_final:
            print("\n" + "="*60)
            print(f"✅ COOKIE EXTRAÍDA Y LIMPIA (Doc {doc_indice}):")
            print("-" * 60)
            print(cookie_final)
            print("="*60)
            return cookie_final
        else:
            print("\n❌ No se encontró una cookie válida que contenga 'session-id'.")
            return None





    except Exception as e:

        browser.quit()  # Cerramos el navegador en caso de error para evitar procesos colgados
        print(f"Error durante la ejecución:")

    
    
    finally:
        print("[*] Finalizando y limpiando rastros...")
        print("Tu saldo de números es:", saldo_numeros())
        browser.quit() # Cerramos el navegador primero

        net_fin = psutil.net_io_counters()
        enviados = (net_fin.bytes_sent - net_inicio.bytes_sent) / 1024 / 1024
        recibidos = (net_fin.bytes_recv - net_inicio.bytes_recv) / 1024 / 1024
        print(f"📊 Datos enviados:   {enviados:.2f} MB")
        print(f"📊 Datos recibidos: {recibidos:.2f} MB")
        print(f"📊 Total:           {enviados + recibidos:.2f} MB")

        
        # Pausa para asegurar que Chrome liberó los archivos de la carpeta
        time.sleep(2)
        
        if os.path.exists(perfil_dir):
            try:
                shutil.rmtree(perfil_dir)
                print(f"[+] Carpeta de sesión {session_id} eliminada.")
            except Exception as e:
                print(f"[!] No se pudo eliminar la carpeta temporal: {e}")

if __name__ == "__main__":
    # Crear carpeta base para perfiles si no existe
    if not os.path.exists("temp_profiles"):
        os.makedirs("temp_profiles")
    
