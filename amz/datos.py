from faker import Faker
import random_address
import requests
import time
import os
from dotenv import load_dotenv

load_dotenv()

# Instancia para datos personales
fake = Faker('en_US')


def generar_nombre():
    return fake.name()

def generar_email():
    return fake.email()

def generar_password():
    return fake.password(
        length=12,
        special_chars=True,
        digits=True,
        upper_case=True,
        lower_case=True
    )

import random_address

# diccionario estados USA
ESTADOS_USA = {
    "AL": "Alabama",
    "AK": "Alaska",
    "AZ": "Arizona",
    "AR": "Arkansas",
    "CA": "California",
    "CO": "Colorado",
    "CT": "Connecticut",
    "DE": "Delaware",
    "FL": "Florida",
    "GA": "Georgia",
    "HI": "Hawaii",
    "ID": "Idaho",
    "IL": "Illinois",
    "IN": "Indiana",
    "IA": "Iowa",
    "KS": "Kansas",
    "KY": "Kentucky",
    "LA": "Louisiana",
    "ME": "Maine",
    "MD": "Maryland",
    "MA": "Massachusetts",
    "MI": "Michigan",
    "MN": "Minnesota",
    "MS": "Mississippi",
    "MO": "Missouri",
    "MT": "Montana",
    "NE": "Nebraska",
    "NV": "Nevada",
    "NH": "New Hampshire",
    "NJ": "New Jersey",
    "NM": "New Mexico",
    "NY": "New York",
    "NC": "North Carolina",
    "ND": "North Dakota",
    "OH": "Ohio",
    "OK": "Oklahoma",
    "OR": "Oregon",
    "PA": "Pennsylvania",
    "RI": "Rhode Island",
    "SC": "South Carolina",
    "SD": "South Dakota",
    "TN": "Tennessee",
    "TX": "Texas",
    "UT": "Utah",
    "VT": "Vermont",
    "VA": "Virginia",
    "WA": "Washington",
    "WV": "West Virginia",
    "WI": "Wisconsin",
    "WY": "Wyoming"
}

ABREVIACIONES = {
    "Street": "St",
    "Avenue": "Ave",
    "Boulevard": "Blvd",
    "Road": "Rd",
    "Drive": "Dr",
    "Lane": "Ln",
    "Court": "Ct",
    "Place": "Pl",
    "Parkway": "Pkwy",
    "Circle": "Cir",
    "Terrace": "Ter",
}


def abreviar_direccion(calle):

    for original, corto in ABREVIACIONES.items():

        calle = calle.replace(original, corto)

    return calle

def generar_direccion_real():

    dir_real = random_address.real_random_address()

    estado_abreviado = dir_real.get('state')

    estado_completo = ESTADOS_USA.get(
        estado_abreviado,
        estado_abreviado
    )

    calle = dir_real.get('address1')

    # aplicar abreviaciones
    calle = abreviar_direccion(calle)

    return {
        "calle": calle,
        "ciudad": dir_real.get('city'),
        "estado": estado_completo,
        "zip": dir_real.get('postalCode'),
    }





direccion = generar_direccion_real()

# País codes para SMS
USA = "187"
CA = "36"
MX = "54"

# Cargar API keys desde .env
API_KEY = os.getenv("GRIZZLYSMS_API_KEY", "")
CAPSOLVER_API_KEY = os.getenv("CAPSOLVER_API_KEY", "")

if not API_KEY:
    raise ValueError("❌ GRIZZLYSMS_API_KEY no configurado en .env")
if not CAPSOLVER_API_KEY:
    raise ValueError("❌ CAPSOLVER_API_KEY no configurado en .env")

def obtener_numero_us():
    url = f"https://api.grizzlysms.com/stubs/handler_api.php?api_key={API_KEY}&action=getNumber&service=am&country={USA}"
    r = requests.get(url)
    respuesta = r.text.strip()
    
    if "ACCESS_NUMBER" in respuesta:
        partes = respuesta.split(':')
        # Devolvemos un diccionario con etiquetas claras
        return {
            "order_id": partes[1],
            "numero": partes[2]
        }
    else:
        print("Error al obtener número:", respuesta)
    return None

def obtener_numero_ca():
    url = f"https://api.grizzlysms.com/stubs/handler_api.php?api_key={API_KEY}&action=getNumber&service=am&country={CA}"
    r = requests.get(url)
    respuesta = r.text.strip()
    
    if "ACCESS_NUMBER" in respuesta:
        partes = respuesta.split(':')
        # Devolvemos un diccionario con etiquetas claras
        return {
            "order_id": partes[1],
            "numero": partes[2]
        }
    else:
        print("Error al obtener número:", respuesta)
    return None

def obtener_numero_mx():
    url = f"https://api.grizzlysms.com/stubs/handler_api.php?api_key={API_KEY}&action=getNumber&service=am&country={MX}"
    r = requests.get(url)
    respuesta = r.text.strip()
    
    if "ACCESS_NUMBER" in respuesta:
        partes = respuesta.split(':')
        # Devolvemos un diccionario con etiquetas claras
        return {
            "order_id": partes[1],
            "numero": partes[2]
        }
    else:
        print("Error al obtener número:", respuesta)
    return None

def esperar_sms(order_id):
    url = f"https://api.grizzlysms.com/stubs/handler_api.php?api_key={API_KEY}&action=getStatus&id={order_id}"
    
    # Intentamos durante un rato
    for _ in range(10):
        r = requests.get(url)
        respuesta = r.text.strip()
        
        if "STATUS_OK" in respuesta:
            codigo = respuesta.split(':')[1]
            return {"codigo": codigo}
        elif "STATUS_WAIT_CODE" in respuesta:
            print("Esperando SMS...")
        
        elif "NO_BALANCE" in respuesta:
            print("Sin saldo.")
            break
        
        time.sleep(10)
    return {"codigo": None}



def saldo_numeros():
    url = f"https://api.grizzlysms.com/stubs/handler_api.php?api_key={API_KEY}&action=getBalance"
    r = requests.get(url)
    saldo = r.text.strip()
    return saldo


def cancelar_numero(order_id):
    time.sleep(240) # Esperamos 4 minutos antes de cancelar
    url = f"https://api.grizzlysms.com/stubs/handler_api.php?api_key={API_KEY}&action=setStatus&status=-1&id={order_id}"
    r = requests.get(url)
    respuesta = r.text.strip()
    if "ACCESS_CANCEL" in respuesta:
        print("Número cancelado correctamente.")
    else:
        print("Error al cancelar número:", respuesta)


