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

# ---------------------------------------------------------------------------
# Utilidades de Chrome
# ---------------------------------------------------------------------------

def _get_profile_path() -> str:
    """Retorna la ruta del perfil dedicado de Chrome para el bot."""
    if os.name == 'nt':
        desktop = os.path.join(os.environ.get('USERPROFILE', ''), 'Desktop')
    else:
        desktop = os.path.expanduser("~")
    return os.path.join(desktop, "ChromeBotProfile")

def _cerrar_chrome_forzado():
    """Mata todos los procesos de Chrome en Windows para liberar el perfil."""
    try:
        os.system("taskkill /f /im chrome.exe /T >nul 2>&1")
    except:
        pass
    time.sleep(1)

def _abrir_chrome_debug_mode(profile_path: str) -> bool:
    """
    Lanza Chrome nativo con el puerto de depuracion 9222 activado.
    Este metodo es el mas robusto contra Cloudflare porque usa el ejecutable
    real de Chrome en un proceso separado al de webdriver.
    """
    import subprocess
    import urllib.request

    # 1. Verificar si ya esta corriendo en el puerto 9222
    try:
        urllib.request.urlopen("http://127.0.0.1:9222/json", timeout=1)
        print("Chrome en modo debug ya esta corriendo.")
        return True
    except:
        pass

    # 2. Buscar el ejecutable de Chrome
    chrome_path = ""
    if os.name == 'nt':
        candidatos = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.join(os.environ.get('LOCALAPPDATA', ''), r"Google\Chrome\Application\chrome.exe"),
        ]
        for p in candidatos:
            if os.path.exists(p):
                chrome_path = p
                break
    else:
        chrome_path = "google-chrome"

    if not chrome_path:
        print("No se encontro la ruta de Chrome nativo.")
        return False

    # 3. Cerrar instancias huerfanas y levantar Chrome nuevo
    if os.name == 'nt':
        _cerrar_chrome_forzado()

    comando = f'"{chrome_path}" --remote-debugging-port=9222 --user-data-dir="{profile_path}"'
    print("Levantando sesion nativa de Chrome en puerto 9222...")
    subprocess.Popen(comando, shell=True)
    time.sleep(4)
    return True

def _crear_driver(profile_path: str):
    """Crea y retorna un objeto WebDriver conectado a la sesion nativa."""
    if _abrir_chrome_debug_mode(profile_path):
        opts = Options()
        opts.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
        return webdriver.Chrome(options=opts)
    else:
        print("Usando metodo clasico de webdriver...")
        opts = Options()
        opts.add_argument(f"--user-data-dir={profile_path}")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)

# ---------------------------------------------------------------------------
# Singleton del WebDriver
# ---------------------------------------------------------------------------
_shared_driver = None

def _obtener_driver():
    """
    Retorna el driver compartido, creando uno nuevo si no existe o si la
    sesion anterior murio (p.ej. el usuario cerro Chrome manualmente).
    """
    global _shared_driver
    profile_path = _get_profile_path()

    if _shared_driver is not None:
        try:
            _ = _shared_driver.title
        except Exception:
            print("La sesion de Chrome anterior expiro. Reiniciando...")
            _shared_driver = None

    if _shared_driver is None:
        _shared_driver = _crear_driver(profile_path)

    # Enfocar una pestana visible (no de extensiones ni devtools)
    try:
        for handle in _shared_driver.window_handles:
            _shared_driver.switch_to.window(handle)
            url_actual = _shared_driver.current_url
            if not url_actual.startswith("chrome-extension://") and "devtools://" not in url_actual:
                break
    except Exception as e:
        print(f"No se pudo seleccionar pestana valida: {e}")

    return _shared_driver

def _invalidar_driver():
    """Fuerza que en la proxima llamada se cree un driver nuevo."""
    global _shared_driver
    _shared_driver = None

# ---------------------------------------------------------------------------
# Motor generico de interaccion con cualquier IA web
# ---------------------------------------------------------------------------

def _enviar_prompt(
    driver,
    prompt: str,
    url: str,
    nombre_ia: str,
    selector_caja_by: By,
    selector_caja_valor: str,
    selector_respuesta_css: str,
    selector_boton_enviar: str = None,
    timeout_espera_caja: int = 60,
    timeout_respuesta: int = 180,
) -> str:
    """Motor universal: navega, pega el prompt y lee la respuesta.
    Robusto ante pérdida de foco del usuario (otro navegador abierto, etc.).
    """

    # 1. Navegar SIEMPRE a la URL de destino y forzar foco de ventana
    print(f"Navegando hacia {nombre_ia}: {url}")
    try:
        # Enfocar la ventana correcta de Chrome antes de navegar
        for handle in driver.window_handles:
            driver.switch_to.window(handle)
            current = driver.current_url
            if not current.startswith("chrome-extension://") and "devtools://" not in current:
                break
        driver.maximize_window()
        # Invocar el foco a nivel del sistema operativo via JS
        driver.execute_script("window.focus();")
    except:
        pass
    driver.get(url)
    time.sleep(4)  # Pausa extra para carga completa (especialmente Gemini)

    # 2. Esperar la caja de texto
    print(f"Buscando caja de texto en {nombre_ia}...")
    text_area = None
    deadline = time.time() + timeout_espera_caja

    while time.time() < deadline:
        try:
            text_area = WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable((selector_caja_by, selector_caja_valor))
            )
            break
        except:
            tiempo_restante = int(deadline - time.time())
            if tiempo_restante % 10 == 0:
                print(f"Esperando caja de {nombre_ia}... ({tiempo_restante}s restantes)")
            time.sleep(1)

    if not text_area:
        return f"❌ Error: No se encontro la caja de chat de {nombre_ia} en {timeout_espera_caja}s. ¿Hay un pop-up o login bloqueando?"

    # 3. Pegar el prompt con foco forzado (resistente a interferencia del usuario)
    print(f"Pegando prompt en {nombre_ia}...")
    pyperclip.copy(prompt)

    # Forzar foco sobre el elemento via JS antes de interactuar
    try:
        driver.execute_script("""
            window.focus();
            arguments[0].focus();
            arguments[0].click();
        """, text_area)
    except:
        pass
    time.sleep(0.5)

    # Intentar Ctrl+V (método principal)
    ctrl = Keys.COMMAND if (os.name == 'posix' and 'darwin' in os.uname().sysname.lower()) else Keys.CONTROL
    texto_insertado = False
    try:
        text_area.send_keys(ctrl, 'v')
        time.sleep(0.8)
        # Verificar que el texto se insertó revisando el contenido inner del elemento
        contenido_actual = driver.execute_script(
            "return arguments[0].innerText || arguments[0].value || '';", text_area
        )
        if len(contenido_actual.strip()) > 5:
            texto_insertado = True
            print(f"Texto insertado via Ctrl+V ({len(contenido_actual)} chars).")
    except Exception as e:
        print(f"Ctrl+V falló: {e}")

    # Fallback 1: document.execCommand (funciona en contenteditable)
    if not texto_insertado:
        print("Intentando fallback execCommand...")
        try:
            driver.execute_script("""
                arguments[0].focus();
                document.execCommand('selectAll', false, null);
                document.execCommand('insertText', false, arguments[1]);
            """, text_area, prompt)
            time.sleep(0.8)
            contenido_actual = driver.execute_script(
                "return arguments[0].innerText || arguments[0].value || '';", text_area
            )
            if len(contenido_actual.strip()) > 5:
                texto_insertado = True
                print(f"Texto insertado via execCommand ({len(contenido_actual)} chars).")
        except Exception as e:
            print(f"execCommand falló: {e}")

    # Fallback 2: send_keys char por char (lento pero confiable)
    if not texto_insertado:
        print("Intentando fallback send_keys directo (puede ser lento)...")
        try:
            driver.execute_script("arguments[0].focus();", text_area)
            # Enviar solo los primeros 4000 chars para no bloquear
            text_area.send_keys(prompt[:4000])
            texto_insertado = True
        except Exception as e:
            print(f"send_keys directo falló: {e}")

    if not texto_insertado:
        return f"❌ Error: No se pudo insertar el prompt en {nombre_ia} (todos los métodos fallaron)."

    time.sleep(0.8)

    # 4. Enviar el prompt (siempre por JS para evitar problemas de foco)
    enviado = False
    if selector_boton_enviar:
        try:
            print("Buscando botón de enviar...")
            boton = WebDriverWait(driver, 8).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, selector_boton_enviar))
            )
            # JS click es más fiable que .click() cuando la ventana no tiene foco del OS
            driver.execute_script("arguments[0].click();", boton)
            enviado = True
            print("Botón de enviar presionado.")
        except Exception as e:
            print(f"Botón no encontrado ({e}), usando Enter como respaldo.")

    if not enviado:
        try:
            driver.execute_script("""
                arguments[0].focus();
                arguments[0].dispatchEvent(new KeyboardEvent('keydown', {
                    key: 'Enter', code: 'Enter', keyCode: 13, bubbles: true
                }));
            """, text_area)
            time.sleep(0.3)
            # Fallback final: send_keys Enter
            text_area.send_keys(Keys.ENTER)
        except:
            pass

    time.sleep(2)

    # 5. Esperar y leer la respuesta
    print(f"Esperando respuesta de {nombre_ia}...")
    try:
        WebDriverWait(driver, timeout_respuesta).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector_respuesta_css))
        )
    except Exception:
        return f"❌ Error: {nombre_ia} no dio respuesta en {timeout_respuesta}s."

    stable_count = 0
    last_len = 0
    for _ in range(150):
        bloques = driver.find_elements(By.CSS_SELECTOR, selector_respuesta_css)
        if not bloques:
            time.sleep(1)
            continue
        texto = bloques[-1].text
        cur_len = len(texto)
        if cur_len == last_len and cur_len > 15:
            stable_count += 1
        else:
            stable_count = 0
            last_len = cur_len
        print(f"Generando... {cur_len} chars (estabilidad {stable_count}/5)", end="\r")
        if stable_count >= 5:
            break
        time.sleep(2)

    respuesta_final = driver.find_elements(By.CSS_SELECTOR, selector_respuesta_css)[-1].text
    print(f"\nRespuesta de {nombre_ia} recibida ({len(respuesta_final)} chars).")
    return respuesta_final

# ---------------------------------------------------------------------------
# Funciones publicas por IA
# ---------------------------------------------------------------------------

def ask_chatgpt_web(prompt: str) -> str:
    """Envia un prompt a ChatGPT y devuelve la respuesta en texto."""
    try:
        driver = _obtener_driver()
        return _enviar_prompt(
            driver=driver,
            prompt=prompt,
            url="https://chatgpt.com/?model=auto",
            nombre_ia="ChatGPT",
            selector_caja_by=By.ID,
            selector_caja_valor="prompt-textarea",
            selector_respuesta_css="div[data-message-author-role='assistant']",
            selector_boton_enviar="button[data-testid='send-button']",
        )
    except Exception as e:
        print(f"Error ChatGPT: {e}")
        _invalidar_driver()
        return f"Error ejecutando ChatGPT Web: {e}"

def ask_gemini_web(prompt: str) -> str:
    """Envia un prompt a Gemini y devuelve la respuesta en texto."""
    try:
        driver = _obtener_driver()
        return _enviar_prompt(
            driver=driver,
            prompt=prompt,
            url="https://gemini.google.com/app",
            nombre_ia="Gemini",
            selector_caja_by=By.CSS_SELECTOR,
            # Múltiples candidatos para mayor robustez ante cambios de UI de Google
            selector_caja_valor=(
                ".ql-editor[contenteditable='true'], "
                "rich-textarea [contenteditable='true'], "
                "[data-placeholder][contenteditable='true'], "
                "div.input-area-container [contenteditable='true']"
            ),
            selector_respuesta_css=(
                "message-content, "
                ".model-response-text, "
                ".response-content"
            ),
            selector_boton_enviar=(
                "button.send-button, "
                "button[aria-label='Enviar mensaje'], "
                "button[aria-label='Send message'], "
                "button[mattooltip='Enviar mensaje'], "
                "button[mattooltip='Send message']"
            ),
            timeout_espera_caja=75,   # Gemini a veces tarda más en cargar
            timeout_respuesta=210,    # Respuestas largas de JSON pueden tardar más
        )
    except Exception as e:
        print(f"Error Gemini: {e}")
        _invalidar_driver()
        return f"Error ejecutando Gemini Web: {e}"

# ---------------------------------------------------------------------------
# Test rapido
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    resp = ask_chatgpt_web("Hola, dime en 2 lineas que es la programacion.")
    print("\nRespuesta:\n", resp)
