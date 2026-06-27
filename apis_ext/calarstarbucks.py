from DrissionPage import Chromium, ChromiumOptions
import os
import uuid
import requests
import psutil

print("=== Iniciando Módulo: Registro con Sesión Única y Aislada ===")
    
    # 1. Configuración de Rutas y Sesión Única
base_path = os.path.dirname(os.path.abspath(__file__))

# Creamos un ID único para que esta sesión sea irreconocible de la anterior
session_id = f"session_{uuid.uuid4().hex[:10]}"
perfil_dir = os.path.join(base_path, "temp_profiles", session_id)

# 2. Configuración de Opciones del Navegador
co = ChromiumOptions()
co.set_browser_path(r'C:\chrome_128\chrome.exe')

# AISLAMIENTO: Definir la carpeta de datos de usuario única
co.set_user_data_path(perfil_dir)
co.set_argument('--disable-features=OptimizationGuideModelDownloading,OptimizationHints,OptimizationTargetPrediction,OptimizationGuide')
co.set_argument('--disable-component-update')
co.set_argument('--disable-background-networking')
co.set_argument('--no-first-run')
co.set_pref('intl.accept_languages', 'en-US,en')
co.set_argument('--disable-blink-features=AutomationControlled')
co.set_argument('--disable-webrtc')
co.set_argument('--disable-dev-shm-usage')
co.set_argument('--disable-extensions')

co.set_argument('--no-first-run')
co.set_argument('--lang=en-US')
co.set_argument('--disable-blink-features=AutomationControlled')
co.set_argument('--disable-webrtc')
co.set_argument('--disable-dev-shm-usage')
co.set_argument('--disable-extensions')

def bloquear_recursos_no_esenciales(page):
    """Bloquea imágenes, fuentes y recursos no esenciales para ahorrar ancho de banda."""
    page.set.blocked_urls([
        '*.png', '*.jpg', '*.jpeg', '*.gif', '*.webp', '*.svg', '*.ico',
        '*.woff', '*.woff2', '*.ttf', '*.eot',
        '*analytics*', '*ads*', '*doubleclick*',
        '*optimizationguide-pa.googleapis.com*'
    ])

co.auto_port()

# Iniciar Navegador


#### Aca comienza a correr la instancia de Chromium con el perfil temporal y la extensión cargada. Todo lo que se haga aquí dentro quedará aislado en esa carpeta de perfil, y al finalizar se borra toda la carpeta para no dejar rastro.
net_inicio = psutil.net_io_counters()


browser = Chromium(co)
page = browser.page()   
bloquear_recursos_no_esenciales(page)

page.get("https://www.starbucks.com/gift")
