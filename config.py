import asyncio
import os
import json
from dotenv import load_dotenv

# ================= LOAD .env =================
load_dotenv()

# ================= CONFIG =================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
if not TELEGRAM_TOKEN:
    raise ValueError("❌ TELEGRAM_TOKEN no está configurado en .env")

API_URL = os.getenv("API_URL", "http://127.0.0.1:5000")
PP_API_URL = os.getenv("PP_API_URL", "http://127.0.0.1:8000/check")
MONERIS_API_URL = os.getenv("MONERIS_API_URL", "http://127.0.0.1:8001/check")

ADMINS = [5651880136, 5133617831]

# ================= DATABASE PATHS =================
KEYS_FILE = os.getenv("KEYS_FILE", "data/keys.json")
GATES_CONFIG_FILE = os.getenv("GATES_CONFIG_FILE", "data/gates_config.json")
DATABASE_PATH = os.getenv("DATABASE_PATH", "data/database_apion.json")

# Crear carpeta data/ si no existe
os.makedirs("data", exist_ok=True)
os.makedirs("logs", exist_ok=True)

def load_gates_status():
    if os.path.exists(GATES_CONFIG_FILE):
        with open(GATES_CONFIG_FILE, "r") as f:
            return json.load(f)
    # Valores por defecto si el archivo no existe
    return {"pp": True, "gt": True, "pfw": True, "mn": False, 
            "wm": True, "ka": True, "amo": True, "gencookieca": True,
              "gencookiemx": True, "gencookieus": True, "genmanusa": True,
                "genmanca": True, "genmanmx": True, "stp": True, "clo": True, "neonet": True,"braintree1": True}

def save_gates_status(status_dict):
    with open(GATES_CONFIG_FILE, "w") as f:
        json.dump(status_dict, f, indent=4)

# Esta variable ahora se carga del archivo al iniciar
GATES_STATUS = load_gates_status()


# --- MAPEOS ADICIONALES PARA BINS.SU ---
V_MAP = {
    "VISA": "Visa", "MC": "MASTERCARD", "MASTERCARD": "MASTERCARD", 
    "AMEX": "AMERICAN EXPRESS", "AMERICAN": "AMERICAN EXPRESS",
    "MAESTRO": "Maestro", "DISCOVER": "Discover", "DCI": "DCI", 
    "JCB": "JCB", "UNIONPAY": "CHINA UNION PAY"
}

L_MAP = {
    "CLASSIC": "Classic/Standard", "STANDARD" "ENHANCED": "Classic/Standard",
    "GOLD": "Gold/Prem", "PREM": "Gold/Prem", "PLATINUM": "Platinum", 
    "SIGNATURE": "Signature", "ELECTRON": "Electron", "PREPAID": "Prepaid",
    "BUSINESS": "Business", "CORPORATE": "Corporate", "INFINITE": "Infinite",
    "CASH": "Cash", "PURCHASING": "Purchasing", "VIRTUAL": "Virtual"
}

T_MAP = {"CREDIT": "Credit", "DEBIT": "Debit", "CHARGE": "CHARGE CARD"}