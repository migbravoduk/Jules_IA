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

def ask_chatgpt_web(prompt_completo: str) -> str:
    """
    Lógica central de Selenium adaptada como herramienta (Skill).
    Recibe el prompt, abre ChatGPT, envía el texto y devuelve la respuesta como string.
    """
    # Configuración de perfil dedicado
    if os.name == 'nt':
        desktop = os.path.join(os.environ.get('USERPROFILE', ''), 'Desktop')
        profile_path = os.path.join(desktop, "ChromeBotProfile")
    else:
        profile_path = os.path.join(os.path.expanduser("~"), ".ChromeBotProfile")

    driver = None
    try:
        # Intentar conectar usando Debugging Port
        if abrir_chrome_debug_mode(profile_path):
            chrome_options = Options()
            chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
            driver = webdriver.Chrome(options=chrome_options)
        else:
            # Fallback clásico si no pudo lanzar el debug
            print("⚠️ Usando método clásico de webdriver...")
            chrome_options = Options()
            chrome_options.add_argument(f"--user-data-dir={profile_path}")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

        driver.get("https://chatgpt.com/")

        wait = WebDriverWait(driver, 60)

        # 1. Esperar caja de chat (sin blocking input) tolerando CAPTCHA manual
        print("Buscando caja de chat. Si ves un control de 'Soy humano' o debes iniciar sesión, hazlo manualmente en la ventana de Chrome.")
        text_area = None
        intentos = 0
        max_intentos = 60 # Esperar hasta 5 minutos

        while intentos < max_intentos:
            try:
                text_area = WebDriverWait(driver, 1).until(EC.presence_of_element_located((By.ID, "prompt-textarea")))
                break
            except:
                intentos += 1
                if intentos % 5 == 0:
                     print("⏳ Aún esperando (Caja de chat no detectada). Completa CAPTCHA/Login si es necesario...")
                time.sleep(5)

        if not text_area:
             return "❌ Error: Se agotó el tiempo de espera (5 minutos) para encontrar la caja de ChatGPT. Asegúrate de haber resuelto el CAPTCHA."

        # 2. Enviar Prompt (Usando Portapapeles para velocidad)
        print("📋 Pegando prompt en ChatGPT...")
        pyperclip.copy(prompt_completo) # Copiamos al portapapeles
        text_area.click()
        time.sleep(0.5)
        # Ctrl+V en Windows/Linux, Cmd+V en Mac
        control_key = Keys.COMMAND if os.name == 'posix' and 'darwin' in os.uname().sysname.lower() else Keys.CONTROL
        text_area.send_keys(control_key, 'v')
        time.sleep(1)
        text_area.send_keys(Keys.ENTER)

        # 3. Esperar respuesta (Lógica mejorada para evitar cortes)
        print("⏳ Esperando respuesta de ChatGPT...")
        selector_respuesta = "div[data-message-author-role='assistant']"
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector_respuesta)))

        stable_count = 0
        last_len = 0

        # Verificamos cada 2 segundos, necesitamos 3 aciertos (6 segundos total de silencio)
        for _ in range(120):
            respuestas = driver.find_elements(By.CSS_SELECTOR, selector_respuesta)
            if not respuestas:
                time.sleep(1); continue

            texto = respuestas[-1].text
            current_len = len(texto)

            if current_len == last_len and current_len > 10:
                stable_count += 1
            else:
                stable_count = 0
                last_len = current_len

            print(f"Generando... {current_len} caracteres (Estabilidad: {stable_count}/3)", end="\r")

            if stable_count >= 3:
                break

            time.sleep(2) # Pausa de 2 segundos entre chequeos

        final_text = respuestas[-1].text
        print(f"\n✅ Respuesta completada. ({len(final_text)} caracteres).")

        return final_text

    except Exception as e:
        return f"❌ Error ejecutando ChatGPT Web: {str(e)}"
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    # Test rápido del módulo si se corre independientemente
    respuesta = ask_chatgpt_web("Hola, dime en 2 líneas qué es la programación.")
    print("\nRespuesta obtenida:\n", respuesta)
