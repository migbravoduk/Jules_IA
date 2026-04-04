import os
from pathlib import Path

# Directorio raíz del proyecto
PROJECT_ROOT = Path(__file__).parent.resolve()

# Configuración de los directorios del sandbox (BASE_DIRS)
BASE_DIRS = {
    "proyecto": PROJECT_ROOT,
    "templates": PROJECT_ROOT / "templates",
    "outputs": PROJECT_ROOT / "outputs",
    "inputs": PROJECT_ROOT / "inputs",
    "temp": PROJECT_ROOT / "temp"
}

# Configuración de Ollama local
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3"

# Configuración de URLs de Gems Especializados de Gemini (Deep Research)
# Reemplaza estas URLs con los enlaces directos a tus Gems personalizados en tu cuenta de Gemini Advanced.
# Por defecto apuntan a la página de inicio normal de Gemini.
GEMINI_GEMS = {
    "finanzas": "https://gemini.google.com/app",
    "fintech": "https://gemini.google.com/app",
    "blockchain": "https://gemini.google.com/app",
    "quantum": "https://gemini.google.com/app",
    "riesgos": "https://gemini.google.com/app",
    "codigo": "https://gemini.google.com/app",
    "default": "https://gemini.google.com/app"
}

# Asegurar que los directorios base existan (Sandbox setup)
def init_directories():
    """Crea los directorios base si no existen."""
    for key, path in BASE_DIRS.items():
        if key != "proyecto": # El directorio del proyecto ya existe
            path.mkdir(parents=True, exist_ok=True)

# Llama a la inicialización al cargar la configuración
init_directories()
