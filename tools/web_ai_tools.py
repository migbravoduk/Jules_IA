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

def ask_chatgpt_web(prompt_completo: str) -> str:
    """
    Lógica central de Selenium adaptada como herramienta (Skill).
    Recibe el prompt, abre ChatGPT, envía el texto y devuelve la respuesta como string.
    """
    # En Linux o entorno headless evitamos taskkill de Windows
    if os.name == 'nt':
        cerrar_chrome_forzado()

    # Configuración de perfil dedicado (adaptado multiplataforma)
    if os.name == 'nt':
        desktop = os.path.join(os.environ.get('USERPROFILE', ''), 'Desktop')
        profile_path = os.path.join(desktop, "ChromeBotProfile")
    else:
        # En Linux/Mac lo ponemos en una carpeta oculta del home
        profile_path = os.path.join(os.path.expanduser("~"), ".ChromeBotProfile")

    chrome_options = Options()
    chrome_options.add_argument(f"--user-data-dir={profile_path}")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-gpu")

    # IMPORTANTE: Si se corre en servidor/docker sin interfaz gráfica real, hay que añadir --headless
    # Como es un agente local para el PC del usuario, se espera que tenga UI (no headless por defecto)
    # Pero lo dejamos comentado por si acaso.
    # chrome_options.add_argument("--headless=new")

    driver = None
    try:
        print("🚀 Iniciando navegador para ChatGPT Web...")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.get("https://chatgpt.com/")

        wait = WebDriverWait(driver, 60)

        # 1. Buscar caja de chat
        try:
            text_area = wait.until(EC.presence_of_element_located((By.ID, "prompt-textarea")))
        except:
            print("\n🛑 Login requerido. Por favor inicia sesión manualmente ahora.")
            # input bloquea la ejecución, pero como esto se corre localmente desde CLI o GUI,
            # es la única forma de avisar al usuario para que se loguee la primera vez.
            input("Presiona ENTER en esta consola cuando veas el chat listo en Chrome...")
            text_area = driver.find_element(By.ID, "prompt-textarea")

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
