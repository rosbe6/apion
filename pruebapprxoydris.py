

from DrissionPage import Chromium, ChromiumOptions
import time
import json
from amz.datos import generar_nombre, generar_direccion_real, obtener_numero_ca
import random



# Configuración del navegador
co = ChromiumOptions()
co.set_browser_path(r'C:\chrome_128\chrome.exe')  # Ruta a tu Chrome

# Configurar el proxy con autenticación (formato correcto para DrissionPage)
proxy_server = "p.webshare.io:9999"
co.set_proxy(f"http://{proxy_server}")

# Configurar opciones adicionales para evitar detección
co.set_argument('--disable-blink-features=AutomationControlled')
co.set_argument('--disable-infobars')
co.set_argument('--no-sandbox')
co.set_argument('--disable-dev-shm-usage')
co.set_argument('--disable-extensions')
co.set_argument('--disable-gpu')

# Iniciar el navegador
browser = Chromium(co)
page = browser.latest_tab

def escritura_humana(elemento, texto):
    for caracter in texto:
        elemento.input(caracter)
        time.sleep(random.uniform(0.07, 0.35))

direccion = generar_direccion_real()

street = direccion['calle']
nombre = generar_nombre()
city = direccion['ciudad']
state = direccion['estado']
postal_code = direccion['zip']

print(f"Generando dirección coherente: {street}, {city}, {state}, {postal_code}")
# Espera para que la página cargue completamente


page.get("https://www.amazon.com.mx/a/addresses/add?ref=ya_address_book_add_button")
time.sleep(1)  # Espera para que la página cargue completamente

print("[*] Llenando formulario de dirección...")

page.ele('#address-ui-widgets-countryCode').click()
time.sleep(0.5)
usa_option = page.ele('#address-ui-widgets-countryCode-dropdown-nativeId_66')
usa_option.click()  # Haz clic en la opción de USA
time.sleep(2)  

escritura_humana(page.ele('#address-ui-widgets-enterAddressFullName'), nombre)
time.sleep(0.5)

escritura_humana(page.ele('#address-ui-widgets-enterAddressPhoneNumber'), "+15815951108")
time.sleep(0.5)


escritura_humana(page.ele('#address-ui-widgets-enterAddressLine1'), str(street))
time.sleep(0.5)

print("Street rellenado")

escritura_humana(page.ele('#address-ui-widgets-enterAddressCity'), str(city))
time.sleep(0.5)

print("City rellenado")

page.ele('#address-ui-widgets-enterAddressStateOrRegion-dropdown-nativeId').select(state)
time.sleep(0.5)
print("State rellenado")

escritura_humana(page.ele('#address-ui-widgets-enterAddressPostalCode'), str(postal_code))
time.sleep(0.5)
print("Postal Code rellenado")

nombre_field = page.ele('#address-ui-widgets-enterAddressFullName', timeout=10)
nombre_field.clear()  

escritura_humana(page.ele('#address-ui-widgets-enterAddressFullName'), nombre)
time.sleep(0.5)


page.ele('#address-ui-widgets-form-submit-button-announce').click()
time.sleep(10)
