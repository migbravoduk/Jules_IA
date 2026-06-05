import os
from pathlib import Path

# Carga opcional de un archivo .env (si python-dotenv está instalado).
# Permite configurar el proyecto sin tocar el código.
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


def _env(nombre: str, defecto: str) -> str:
    """Lee una variable de entorno con un valor por defecto."""
    valor = os.environ.get(nombre)
    return valor if valor not in (None, "") else defecto


def _env_int(nombre: str, defecto: int) -> int:
    """Lee una variable de entorno entera con un valor por defecto."""
    try:
        return int(os.environ.get(nombre, defecto))
    except (TypeError, ValueError):
        return defecto


# Directorio raíz del proyecto
PROJECT_ROOT = Path(__file__).parent.resolve()

# Configuración de los directorios del sandbox (BASE_DIRS)
BASE_DIRS = {
    "proyecto": PROJECT_ROOT,
    "templates": PROJECT_ROOT / "templates",
    "outputs": PROJECT_ROOT / "outputs",
    "inputs": PROJECT_ROOT / "inputs",
    "temp": PROJECT_ROOT / "temp",
}

# ── Ollama (IA local) ──────────────────────────────────────────────
OLLAMA_URL = _env("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = _env("OLLAMA_MODEL", "llama3")
OLLAMA_TIMEOUT = _env_int("OLLAMA_TIMEOUT", 60)

# ── IA web (Selenium) ──────────────────────────────────────────────
# Motor por defecto cuando el usuario no especifica: "gemini" o "chatgpt".
MOTOR_IA_DEFECTO = _env("MOTOR_IA_DEFECTO", "gemini").lower()

# Timeouts de la interacción con la IA web (segundos)
TIMEOUT_ESPERA_CAJA = _env_int("TIMEOUT_ESPERA_CAJA", 60)
TIMEOUT_RESPUESTA = _env_int("TIMEOUT_RESPUESTA", 180)
# Tiempo de gracia para iniciar sesión manualmente en la ventana de Chrome.
TIMEOUT_LOGIN_MANUAL = _env_int("TIMEOUT_LOGIN_MANUAL", 180)

# Ruta del perfil dedicado de Chrome para el bot.
# Por defecto en %LOCALAPPDATA% (Windows) o ~/.cache (otros) para no
# ensuciar el Escritorio. Se puede sobreescribir con CHROME_PROFILE_PATH.
def _perfil_chrome_defecto() -> str:
    if os.name == "nt":
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    else:
        base = os.path.join(os.path.expanduser("~"), ".cache")
    return os.path.join(base, "VaderBrain", "ChromeBotProfile")


CHROME_PROFILE_PATH = _env("CHROME_PROFILE_PATH", _perfil_chrome_defecto())


# Asegurar que los directorios base existan (Sandbox setup)
def init_directories():
    """Crea los directorios base si no existen."""
    for key, path in BASE_DIRS.items():
        if key != "proyecto":  # El directorio del proyecto ya existe
            path.mkdir(parents=True, exist_ok=True)


# Llama a la inicialización al cargar la configuración
init_directories()
