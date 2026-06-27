import re
import uuid
import time
import random
import requests
import faker

Faker = faker.Faker()

CAPSOLVER_KEY = "CAP-E628130ED40FD0A0BBC180D0C7822D2C3B13D9BAAE3152A7F7A15F473A4F852F"
STRIPE_PK     = "pk_live_cSsXS3MNe8Y7K23zeUMkuvK5"
STRIPE_UA     = "stripe.js/78ef418"

session = requests.Session()


# ─── helpers ──────────────────────────────────────────────────────────────────

def gen_stripe_id():
    """UUID-v4 + 6 hex chars, igual al formato que genera stripe.js."""
    return str(uuid.uuid4()) + ''.join(random.choices('0123456789abcdef', k=6))


def _extract_auth(html):
    m = re.search(r'name="authenticity_token"[^>]*value="([^"]+)"', html)
    return m.group(1) if m else None

def _extract_csrf(html, fallback=None):
    m = re.search(r'<meta[^>]*name="csrf-token"[^>]*content="([^"]+)"', html)
    return m.group(1) if m else fallback


# ─── paso 1: página de registro ───────────────────────────────────────────────

def getautenticity():
    url = "https://mealplans.cooksmarts.com/trial_subscription/new?signup=true&plan=annually"
    req = session.get(url=url)
    html = req.text
    with open("pruebastrie1.html", "w", encoding="utf-8") as f:
        f.write(html)

    auth_token = _extract_auth(html)
    csrf_token = _extract_csrf(html, fallback=auth_token)
    print(f"Auth token : {auth_token}")
    print(f"CSRF token : {csrf_token}")
    return auth_token, csrf_token


# ─── paso 2: resolver reCAPTCHA v2 ────────────────────────────────────────────

def sendtask():
    res = requests.post(
        "https://api.capsolver.com/createTask",
        headers={"Content-Type": "application/json"},
        json={
            "clientKey": CAPSOLVER_KEY,
            "task": {
                "type": "ReCaptchaV2TaskProxyLess",
                "websiteURL": "https://mealplans.cooksmarts.com/trial_subscription/new?signup=true&plan=annually",
                "websiteKey": "6Ldqv7IUAAAAANVx5Ai9pFK7LL-AmjiSK4dk7KAl",
            },
        },
    )
    data = res.json()
    task_id = data["taskId"]
    print(f"Capsolver taskId: {task_id}")
    return task_id


def gettaskresult(taskid):
    while True:
        res = requests.post(
            "https://api.capsolver.com/getTaskResult",
            headers={"Content-Type": "application/json"},
            json={"clientKey": CAPSOLVER_KEY, "taskId": taskid},
        )
        data = res.json()
        status = data.get("status")
        print(f"Capsolver status: {status}")
        if status == "ready":
            return data["solution"]["gRecaptchaResponse"]
        elif status == "failed":
            print(f"Capsolver failed: {data}")
            return None
        time.sleep(3)


# ─── paso 3: registro de usuario ──────────────────────────────────────────────

def gettrial(auttoken, csrf_token, name, apellido, email, passw, captcha):
    req = session.post(
        "https://mealplans.cooksmarts.com/trial_subscription",
        headers={
            'accept': 'text/vnd.turbo-stream.html, text/html, application/xhtml+xml',
            'accept-language': 'en-US,en;q=0.9,es;q=0.8',
            'cache-control': 'no-cache',
            'content-type': 'application/x-www-form-urlencoded;charset=UTF-8',
            'dpr': '1.25',
            'origin': 'https://mealplans.cooksmarts.com',
            'pragma': 'no-cache',
            'priority': 'u=1, i',
            'referer': 'https://mealplans.cooksmarts.com/trial_subscription/new?signup=true&plan=annually',
            'sec-ch-ua': '"Google Chrome";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36',
            'viewport-width': '788',
            'x-csrf-token': csrf_token,
            'x-turbo-request-id': str(uuid.uuid4()),
        },
        data={
            "authenticity_token": auttoken,
            "plan": "annually",
            "user[ga_client_id]": "",
            "user[first_name]": name,
            "user[last_name]": apellido,
            "user[email]": email,
            "user[password]": passw,
            "user[password_confirmation]": passw,
            "g-recaptcha-response": captcha,
            "commit": "Next",
        },
    )
    print(f"Status gettrial: {req.status_code}")
    with open("gettrial.html", "w", encoding="utf-8") as f:
        f.write(req.text)


# ─── paso 4: página de pago (extrae nuevo authenticity_token) ─────────────────

def getpaymentpage():
    req = session.get("https://mealplans.cooksmarts.com/trial_subscription/payment?plan=annually")
    html = req.text
    with open("checktrial.html", "w", encoding="utf-8") as f:
        f.write(html)

    auth_token = _extract_auth(html)
    print(f"Auth token pago: {auth_token}")
    return auth_token


# ─── paso 5: crear token Stripe ───────────────────────────────────────────────

def getstripetoken(cc, mes, ano, cvv, postal):
    data = {
        "time_on_page":       str(random.randint(60000, 900000)),
        "guid":               gen_stripe_id(),
        "muid":               gen_stripe_id(),
        "sid":                gen_stripe_id(),
        "key":                STRIPE_PK,
        "payment_user_agent": STRIPE_UA,
        "card[number]":       cc,
        "card[exp_month]":    mes,
        "card[exp_year]":     ano,
        "card[cvc]":          cvv,
        "card[address_zip]":  postal,
    }
    req = requests.post(
        "https://api.stripe.com/v1/tokens",
        headers={
            "accept": "application/json",
            "accept-language": "en-US",
            "cache-control": "no-cache",
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://js.stripe.com",
            "pragma": "no-cache",
            "priority": "u=1, i",
            "referer": "https://js.stripe.com/",
            "sec-ch-ua": '"Google Chrome";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36",
        },
        data=data,
        timeout=30,
    )
    res = req.json()
    token_id = res.get("id")
    error = res.get("error", {}).get("message")
    print(f"Stripe token: {token_id or error}")
    return token_id, error



def pay(auttoken,stoken):
    url = "https://mealplans.cooksmarts.com/trial_subscription/charge"

    headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'es-US,es;q=0.9',
    'cache-control': 'no-cache',
    'content-type': 'application/x-www-form-urlencoded',
    'origin': 'https://mealplans.cooksmarts.com',
    'pragma': 'no-cache',
    'priority': 'u=0, i',
    'referer': 'https://mealplans.cooksmarts.com/trial_subscription/payment?plan=annually',
    'sec-ch-ua': '"Google Chrome";v="149", "Chromium";v="149", "Not)A;Brand";v="24"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36',
    }

    data = {
        'authenticity_token': auttoken,
        'plan': 'annually',
        'version': '2023',
        'coupon': '',
        'stripe_token': stoken,
    }


    req4 = session.post(url=url, headers=headers,data=data)

    html = req4.text
    with open("pay.html", "w", encoding="utf-8") as f:
        f.write(html)


def checksub():
    url = "https://mealplans.cooksmarts.com/welcome"

    req1 = session.get(url=url)
    html = req1.text
    with open("checksub.html", "w", encoding="utf-8") as f:
        f.write(html)


name     = "Mar"
apellido = "Cass"
email    = "marcas3434@gmail.com"
passw    = "rossaQ333"
cc       = "4536895908928870"
mes      = "08"
ano      = "2030"
cvv      = "558"
postal   = "68155"

auttoken, csrf_token = getautenticity()
taskid  = sendtask()
captcha = gettaskresult(taskid)

gettrial(auttoken, csrf_token, name, apellido, email, passw, captcha)

pay_auth = getpaymentpage()
stoken = getstripetoken(cc, mes, ano, cvv, postal)
pay(pay_auth,stoken)
checksub()

