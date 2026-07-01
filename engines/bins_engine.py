import csv
import re
import os
import httpx
import logging
from dotenv import load_dotenv
# Importamos tu función desde el archivo paises.py
from paises import obtener_pais_formateado

# Cargar .env desde el directorio raíz del proyecto
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

logger = logging.getLogger(__name__) 

# Ruta hacia tu archivo bins_all.csv
CSV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "bins_all.csv"))

async def get_bin_dict(cc_bin):
    """Devuelve el diccionario buscando localmente en el archivo CSV"""
    solo_bin = re.sub(r'\D', '', str(cc_bin))[:6]
    
    if not os.path.exists(CSV_PATH):
        print(f"❌ Error: No se encontró el archivo CSV en la ruta: {CSV_PATH}")
        return None

    try:
        with open(CSV_PATH, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)
            
            for row in reader:
                if not row or len(row) < 7:
                    continue
                
                # row[0]=BIN, row[1]=Código ISO (ej: "US")
                if row[0] == solo_bin:
                    # Pasamos el código ISO (row[1]) por tu función mágica
                    pais_completo = obtener_pais_formateado(row[1])
                    
                    return {
                        "bin": solo_bin,
                        "pais": pais_completo, # <--- Aquí ya va formateado hermoso
                        "brand": (row[3] or "UNKNOWN").upper(),
                        "type": (row[4] or "UNKNOWN").upper(),
                        "level": (row[5] or "STANDARD").upper(),
                        "bank": (row[6] or "UNKNOWN").upper()
                    }
    except Exception as e:
        print(f"Error leyendo el CSV: {e}")
        
    return None


async def get_bin_dict_new(cc_bin):
    """Consulta información del BIN en la API remota (sin usar el CSV local)."""
    bin_query = str(cc_bin).strip()

    if not bin_query:
        return None

    url = f"https://data.handyapi.com/bin/{bin_query}"
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
    proxy = os.getenv('HANDYAPI_PROXY')

    try:
        if proxy:
            logger.info(f"✅ Usando proxy HandyAPI: {proxy[:30]}...")
        else:
            logger.warning(f"⚠️  Sin proxy HandyAPI configurado")

        async with httpx.AsyncClient(proxy=proxy) as client:
            r = await client.get(url, headers=headers, timeout=10.0)

        if r.status_code != 200:
            logger.error(f"❌ HandyAPI error: Status {r.status_code}")
            return None

        data = r.json()

        # Banco
        banco = data.get('Issuer', 'UNKNOWN')
        if isinstance(banco, dict):
            banco = banco.get('name') or banco.get('Name') or 'UNKNOWN'

        # País - preferimos obtener emoji/formato desde paises.obtener_pais_formateado
        country = data.get('Country', {})
        if isinstance(country, dict):
            iso = None
            for k in ('Iso2', 'iso2', 'ISO2', 'alpha2', 'Alpha2', 'iso', 'ISO', 'Iso', 'code', 'Code'):
                if k in country and country[k]:
                    iso = country[k]
                    break
            if iso:
                pais = obtener_pais_formateado(iso)
            else:
                nombre_pais = country.get('Name') or country.get('name')
                pais = obtener_pais_formateado(nombre_pais) if nombre_pais else 'UNKNOWN 🌐'
        else:
            pais = obtener_pais_formateado(country) if country else 'UNKNOWN 🌐'

        marca = (data.get('Scheme') or data.get('scheme') or 'UNKNOWN').upper()
        tipo = (data.get('Type') or data.get('type') or 'UNKNOWN')
        try:
            tipo = tipo.capitalize()
        except Exception:
            pass

        nivel_raw = data.get('CardTier') or data.get('brand') or data.get('card_tier') or 'UNKNOWN'
        nivel = str(nivel_raw)
        # Eliminar la marca del nivel si aparece (ej: 'MASTERCARD' dentro de 'PREPAID MASTERCARD ...')
        try:
            if marca and marca.lower() in nivel.lower():
                nivel = re.sub(re.escape(marca), '', nivel, flags=re.IGNORECASE).strip()
            nivel = re.sub(r'^[\-\:\s]+', '', nivel)
            nivel = re.sub(r'\s{2,}', ' ', nivel).strip()
            nivel = nivel.upper()
        except Exception:
            nivel = nivel.upper()

        return {
            "bin": bin_query,
            "pais": pais,
            "brand": marca,
            "type": tipo,
            "level": nivel,
            "bank": banco
        }
    except Exception as e:
        logger.error(f"❌ HandyAPI error: {type(e).__name__}: {e}")
        return None

async def get_bin_info(cc_bin):
    """Mantiene compatibilidad con el formato viejo (String)"""
    data = await get_bin_dict(cc_bin)
    if not data: 
        return "EMPTY"
    return f"{data['type']} - {data['level']} - {data['brand']}, {data['bank']}, {data['pais']}"

async def fetch_bins_engine(country="", bank="", vendor="", card_type="", level="", limit=1000):
    """Buscador optimizado para CSV con soporte de nombres completos de países y códigos ISO"""
    if not os.path.exists(CSV_PATH):
        return "EMPTY"
        
    biblioteca = {}
    count = 0
    
    # Limpiamos y normalizamos las entradas a minúsculas
    f_country = country.lower().strip()
    f_bank = bank.lower().strip()
    f_vendor = vendor.lower().strip()
    f_type = card_type.lower().strip()
    f_level = level.lower().strip()

    # Si el usuario escribió un país largo (ej: "colombia"), intentamos buscar su ISO de 2 letras
    # Importamos PAISES_DICT para tener la lista de traducciones a mano
    from paises import PAISES_DICT
    iso_detectado = ""
    if f_country and len(f_country) > 2:
        for iso, nombre in PAISES_DICT.items():
            if f_country in nombre.lower():
                iso_detectado = iso.lower()
                break

    try:
        with open(CSV_PATH, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if not row or len(row) < 7:
                    continue
                
                bin_num, c_code, flag, vdr_val, typ_val, lvl_val, banco_raw = row
                c_code_lower = c_code.lower()
                
                # --- FILTRO DE PAÍS ---
                if f_country:
                    if f_country != c_code_lower and f_country != flag.lower() and iso_detectado != c_code_lower:
                        continue

                # --- RESTO DE FILTROS ---
                if f_bank and f_bank not in banco_raw.lower(): continue
                if f_vendor and f_vendor not in vdr_val.lower(): continue
                if f_type and f_type not in typ_val.lower(): continue
                if f_level and f_level not in lvl_val.lower(): continue
                
                b_key = re.sub(r'[^a-zA-Z0-9]', '', banco_raw).lower() or "indefinido"
                cat_tipo = f"{vdr_val} {typ_val} ({lvl_val})".upper()
                
                # --- AQUÍ ESTÁ EL CAMBIO CLAVE ---
                # Si el banco es nuevo y ya alcanzamos el límite de bancos permitidos, lo saltamos
                if b_key not in biblioteca and len(biblioteca) >= limit:
                    continue
                
                # Si ya está en la biblioteca o aún hay espacio para nuevos bancos, lo agregamos
                if b_key not in biblioteca:
                    nombre_banco = banco_raw.strip().upper() or "BANCO INDEFINIDO"
                    biblioteca[b_key] = {"nombre": nombre_banco, "sub": {}}
                    
                if cat_tipo not in biblioteca[b_key]["sub"]:
                    biblioteca[b_key]["sub"][cat_tipo] = []
                
                biblioteca[b_key]["sub"][cat_tipo].append(bin_num)
                
            return biblioteca if biblioteca else "EMPTY"
                    
            return biblioteca if biblioteca else "EMPTY"
    except Exception as e:
        print(f"Error en fetch_bins_engine: {e}")
        return None