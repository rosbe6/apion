import httpx
import re
import asyncio
import random

# --- CONFIGURACIÓN ---
# Asegúrate de que los datos de IPRoyal sean correctos
PROXY_URL = "http://o1CK8doqxzS9ENdO:ewwKtN9UnwgSnWnV_country-us@geo.iproyal.com:12321"

def get_headers(step="init"):
    h = {
        'authority': 'www.5littlemonkeys.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'accept-language': 'en-US,en;q=0.9',
        'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36'
    }
    
    if step == "init":
        h['sec-fetch-dest'] = 'document'
        h['sec-fetch-mode'] = 'navigate'
        h['sec-fetch-site'] = 'none'
    elif step == "product":
        h['sec-fetch-dest'] = 'document'
        h['sec-fetch-mode'] = 'navigate'
        h['sec-fetch-site'] = 'same-origin'
        h['referer'] = 'https://www.5littlemonkeys.com/'
    
    return h

async def main():
    # Usamos http2=True para imitar a Chrome
    async with httpx.AsyncClient(proxy=PROXY_URL, http2=True, follow_redirects=True, timeout=45) as client:
        print("🌐 Verificando conexión de proxy...")
        try:
            ip_check = await client.get("https://api.ipify.org")
            print(f"✅ Saliendo por IP: {ip_check.text}")
        except:
            print("❌ El proxy no responde o las credenciales están mal.")
            return

        # PASO 1: Visitar la HOME (Calentamiento)
        print("🏠 Visitando Home para generar cookies...")
        await client.get("https://www.5littlemonkeys.com/", headers=get_headers("init"))
        await asyncio.sleep(random.uniform(3, 5)) # Espera "humana"

        # PASO 2: Obtener el PRODUCTO y el FORM_KEY
        print("📦 Entrando a la página del producto...")
        url_prod = "https://www.5littlemonkeys.com/categories/building-toys/lego.html?product_list_order=price"
        resp = await client.get(url_prod, headers=get_headers("product"))
        
        # Guardamos para ver si pasamos
        with open("last_check.html", "w", encoding="utf-8") as f:
            f.write(resp.text)

        if "Attention Required!" in resp.text or "blocked" in resp.text:
            print("🛑 Cloudflare nos bloqueó de nuevo. Necesitas rotar la IP o cambiar el User-Agent.")
            return

        match = re.search(r'name="form_key"\s+type="hidden"\s+value="([a-zA-Z0-9]+)"', resp.text)
        if match:
            f_key = match.group(1)
            print(f"🔥 ¡ÉXITO! Form Key encontrado: {f_key}")
            
            # PASO 3: AGREGAR AL CARRITO (AQUÍ ES DONDE SE CONSOLIDA LA SESIÓN)
            uenc = "aHR0cHM6Ly93d3cuNWxpdHRsZW1vbmtleXMuY29tL2NhdGVnb3JpZXMvYnVpbGRpbmctdG95cy9sZWdvLmh0bWw_cHJvZHVjdF9saXN0X29yZGVyPXByaWNl"
            add_url = f"https://www.5littlemonkeys.com/checkout/cart/add/uenc/{uenc}/product/12418/"
            
            payload = {'product': '12418', 'uenc': uenc, 'form_key': f_key}
            h_add = get_headers("product")
            h_add.update({
                'accept': 'application/json, text/javascript, */*; q=0.01',
                'x-requested-with': 'XMLHttpRequest',
                'content-type': 'application/x-www-form-urlencoded; charset=UTF-8'
            })
            
            r_add = await client.post(add_url, data=payload, headers=h_add)
            if r_add.status_code == 200:
                print("🛒 Producto agregado. El bot está listo para el checkout.")
            else:
                print(f"❌ Error al agregar: {r_add.status_code}")
        else:
            print("❌ No se encontró el form_key. Revisa last_check.html")

if __name__ == "__main__":
    asyncio.run(main())