# Agente IA Local de Archivos (Ollama + ChatGPT Web + Office)

Este proyecto es una aplicación local en Python que funciona como un asistente inteligente de escritorio. Combina lo mejor de dos mundos para ayudarte a gestionar, crear y procesar archivos de Office y texto:

- **IA Local (Ollama):** Actúa como el orquestador principal. Es rápido, privado y resuelve tareas sencillas como resúmenes cortos, redacción básica y listar archivos de forma local.
- **IA Externa (ChatGPT vía Selenium):** Se invoca automáticamente como un "Skill Avanzado" para tareas complejas que requieren de mucho razonamiento estructurado o conocimiento de internet. Esto evita las alucinaciones típicas de los modelos locales al generar bases de datos enteras (Excel), presentaciones (PowerPoint) o informes extensos (Word).

Cuenta con una **interfaz gráfica amigable** (`CustomTkinter`) y un motor inteligente (`dispatcher_ia`) que interpreta tus instrucciones en lenguaje natural.

---

## 1. Arquitectura y Seguridad (Sandbox)

El proyecto está diseñado de forma modular, lo que garantiza extensibilidad. Además, implementa un **"sandbox"** (entorno seguro) a través del archivo `sandbox.py`. El agente solo puede crear, leer y modificar archivos dentro de las carpetas permitidas (por ejemplo, `outputs/`), evitando modificaciones accidentales en tu sistema.

```text
project/
│
├── main.py              # Lógica core, conexión con Ollama y funciones base
├── config.py            # Rutas seguras (BASE_DIRS) y URL de Ollama
├── sandbox.py           # Resolución de rutas (Previene Path Traversal)
├── gui.py               # Interfaz gráfica (Ejecuta esto para empezar)
├── README.md            # Documentación
│
├── tools/               # "Skills" del agente
│   ├── word_tools.py    # Crea Words (básicos y complejos vía JSON)
│   ├── excel_tools.py   # Crea Excels con múltiples hojas y auto-formato
│   ├── ppt_tools.py     # Crea PowerPoint y reemplaza variables
│   ├── web_ai_tools.py  # Conexión con ChatGPT Web usando Selenium
│   ├── ai_tools.py      # Dispatcher: El "Cerebro" que entiende tus intenciones
│
├── outputs/             # Directorio principal donde el agente guarda tus archivos
├── templates/           # Directorio para plantillas base de Office
├── temp/                # Directorio para archivos temporales
```

---

## 2. Instalación

### Paso 1: Instalar Ollama localmente
1. Descarga e instala [Ollama](https://ollama.com/).
2. Abre una terminal y descarga el modelo por defecto (`llama3`):
   ```bash
   ollama run llama3
   ```
   *(Asegúrate de que Ollama esté ejecutándose en segundo plano, por defecto en `http://localhost:11434`)*

### Paso 2: Requisitos para IA Externa (Selenium)
El módulo avanzado requiere tener **Google Chrome** instalado en tu PC. Selenium abrirá una ventana limpia para interactuar con ChatGPT por ti.
*Nota: La primera vez que pidas una tarea compleja, es posible que la consola te pida iniciar sesión manualmente en ChatGPT. Solo tendrás que hacerlo una vez; la sesión se guarda en un perfil local dedicado (`ChromeBotProfile`).*

### Paso 3: Configurar el entorno en Python
1. Abre tu terminal (ej. Anaconda Prompt).
2. Crea un entorno virtual (recomendado):
   ```bash
   conda create -n agente_ia python=3.11
   conda activate agente_ia
   ```
3. Instala todas las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

---

## 3. Ejecución

Para abrir la interfaz amigable, simplemente ejecuta:
```bash
python gui.py
```
Desde allí podrás ver tus archivos y escribir en la caja de texto lo que necesitas que el agente haga.

---

## 4. Ejemplos de Uso "Mágicos"

El `dispatcher_ia` es inteligente. Si tu instrucción es corta o básica, usará la IA Local (Ollama). **Si tu instrucción es larga (>80 caracteres), pide "investigar", crear algo "complejo" o menciona "noticias", activará automáticamente a ChatGPT.**

Además, **entiende cómo quieres llamar a los archivos** si lo pones entre comillas, e incluso añade fechas:

### ✨ Tareas Complejas (Se derivan a ChatGPT + Formato Office)
- **PowerPoint estructurado:**
  > *"Crear una ppt compleja sobre el futuro del trabajo y la inteligencia artificial."*
- **Investigación extensa en Word con fecha y nombre:**
  > *"Créame un word de las principales noticias del día sobre la guerra comercial entre potencias, y cómo se movieron las criptomonedas respecto a esto. Llámale al archivo 'Resumen Cripto' y añádele la fecha de hoy."*
  *(El agente generará el archivo `Resumen_Cripto_2026-03-30.docx` usando ChatGPT y le dará formato de títulos y párrafos justificados).*
- **Bases de datos en Excel:**
  > *"Quiero un excel complejo sobre un balance financiero anual con ingresos y gastos en una hoja, y recursos humanos en otra. Llámale 'Balance Anual'."*
- **Consulta directa web:**
  > *"Pregúntale a chatgpt cómo se hace una tarta de manzana."*

### ⚡ Tareas Locales Rápidas (Usan Ollama)
- **Gestión:**
  > *"Muestra los archivos en la carpeta"*
- **Creación básica:**
  > *"Hazme un informe en word sobre finanzas descentralizadas."*
- **Resumen:**
  > *(Selecciona un archivo en la GUI)* -> *"Resume el archivo"*

---

## 5. Modo Desarrollador: Cómo agregar una nueva Función (SKILL)

La arquitectura permite que agregar nuevas habilidades sea muy fácil. Aquí tienes un ejemplo para crear PDFs:

**1. Crea la herramienta en `tools/`** (ej. `tools/pdf_tools.py`):
```python
from sandbox import resolve_path

def crear_pdf_desde_json(filename, json_data):
    filepath = resolve_path(filename)
    # logica para armar el PDF usando alguna librería como reportlab...
    return f"PDF creado en {filepath}"
```

**2. Orquesta la llamada a ChatGPT** en `tools/ai_tools.py`:
```python
from tools.web_ai_tools import ask_chatgpt_web, limpiar_json_de_chatgpt
from tools.pdf_tools import crear_pdf_desde_json

def cmd_crear_pdf_complejo(instruccion, filename):
    prompt = f"Genera un resumen en JSON sobre: {instruccion}. Formato: {{\"titulo\": \"...\", \"cuerpo\": \"...\"}}"
    respuesta = ask_chatgpt_web(prompt)
    if "❌ Error" in respuesta: return respuesta
    return crear_pdf_desde_json(filename, limpiar_json_de_chatgpt(respuesta))
```

**3. Agrégalo al Dispatcher:**
```python
def dispatcher_ia(instruccion):
    instruccion_lower = instruccion.lower()
    # ... código existente ...

    # NUEVO SKILL:
    elif "pdf complejo" in instruccion_lower:
        nombre_limpio = obtener_nombre_seguro(instruccion, "resumen_pdf")
        return cmd_crear_pdf_complejo(instruccion, f"{nombre_limpio}.pdf")
```
¡Y listo! Ya puedes pedirle al agente en la GUI: *"Haz un pdf complejo sobre la revolución industrial"*.
