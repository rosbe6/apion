import httpx
import asyncio
import random

# --- CONFIGURACIÓN ---
# Usamos tus proxies de Canadá ya que el sitio es .ca
PROXY_URL = "http://o1CK8doqxzS9ENdO:ewwKtN9UnwgSnWnV_country-us@geo.iproyal.com:12321"

HEADERS_BASE = {
    'authority': 'petplanet-cumberlandsquare.ca',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'accept-language': 'en-US,en;q=0.9',
    'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
    'upgrade-insecure-requests': '1'
}

async def main():
    async with httpx.AsyncClient(proxy=PROXY_URL, http2=True, follow_redirects=True, timeout=30) as client:
        print("🚀 Iniciando Paso 1: Creación de Sesión en PetPlanet...")

        # 1. Visitar la tienda para obtener cookies iniciales
        try:
            print("🏠 Cargando Home...")
            await client.get("https://petplanet-cumberlandsquare.ca/", headers=HEADERS_BASE)
            await asyncio.sleep(random.uniform(1, 3))

            # 2. Visitar un producto barato (ej: un juguete o snack)
            # Usaremos el flujo de la web para ir al carrito
            print("📦 Accediendo al producto...")
            product_url = "https://petplanet-cumberlandsquare.ca/products/f62211-starmark-everlasting-treat-chicken-small"
            await client.get(product_url, headers=HEADERS_BASE)
            
            # 3. Este tipo de Shopify usa un carrito lateral. 
            # Necesitamos disparar el proceso de checkout
            print("🛒 Iniciando Checkout...")
            checkout_init_url = "https://petplanet-cumberlandsquare.ca/checkout"
            
            resp = await client.get(checkout_init_url, headers=HEADERS_BASE)
            
            if resp.status_code == 200:
                # El checkout de Shopify nos redirige a una URL con un token largo
                # Ejemplo: /checkout/c/c1-abc123...
                final_url = str(resp.url)
                if "/checkout/" in final_url:
                    checkout_token = final_url.split('/')[-1].split('?')[0]
                    print(f"✅ Checkout creado exitosamente.")
                    print(f"🔗 Token de Checkout: {checkout_token}")
                    return checkout_token
                else:
                    print("❌ No se redirigió al checkout. Posible bloqueo de Cloudflare.")
            else:
                print(f"❌ Error: {resp.status_code}")

        except Exception as e:
            print(f"❌ Error de conexión: {e}")

if __name__ == "__main__":
    asyncio.run(main())