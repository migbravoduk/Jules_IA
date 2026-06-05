import os
import time
import subprocess
import urllib.request
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pyperclip

from config import (
    CHROME_PROFILE_PATH,
    TIMEOUT_ESPERA_CAJA,
    TIMEOUT_RESPUESTA,
    TIMEOUT_LOGIN_MANUAL,
)

# ---------------------------------------------------------------------------
# Utilidades de Chrome
# ---------------------------------------------------------------------------

def _get_profile_path() -> str:
    """Retorna la ruta del perfil dedicado de Chrome para el bot."""
    os.makedirs(CHROME_PROFILE_PATH, exist_ok=True)
    return CHROME_PROFILE_PATH


def _cerrar_chrome_del_perfil(profile_path: str):
    """
    Cierra ÚNICAMENTE los procesos de Chrome que están usando el perfil del bot,
    para liberar el lock del perfil sin tocar las demás ventanas de Chrome del
    usuario. En versiones antiguas de Windows recurre a un filtrado por título.
    """
    if os.name != 'nt':
        return
    # Marcador único de la ruta del perfil para identificar SOLO el Chrome del bot.
    marcador = os.path.basename(profile_path.rstrip("\\/")) or "ChromeBotProfile"
    ps_cmd = (
        "Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\" | "
        f"Where-Object {{ $_.CommandLine -like '*{marcador}*' }} | "
        "ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
    )
    try:
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_cmd],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15
        )
    except Exception as e:
        print(f"No se pudo cerrar el Chrome del perfil del bot: {e}")
    time.sleep(1)


def _abrir_chrome_debug_mode(profile_path: str) -> bool:
    """
    Lanza Chrome nativo con el puerto de depuracion 9222 activado.
    Este metodo es el mas robusto contra Cloudflare porque usa el ejecutable
    real de Chrome en un proceso separado al de webdriver.
    """
    # 1. Verificar si ya esta corriendo en el puerto 9222
    try:
        urllib.request.urlopen("http://127.0.0.1:9222/json", timeout=1)
        print("Chrome en modo debug ya esta corriendo.")
        return True
    except Exception:
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

    # 3. Cerrar SOLO instancias previas del bot (no las del usuario) y levantar Chrome
    _cerrar_chrome_del_perfil(profile_path)

    comando = f'"{chrome_path}" --remote-debugging-port=9222 --user-data-dir="{profile_path}"'
    print("Levantando sesion nativa de Chrome en puerto 9222...")
    subprocess.Popen(comando, shell=True)

    # Esperar a que el puerto de depuración responda (hasta ~10s)
    for _ in range(20):
        try:
            urllib.request.urlopen("http://127.0.0.1:9222/json", timeout=1)
            return True
        except Exception:
            time.sleep(0.5)
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


def _esperar_login_manual(driver, dominio_esperado: str, nombre_ia: str) -> bool:
    """
    Cuando se detecta una pantalla de login (Google u OpenAI), pausa y espera a
    que el usuario inicie sesion manualmente en la ventana de Chrome.
    Devuelve True si tras el login se llegó al dominio esperado.
    """
    print(f"  Pantalla de login de {nombre_ia} detectada.")
    print(f"  Inicia sesion manualmente en la ventana de Chrome "
          f"(espera hasta {TIMEOUT_LOGIN_MANUAL}s)...")
    deadline = time.time() + TIMEOUT_LOGIN_MANUAL
    while time.time() < deadline:
        if dominio_esperado in driver.current_url:
            print("[OK] Login completado. Continuando...")
            return True
        time.sleep(2)
    return False


def _es_pantalla_de_login(url: str, nombre_ia: str) -> bool:
    """Detecta URLs de login/autenticación de Google y OpenAI/ChatGPT."""
    url_l = url.lower()
    patrones_comunes = ["accounts.google.com", "google.com/signin"]
    patrones_chatgpt = ["auth.openai.com", "auth0.openai.com", "/auth/login", "login.openai", "platform.openai.com/login"]
    patrones = patrones_comunes + (patrones_chatgpt if nombre_ia.lower() == "chatgpt" else [])
    return any(p in url_l for p in patrones)


def _es_cloudflare(driver) -> bool:
    """Heurística para detectar el reto 'Just a moment...' de Cloudflare."""
    try:
        titulo = (driver.title or "").lower()
        if "just a moment" in titulo or "un momento" in titulo:
            return True
        cuerpo = driver.find_elements(By.CSS_SELECTOR, "#challenge-running, #cf-challenge-running")
        return len(cuerpo) > 0
    except Exception:
        return False

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
    selector_boton_stop: str = None,
    timeout_espera_caja: int = None,
    timeout_respuesta: int = None,
) -> str:
    """Motor universal: navega, pega el prompt y lee la respuesta.
    Robusto ante pérdida de foco del usuario, login y Cloudflare.
    """
    if timeout_espera_caja is None:
        timeout_espera_caja = TIMEOUT_ESPERA_CAJA
    if timeout_respuesta is None:
        timeout_respuesta = TIMEOUT_RESPUESTA

    # 1. Navegacion robusta: 3 metodos en cascada con verificacion de URL
    #    driver.get() en modo debug puede ejecutarse sin que Chrome navegue visualmente.
    dominio_esperado = url.split("/")[2]
    navegado = False

    for intento in range(3):
        url_antes = driver.current_url
        print(f"[Nav {intento+1}/3] Destino: {url} | URL actual: {url_antes}")
        try:
            if intento == 0:
                driver.get(url)
            elif intento == 1:
                print("  Intentando via JS window.location.href...")
                driver.execute_script("window.location.href = arguments[0];", url)
            else:
                print("  Abriendo nueva pestana y navegando...")
                driver.execute_script("window.open('');")
                time.sleep(1)
                driver.switch_to.window(driver.window_handles[-1])
                driver.get(url)
        except Exception as e:
            print(f"  Metodo {intento+1} fallo: {e}")

        # Esperar carga y verificar URL
        time.sleep(5)
        url_actual = driver.current_url
        print(f"  URL post-navegacion: {url_actual}")

        # Cloudflare: dar tiempo a que se resuelva el reto
        if _es_cloudflare(driver):
            print("  Reto de Cloudflare detectado. Esperando resolución (hasta 30s)...")
            cf_deadline = time.time() + 30
            while time.time() < cf_deadline and _es_cloudflare(driver):
                time.sleep(2)
            url_actual = driver.current_url

        if dominio_esperado in url_actual and not _es_pantalla_de_login(url_actual, nombre_ia):
            print(f"[OK] Navegacion exitosa hacia {nombre_ia}.")
            navegado = True
            break

        # Detectar pantalla de login (Google u OpenAI según el motor)
        if _es_pantalla_de_login(url_actual, nombre_ia):
            if _esperar_login_manual(driver, dominio_esperado, nombre_ia):
                navegado = True
                break

        print("  URL no corresponde al dominio esperado, reintentando...")

    if not navegado:
        _invalidar_driver()
        return (
            "❌ Error: No se pudo navegar a " + nombre_ia + " tras 3 intentos. "
            "URL final: " + driver.current_url + ". "
            "Se reiniciara Chrome en el siguiente intento."
        )

    time.sleep(2)  # Pausa extra para estabilizar pagina cargada

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
        except Exception:
            tiempo_restante = int(deadline - time.time())
            if tiempo_restante % 10 == 0:
                print(f"Esperando caja de {nombre_ia}... ({tiempo_restante}s restantes)")
            # Si durante la espera nos redirigen a login, gestionarlo
            url_ahora = driver.current_url
            if _es_pantalla_de_login(url_ahora, nombre_ia):
                if _esperar_login_manual(driver, dominio_esperado, nombre_ia):
                    deadline = time.time() + timeout_espera_caja  # reiniciar la espera
            time.sleep(1)

    if not text_area:
        return f"❌ Error: No se encontro la caja de chat de {nombre_ia} en {timeout_espera_caja}s. ¿Hay un pop-up o login bloqueando?"

    # 3. Pegar el prompt con foco forzado (resistente a interferencia del usuario)
    print(f"Pegando prompt en {nombre_ia}...")
    pyperclip.copy(prompt)

    try:
        driver.execute_script("""
            window.focus();
            arguments[0].focus();
            arguments[0].click();
        """, text_area)
    except Exception:
        pass
    time.sleep(0.5)

    # Intentar Ctrl+V (método principal)
    ctrl = Keys.COMMAND if (os.name == 'posix' and 'darwin' in os.uname().sysname.lower()) else Keys.CONTROL
    texto_insertado = False
    try:
        text_area.send_keys(ctrl, 'v')
        time.sleep(0.8)
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
            text_area.send_keys(Keys.ENTER)
        except Exception:
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

    respuesta_final = _leer_respuesta_estable(
        driver, selector_respuesta_css, selector_boton_stop, timeout_respuesta
    )
    print(f"\nRespuesta de {nombre_ia} recibida ({len(respuesta_final)} chars).")
    if not respuesta_final.strip():
        return f"❌ Error: {nombre_ia} devolvió una respuesta vacía."
    return respuesta_final


def _leer_respuesta_estable(driver, selector_respuesta_css, selector_boton_stop, timeout_respuesta) -> str:
    """
    Lee el último bloque de respuesta esperando a que el texto se estabilice.
    Si se conoce el botón de 'detener generación', su desaparición confirma el fin.
    """
    stable_count = 0
    last_len = 0
    max_iteraciones = max(int(timeout_respuesta / 2), 60)
    for _ in range(max_iteraciones):
        bloques = driver.find_elements(By.CSS_SELECTOR, selector_respuesta_css)
        if not bloques:
            time.sleep(1)
            continue
        texto = bloques[-1].text
        cur_len = len(texto)

        # ¿Sigue generando? (botón stop visible)
        generando = False
        if selector_boton_stop:
            try:
                generando = len(driver.find_elements(By.CSS_SELECTOR, selector_boton_stop)) > 0
            except Exception:
                generando = False

        if cur_len == last_len and cur_len > 15:
            stable_count += 1
        else:
            stable_count = 0
            last_len = cur_len

        print(f"Generando... {cur_len} chars (estabilidad {stable_count}/5)", end="\r")

        # Fin: texto estable y, si lo conocemos, sin botón de stop
        if stable_count >= 5 and not generando:
            break
        time.sleep(2)

    bloques = driver.find_elements(By.CSS_SELECTOR, selector_respuesta_css)
    return bloques[-1].text if bloques else ""

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
            selector_boton_stop="button[data-testid='stop-button'], button[aria-label='Detener generación'], button[aria-label='Stop generating']",
        )
    except Exception as e:
        print(f"Error ChatGPT: {e}")
        _invalidar_driver()
        return f"❌ Error ejecutando ChatGPT Web: {e}"

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
            selector_boton_stop=(
                "button[aria-label='Detener respuesta'], "
                "button[aria-label='Stop response'], "
                "button.stop"
            ),
            timeout_espera_caja=max(TIMEOUT_ESPERA_CAJA, 75),  # Gemini tarda más en cargar
            timeout_respuesta=max(TIMEOUT_RESPUESTA, 210),     # Respuestas largas de JSON
        )
    except Exception as e:
        print(f"Error Gemini: {e}")
        _invalidar_driver()
        return f"❌ Error ejecutando Gemini Web: {e}"

# ---------------------------------------------------------------------------
# Test rapido
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    resp = ask_chatgpt_web("Hola, dime en 2 lineas que es la programacion.")
    print("\nRespuesta:\n", resp)
