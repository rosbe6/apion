import base64
import time
import requests
import os
from PIL import Image
from io import BytesIO
from loguru import logger
from dotenv import load_dotenv
from DrissionPage import ChromiumPage, ChromiumOptions
from browser_utils import get_chromium_or_env

load_dotenv()

# Cargar CAPSOLVER_API_KEY desde .env
CAPSOLVER_API_KEY = os.getenv("CAPSOLVER_API_KEY", "")
if not CAPSOLVER_API_KEY:
    raise ValueError("❌ CAPSOLVER_API_KEY no configurado en .env")

# Mapa de palabras en español → question de Capsolver
HINT_MAP = {
    # Español
    "bolsa": "aws:grid:bag",
    "bolsas": "aws:grid:bag",
    "cama": "aws:grid:bed",
    "camas": "aws:grid:bed",
    "cinturón": "aws:grid:belts",
    "cinturones": "aws:grid:belts",
    "prismático": "aws:grid:binocular",
    "prismáticos": "aws:grid:binocular",
    "balde": "aws:grid:bucket",
    "cubeta": "aws:grid:bucket",
    "silla": "aws:grid:chair",
    "sillas": "aws:grid:chair",
    "reloj": "aws:grid:clock",
    "relojes": "aws:grid:clock",
    "olla": "aws:grid:cooking pot",
    "ollas": "aws:grid:cooking pot",
    "cortina": "aws:grid:curtain",
    "cortinas": "aws:grid:curtain",
    "tenedor": "aws:grid:fork",
    "tenedores": "aws:grid:fork",
    "sombrero": "aws:grid:hat",
    "sombreros": "aws:grid:hat",
    "tijera": "aws:grid:scissors",
    "tijeras": "aws:grid:scissors",
    "asiento": "aws:grid:seat",
    "asientos": "aws:grid:seat",
    "cuchara": "aws:grid:spoon",
    "cucharas": "aws:grid:spoon",
    "maleta": "aws:grid:suitcase",
    "maletas": "aws:grid:suitcase",
    "paraguas": "aws:grid:umbrella",
    # Inglés
    "bag": "aws:grid:bag",
    "bags": "aws:grid:bag",
    "bed": "aws:grid:bed",
    "beds": "aws:grid:bed",
    "belt": "aws:grid:belts",
    "belts": "aws:grid:belts",
    "binocular": "aws:grid:binocular",
    "binoculars": "aws:grid:binocular",
    "bucket": "aws:grid:bucket",
    "buckets": "aws:grid:bucket",
    "chair": "aws:grid:chair",
    "chairs": "aws:grid:chair",
    "clock": "aws:grid:clock",
    "clocks": "aws:grid:clock",
    "cooking pot": "aws:grid:cooking pot",
    "cooking pots": "aws:grid:cooking pot",
    "curtain": "aws:grid:curtain",
    "curtains": "aws:grid:curtain",
    "fork": "aws:grid:fork",
    "forks": "aws:grid:fork",
    "hat": "aws:grid:hat",
    "hats": "aws:grid:hat",
    "scissors": "aws:grid:scissors",
    "seat": "aws:grid:seat",
    "seats": "aws:grid:seat",
    "spoon": "aws:grid:spoon",
    "spoons": "aws:grid:spoon",
    "suitcase": "aws:grid:suitcase",
    "suitcases": "aws:grid:suitcase",
    "umbrella": "aws:grid:umbrella",
    "umbrellas": "aws:grid:umbrella",
}


def get_captcha_hint(page):
    """Obtiene el texto del hint y lo mapea al formato de Capsolver"""
    try:
        em_elements = page.eles('tag:em')
        for em in em_elements:
            is_underlined = page.run_js(
                "return window.getComputedStyle(arguments[0]).textDecoration.includes('underline');",
                em
            )
            if is_underlined:
                underlined_text = em.text.strip().lower()
                logger.info(f"Texto subrayado: '{underlined_text}'")

                for keyword, question in HINT_MAP.items():
                    if keyword in underlined_text:
                        logger.info(f"Question mapeada: {question}")
                        return question

                logger.warning(f"Palabra '{underlined_text}' no encontrada en el mapa")
                return None

        logger.warning("No se encontró hint subrayado")
        return None
    except Exception as e:
        logger.error(f"Error obteniendo hint: {e}")
        return None


def get_canvas_base64(page):
    """Captura la imagen del canvas como base64"""
    try:
        canvas = page.ele('tag:canvas')
        if not canvas:
            logger.error("No se encontró el canvas")
            return None
        img_base64 = page.run_js("return arguments[0].toDataURL('image/png');", canvas)
        logger.info("Canvas capturado correctamente")
        return img_base64
    except Exception as e:
        logger.error(f"Error capturando canvas: {e}")
        return None


def split_canvas_into_9(img_base64):
    """
    Divide el canvas 3x3 en 9 imágenes individuales en base64.
    Capsolver necesita cada celda por separado.
    """
    try:
        img_data = img_base64.split('base64,')[1] if 'base64,' in img_base64 else img_base64
        img = Image.open(BytesIO(base64.b64decode(img_data)))

        w, h = img.size
        cell_w = w // 3
        cell_h = h // 3

        images_b64 = []
        for row in range(3):
            for col in range(3):
                left   = col * cell_w
                top    = row * cell_h
                right  = left + cell_w
                bottom = top + cell_h

                cell = img.crop((left, top, right, bottom))
                buffer = BytesIO()
                cell.save(buffer, format="PNG")
                cell_b64 = base64.b64encode(buffer.getvalue()).decode()
                images_b64.append(cell_b64)

        logger.info(f"Canvas dividido en {len(images_b64)} imágenes")
        return images_b64
    except Exception as e:
        logger.error(f"Error dividiendo canvas: {e}")
        return None


def send_to_capsolver(api_key, images_b64, question):
    """Envía las 9 imágenes a Capsolver y retorna los índices a clickear"""
    try:
        logger.info(f"Enviando a Capsolver, question: '{question}'")

        response = requests.post("https://api.capsolver.com/createTask", json={
            "clientKey": api_key,
            "task": {
                "type": "AwsWafClassification",
                "websiteURL": "https://www.amazon.com",
                "images": images_b64,
                "question": question
            }
        }, timeout=30)

        result = response.json()
        logger.debug(f"Respuesta Capsolver: {result}")

        if result.get("errorId") != 0:
            logger.error(f"Error: {result.get('errorDescription')}")
            return None

        # AwsWafClassification devuelve resultado directo (sin polling)
        solution = result.get("solution", {})
        objects = solution.get("objects", [])
        logger.success(f"Índices recibidos (base 0): {objects}")

        # Convertir de base 0 a base 1 para el click
        indexes = [i + 1 for i in objects]
        logger.info(f"Índices para click (base 1): {indexes}")
        return indexes

    except Exception as e:
        logger.error(f"Error en Capsolver: {e}")
        return None


def click_captcha_cells(page, indexes):
    """Hace click en las celdas del grid según los índices"""
    try:
        buttons = page.eles('xpath://canvas/button')
        if not buttons:
            buttons = page.eles('xpath://canvas/..//button')

        logger.info(f"Botones encontrados: {len(buttons)}")

        if not buttons:
            logger.error("No se encontraron botones en el grid")
            return False

        for index in indexes:
            idx = index - 1
            if idx < len(buttons):
                page.run_js("arguments[0].click();", buttons[idx])
                logger.info(f"✓ Click en celda {index}")
                time.sleep(0.3)
            else:
                logger.warning(f"Índice {index} fuera de rango")

        # Confirmar
        time.sleep(0.5)
        confirm = page.ele('xpath://button[@type="submit"] | //input[@type="submit"]')
        if confirm:
            page.run_js("arguments[0].click();", confirm)
            logger.success("✅ Captcha confirmado")

        return True
    except Exception as e:
        logger.error(f"Error clickeando celdas: {e}")
        return False


def solve_captcha(page, api_key):
    """Función principal: detecta y resuelve el captcha"""
    logger.info("Verificando captcha...")

    captcha = page.ele('xpath://h1[contains(@id, "captcha-header")]', timeout=60)
    if not captcha:
        logger.info("No hay captcha en la página")
        return True

    logger.warning("⚠️ Captcha detectado!")
    time.sleep(1)

    # 1. Capturar canvas completo
    img_base64 = get_canvas_base64(page)
    if not img_base64:
        return False

    # 2. Obtener question mapeada
    question = get_captcha_hint(page)
    if not question:
        logger.error("No se pudo mapear el hint al formato de Capsolver")
        return False

    # 3. Dividir en 9 imágenes
    images_b64 = split_canvas_into_9(img_base64)
    if not images_b64:
        return False

    # 4. Enviar a Capsolver
    indexes = send_to_capsolver(api_key, images_b64, question)
    if not indexes:
        return False

    # 5. Clickear celdas y confirmar
    return click_captcha_cells(page, indexes)


def main():
    options = ChromiumOptions()
    chromium_path = get_chromium_or_env()
    options.set_browser_path(chromium_path)
    options.set_argument('--no-sandbox')
    options.set_argument('--window-size=1920,1080')
    options.set_argument(
        '--user-agent=Mozilla/5.0 (X11; Linux x86_64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36'
    )
    options.auto_port()

    page = ChromiumPage(addr_or_opts=options)
    time.sleep(2)  # Espera a que el navegador esté listo

    try:
        page.get("https://www.amazon.com/ap/cvf/request?arb=fbd7059f-06e4-4ff6-98db-d3a74490330c&language=es")
        logger.info("Amazon cargado")

        success = solve_captcha(page, CAPSOLVER_API_KEY)

        if success:
            logger.success("✅ Captcha resuelto!")
        else:
            logger.error("❌ No se pudo resolver el captcha")

    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        input("Presiona Enter para cerrar...")
        page.quit()


if __name__ == "__main__":
    main()