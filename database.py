# database.py
import json
import os
import time
import asyncio
from config import KEYS_FILE, DATABASE_PATH

antispam_db = {}

# Configuración de IDs
OWNER_ID = 5651880136
ADMINS = [5133617831]

# Usar rutas configuradas (soportan relativas y absolutas)
FILE_KEYS = KEYS_FILE
FILE_EXTRAS = DATABASE_PATH
FILE_CHATS = "data/chats.json"

DB_LOCK = asyncio.Lock()
def load_users():
    """Carga la lista de usuarios desde users.json."""
    if not os.path.exists(FILE_KEYS):
        return {"users": []}
    with open(FILE_KEYS, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return {"users": []}


def get_all_users():
    """Devuelve la lista de todos los usuarios registrados."""
    # Intentamos leer el archivo de keys y extraer todos los IDs de usuario
    # que puedan aparecer en las secciones "usuarios" o en cada key bajo "user".
    if not os.path.exists(FILE_KEYS):
        return []
    try:
        with open(FILE_KEYS, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        return []

    users_set = set()
    # Desde la sección 'usuarios' (claves del dict)
    for uid in data.get('usuarios', {}).keys():
        try:
            users_set.add(int(uid))
        except:
            users_set.add(uid)

    # Desde la lista 'keys' (campo 'user' en cada entrada)
    for k in data.get('keys', []):
        u = k.get('user')
        if u is not None:
            users_set.add(u)

    return list(users_set)


# --- FUNCIONES PARA KEYS Y USUARIOS ---
async def load_keys():
    async with DB_LOCK:
        if not os.path.exists(FILE_KEYS):
            base = {"keys": [], "usuarios": {}}
            with open(FILE_KEYS, "w") as f:
                json.dump(base, f, indent=4)
            return base
        with open(FILE_KEYS, "r") as f:
            try:
                return json.load(f)
            except:
                return {"keys": [], "usuarios": {}}

async def save_keys(data):
    async with DB_LOCK:
        with open(FILE_KEYS, "w") as f:
            json.dump(data, f, indent=4)

# --- FUNCIÓN EXCLUSIVA PARA EXTRAS ---
async def load_extras():
    # Esta solo lee, no necesita bloqueo de escritura usualmente
    if not os.path.exists(FILE_EXTRAS):
        return {}
    with open(FILE_EXTRAS, "r") as f:
        try:
            return json.load(f)
        except:
            return {}

def get_rango(user_id):
    if user_id == OWNER_ID: return 3
    if os.path.exists(FILE_KEYS):
        try:
            with open(FILE_KEYS, "r") as f:
                data = json.load(f)
                user_str = str(user_id)
                u_data = data.get("usuarios", {}).get(user_str, {})
                rango = u_data.get("rango", "FREE")
                return {"OWNER": 3, "ADMIN": 2, "PREMIUM": 1}.get(rango, 0)
        except: return 0
    return 0


# --- CHAT REGISTRY ---
def load_chats():
    if not os.path.exists(FILE_CHATS):
        return {"chats": []}
    try:
        with open(FILE_CHATS, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"chats": []}

def save_chats(data):
    with open(FILE_CHATS, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)

def add_chat(chat_id):
    """Añade un chat (usuario o grupo) a la lista persistente."""
    data = load_chats()
    chats = data.get('chats', [])
    if chat_id not in chats:
        chats.append(chat_id)
        data['chats'] = chats
        save_chats(data)

def get_all_chats():
    data = load_chats()
    return data.get('chats', [])

def get_info_usuario(user_id):
    if os.path.exists(FILE_KEYS):
        try:
            with open(FILE_KEYS, "r") as f:
                data = json.load(f)
                user_str = str(user_id)
                return data.get("usuarios", {}).get(user_str, {})
        except: return {}
    return {}

def tengo_creditos(user_id):
    if user_id == OWNER_ID: return True
    elif user_id in [5133617831]: return True
    info = get_info_usuario(user_id)
    return info.get("credits", 0) > 0

def usar_credito(user_id):
    """
    Descuenta 1 crédito del usuario.
    :param user_id: ID del usuario en Telegram.
    :return: True si se descontó el crédito, False si no.
    """
    user_str = str(user_id)

    # El OWNER no gasta créditos
    if user_id == OWNER_ID:
        return True
    elif user_id in [5133617831]:
        return True

    # Leer archivo directamente (versión síncrona)
    if not os.path.exists(FILE_KEYS):
        print(f"❌ Archivo {FILE_KEYS} no existe.")
        return False

    with open(FILE_KEYS, "r") as f:
        try:
            data = json.load(f)
        except:
            print(f"❌ Error al leer {FILE_KEYS}.")
            return False

    u_data = data.get("usuarios", {}).get(user_str, {})
    
    current_credits = u_data.get("credits", 0)
    if current_credits > 0:
        u_data["credits"] = current_credits - 1
        # Guardar directamente (versión síncrona)
        with open(FILE_KEYS, "w") as f:
            json.dump(data, f, indent=4)
        print(f"✅ Crédito descontado al usuario {user_id}. Créditos restantes: {u_data['credits']}")
        return True
    else:
        print(f"❌ El usuario {user_id} no tiene créditos.")
        return False
    
def usar_creditoman(user_id):
    """
    Descuenta 1 crédito del usuario.
    :param user_id: ID del usuario en Telegram.
    :return: True si se descontó el crédito, False si no.
    """
    user_str = str(user_id)

    # El OWNER no gasta créditos
    if user_id == OWNER_ID:
        return True
    elif user_id in [5133617831]:
        return True

    # Leer archivo directamente (versión síncrona)
    if not os.path.exists(FILE_KEYS):
        print(f"❌ Archivo {FILE_KEYS} no existe.")
        return False

    with open(FILE_KEYS, "r") as f:
        try:
            data = json.load(f)
        except:
            print(f"❌ Error al leer {FILE_KEYS}.")
            return False

    u_data = data.get("usuarios", {}).get(user_str, {})
    
    current_credits = u_data.get("credits", 0)
    if current_credits > 0:
        u_data["credits"] = current_credits - 0.25
        # Guardar directamente (versión síncrona)
        with open(FILE_KEYS, "w") as f:
            json.dump(data, f, indent=4)
        print(f"✅ 0.25 CRDS descontado al usuario {user_id}. Créditos restantes: {u_data['credits']}")
        return True
    else:
        print(f"❌ El usuario {user_id} no tiene créditos.")
        return False
    

def usar_creditous(user_id):
    """
    Descuenta 3 créditos del usuario.
    :param user_id: ID del usuario en Telegram.
    :return: True si se descontaron los créditos, False si no.
    """
    user_str = str(user_id)

    # El OWNER no gasta créditos
    if user_id == OWNER_ID:
        return True

    # Leer archivo directamente (versión síncrona)
    if not os.path.exists(FILE_KEYS):
        print(f"❌ Archivo {FILE_KEYS} no existe.")
        return False

    with open(FILE_KEYS, "r") as f:
        try:
            data = json.load(f)
        except:
            print(f"❌ Error al leer {FILE_KEYS}.")
            return False

    u_data = data.get("usuarios", {}).get(user_str, {})
    
    current_credits = u_data.get("credits", 0)
    if current_credits > 0 and current_credits >= 3:
        u_data["credits"] = current_credits - 3
        # Guardar directamente (versión síncrona)
        with open(FILE_KEYS, "w") as f:
            json.dump(data, f, indent=4)
        print(f"✅ 3 Créditos descontados al usuario {user_id}. Créditos restantes: {u_data['credits']}")
        return True
    else:
        print(f"❌ El usuario {user_id} no tiene créditos.")
        return False

def quitar_creditos(user_id, cantidad, all):
    """
    Descuenta una cantidad específica de créditos del usuario.
    :param user_id: ID del usuario en Telegram.
    :param cantidad: Número de créditos a descontar.
    :return: True si se descontaron los créditos, False si no.
    """
    user_str = str(user_id)

    # El OWNER no gasta créditos
    if user_id == OWNER_ID:
        return True
    
    if user_id in [5133617831]:
        return True

    # Leer archivo directamente (versión síncrona)
    if not os.path.exists(FILE_KEYS):
        print(f"❌ Archivo {FILE_KEYS} no existe.")
        return False

    with open(FILE_KEYS, "r") as f:
        try:
            data = json.load(f)
        except:
            print(f"❌ Error al leer {FILE_KEYS}.")
            return False

    u_data = data.get("usuarios", {}).get(user_str, {})
    
    current_credits = u_data.get("credits", 0)
    if current_credits > 0 and current_credits >= cantidad:
        u_data["credits"] = current_credits - cantidad
        # Guardar directamente (versión síncrona)
        with open(FILE_KEYS, "w") as f:
            json.dump(data, f, indent=4)
        print(f"✅ {cantidad} Créditos descontados al usuario {user_id}. Créditos restantes: {u_data['credits']}")
        return True
    if all and current_credits > 0:
        u_data["credits"] = 0
        # Guardar directamente (versión síncrona)
        with open(FILE_KEYS, "w") as f:
            json.dump(data, f, indent=4)
        print(f"✅ Todos los créditos descontados al usuario {user_id}. Créditos restantes: 0")
        return True
    else:
        print(f"❌ El usuario {user_id} no tiene suficientes créditos.")
        return False

def obtener_rango(user_id):
    try:
        with open('keys.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Convertimos ID a string porque en el JSON están como "12345"
        user_id_str = str(user_id)
        
        # Buscamos al usuario dentro de la sección "usuarios"
        usuarios = data.get("usuarios", {})
        
        if user_id_str in usuarios:
            return usuarios[user_id_str].get("rango", "FREE")
        
        return "FREE" # Si el usuario no existe en el JSON
    except Exception as e:
        print(f"Error al leer keys.json: {e}")
        return "FREE"

def check_antispam_vbv(user_id, owner_id, admins_list):
    """
    Función maestra para llamar antes de cualquier comando.
    Retorna (True, 0) si puede pasar.
    Retorna (False, tiempo) si debe esperar.
    """
    now = time.time()
    
    # 1. Los jefes no tienen antispam
    if user_id == owner_id or user_id in admins_list:
        return True, 0

    # 2. Llamamos a tu función para ver el rango
    rango = obtener_rango(user_id)
    
    # 3. Definimos segundos según rango
    cooldown = 20 if rango == "PREMIUM" else 30
    
    # 4. Cálculo de tiempo restante
    last_time = antispam_db.get(user_id, 0)
    tiempo_restante = int(last_time + cooldown - now)

    if tiempo_restante > 0:
        return False, tiempo_restante

    # 5. Si pasó, actualizamos el último uso
    antispam_db[user_id] = now
    return True, 0


def check_antispam(user_id, owner_id, admins_list):
    """
    Función maestra para llamar antes de cualquier comando.
    Retorna (True, 0) si puede pasar.
    Retorna (False, tiempo) si debe esperar.
    """
    now = time.time()
    
    # 1. Los jefes no tienen antispam
    if user_id == owner_id or user_id in admins_list:
        return True, 0

    # 2. Llamamos a tu función para ver el rango
    rango = obtener_rango(user_id)
    
    # 3. Definimos segundos según rango
    cooldown = 30 if rango == "PREMIUM" else 60
    
    # 4. Cálculo de tiempo restante
    last_time = antispam_db.get(user_id, 0)
    tiempo_restante = int(last_time + cooldown - now)

    if tiempo_restante > 0:
        return False, tiempo_restante

    # 5. Si pasó, actualizamos el último uso
    antispam_db[user_id] = now
    return True, 0


def esbin(bin):
    """
    Valida que el BIN sea sólo números y tenga al menos 6 dígitos.
    Devuelve True si es válido, False en caso contrario.
    """
    try:
        b = str(bin).strip()
    except Exception:
        return False

    if not b.isdigit() or len(b) < 6:
        return False

    return True
