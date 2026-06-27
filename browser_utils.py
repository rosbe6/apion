import os
import glob
import platform

def find_chromium_path():
    """
    Detecta la ruta de Chromium/Chrome automáticamente según el SO.
    Funciona en Windows, macOS y Linux.

    Returns:
        str: Ruta completa a Chromium/Chrome

    Raises:
        Exception: Si Chromium no se encuentra en ninguna ruta conocida
    """

    system = platform.system()

    # Rutas por SO
    if system == "Linux":
        possible_paths = [
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
            "/snap/bin/chromium",
            "/opt/google/chrome/chrome",
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
        ]
    elif system == "Darwin":  # macOS
        possible_paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
        ]
    elif system == "Windows":
        possible_paths = [
            r"C:\chrome_128\chrome.exe",
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files\Chromium\chrome.exe",
        ]
    else:
        raise Exception(f"❌ Sistema operativo no soportado: {system}")

    # Buscar en rutas directas
    for path in possible_paths:
        if os.path.exists(path) and os.path.isfile(path):
            return path

    # Buscar en /snap/ (patrón glob para Snap)
    if system == "Linux":
        snap_pattern = "/snap/chromium/current/usr/bin/chromium"
        if os.path.exists(snap_pattern):
            return snap_pattern

    # Último recurso: si está en PATH, intentar encontrar
    if system in ["Linux", "Darwin"]:
        result = os.popen("which chromium 2>/dev/null || which google-chrome 2>/dev/null").read().strip()
        if result:
            return result

    # Si no encontramos nada, lanzar error
    if system == "Linux":
        raise Exception(
            "❌ Chromium no encontrado.\n"
            "Instala con: sudo apt install chromium-browser -y\n"
            "O descarga desde: https://www.chromium.org/getting-involved/download-chromium"
        )
    elif system == "Windows":
        raise Exception(
            "❌ Chrome no encontrado.\n"
            "Descarga desde: https://www.google.com/intl/es/chrome/"
        )
    else:
        raise Exception("❌ Chromium/Chrome no encontrado")

def get_chromium_or_env():
    """
    Obtiene la ruta de Chromium de variable de entorno o detecta automáticamente.
    Preferencia: Variable de entorno CHROMIUM_PATH > Detección automática
    """
    chromium_path = os.getenv("CHROMIUM_PATH")

    if chromium_path and os.path.exists(chromium_path):
        return chromium_path

    return find_chromium_path()
