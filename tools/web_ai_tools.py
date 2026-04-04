import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pyperclip

def cerrar_chrome_forzado():
    """Mata procesos de Chrome para liberar el perfil."""
    try:
        os.system("taskkill /f /im chrome.exe /T >nul 2>&1")
    except:
        pass
    time.sleep(1)

def abrir_chrome_debug_mode(profile_path: str):
    """
    Abre el navegador Chrome nativo del usuario con el puerto de depuración 9222 abierto.
    Este es el método más robusto contra Cloudflare porque usa el ejecutable real de Chrome
    en un proceso separado, no administrado por el binario de webdriver.
    """
    import subprocess
    import time
    import urllib.request

    # Comprobar si ya está corriendo en el puerto 9222
    try:
        urllib.request.urlopen("http://127.0.0.1:9222/json", timeout=1)
        print("✅ Chrome en modo debug ya está corriendo.")
        return True
    except:
        pass

    chrome_path = ""
    if os.name == 'nt': # Windows
        paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.join(os.environ.get('LOCALAPPDATA', ''), r"Google\Chrome\Application\chrome.exe")
        ]
        for p in paths:
            if os.path.exists(p):
                chrome_path = p
                break
    else:
        # En Linux/Mac, asumimos que chrome está en el PATH
        chrome_path = "google-chrome"

    if not chrome_path:
        print("⚠️ No se encontró la ruta de Chrome nativo.")
        return False

    if os.name == 'nt':
        cerrar_chrome_forzado()

    comando = f'"{chrome_path}" --remote-debugging-port=9222 --user-data-dir="{profile_path}"'
    print("🚀 Levantando sesión nativa de Chrome en puerto 9222...")
    subprocess.Popen(comando, shell=True)
    time.sleep(3) # Dar tiempo a que Chrome abra completamente
    return True

def enviar_prompt_generico(driver, wait, prompt_completo: str, url: str, selector_caja: By, valor_caja: str, selector_respuesta_css: str, nombre_ia: str) -> str:
    """
    Función base para interactuar tanto con ChatGPT como con Gemini.
    """
    driver.get(url)

    # 1. Esperar caja de chat tolerando CAPTCHAs/Logins
    print(f"Buscando caja de chat en {nombre_ia}. Si ves un control o login, hazlo manualmente en la ventana de Chrome.")
    text_area = None
    intentos = 0
    max_intentos = 60 # Esperar hasta 5 minutos

    while intentos < max_intentos:
        try:
            text_area = WebDriverWait(driver, 1).until(EC.presence_of_element_located((selector_caja, valor_caja)))
            break
        except:
            intentos += 1
            if intentos % 5 == 0:
                 print(f"⏳ Aún esperando (Caja de chat de {nombre_ia} no detectada). Completa login si es necesario...")
            time.sleep(5)

    if not text_area:
         return f"❌ Error: Se agotó el tiempo de espera (5 minutos) para encontrar la caja de {nombre_ia}."

    # 2. Enviar Prompt (Usando Portapapeles para velocidad)
    print(f"📋 Pegando prompt en {nombre_ia}...")
    pyperclip.copy(prompt_completo)
    text_area.click()
    time.sleep(0.5)
    control_key = Keys.COMMAND if os.name == 'posix' and 'darwin' in os.uname().sysname.lower() else Keys.CONTROL
    text_area.send_keys(control_key, 'v')
    time.sleep(1)
    text_area.send_keys(Keys.ENTER)

    # 3. Esperar respuesta
    print(f"⏳ Esperando respuesta de {nombre_ia} (esto puede tomar un minuto)...")
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector_respuesta_css)))

    stable_count = 0
    last_len = 0

    # Verificamos cada 2 segundos, necesitamos 3 aciertos (6 segundos total de silencio)
    for _ in range(120):
        respuestas = driver.find_elements(By.CSS_SELECTOR, selector_respuesta_css)
        if not respuestas:
            time.sleep(1); continue

        texto = respuestas[-1].text
        current_len = len(texto)

        if current_len == last_len and current_len > 15: # >15 para asegurar que no es texto de carga vacío
            stable_count += 1
        else:
            stable_count = 0
            last_len = current_len

        print(f"Generando... {current_len} caracteres (Estabilidad: {stable_count}/3)", end="\r")

        if stable_count >= 3:
            break

        time.sleep(2)

    final_text = respuestas[-1].text
    print(f"\n✅ Respuesta de {nombre_ia} completada. ({len(final_text)} caracteres).")

    return final_text

def inicializar_driver_con_debug(profile_path: str):
    """Inicializa y retorna el driver conectándose a Chrome."""
    driver = None
    if abrir_chrome_debug_mode(profile_path):
        chrome_options = Options()
        chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        driver = webdriver.Chrome(options=chrome_options)
    else:
        print("⚠️ Usando método clásico de webdriver...")
        chrome_options = Options()
        chrome_options.add_argument(f"--user-data-dir={profile_path}")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

def ask_chatgpt_web(prompt_completo: str) -> str:
    """Abre ChatGPT, envía el texto y devuelve la respuesta."""
    # Configuración de perfil dedicado
    if os.name == 'nt':
        desktop = os.path.join(os.environ.get('USERPROFILE', ''), 'Desktop')
        profile_path = os.path.join(desktop, "ChromeBotProfile")
    else:
        profile_path = os.path.join(os.path.expanduser("~"), ".ChromeBotProfile")

    try:
        driver = inicializar_driver_con_debug(profile_path)
        wait = WebDriverWait(driver, 60)
        return enviar_prompt_generico(
            driver, wait, prompt_completo,
            url="https://chatgpt.com/",
            selector_caja=By.ID,
            valor_caja="prompt-textarea",
            selector_respuesta_css="div[data-message-author-role='assistant']",
            nombre_ia="ChatGPT"
        )
    except Exception as e:
        return f"❌ Error ejecutando ChatGPT Web: {str(e)}"
    finally:
        if driver: driver.quit()

def ask_gemini_web(prompt_completo: str, gem_url: str = "https://gemini.google.com/app") -> str:
    """Abre Gemini (o un Gem específico), envía el texto y devuelve la respuesta."""
    if os.name == 'nt':
        desktop = os.path.join(os.environ.get('USERPROFILE', ''), 'Desktop')
        profile_path = os.path.join(desktop, "ChromeBotProfile")
    else:
        profile_path = os.path.join(os.path.expanduser("~"), ".ChromeBotProfile")

    driver = None
    try:
        driver = inicializar_driver_con_debug(profile_path)
        wait = WebDriverWait(driver, 60)

        # En Gemini la caja de texto tiene clase 'ql-editor' o se ubica por css '.ql-editor textarea'
        # Usaremos la etiqueta rich-textarea o div con aria-label "Introduce una petición aquí"
        return enviar_prompt_generico(
            driver, wait, prompt_completo,
            url=gem_url,
            selector_caja=By.CSS_SELECTOR,
            valor_caja="rich-textarea div p", # Selector típico del input de Gemini
            selector_respuesta_css="message-content", # Gemini usa la etiqueta <message-content>
            nombre_ia="Gemini"
        )
    except Exception as e:
        return f"❌ Error ejecutando Gemini Web: {str(e)}"
    finally:
        if driver: driver.quit()

if __name__ == "__main__":
    # Test rápido del módulo si se corre independientemente
    respuesta = ask_chatgpt_web("Hola, dime en 2 líneas qué es la programación.")
    print("\nRespuesta obtenida:\n", respuesta)
