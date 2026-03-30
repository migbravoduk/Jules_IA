Agente IA Local de Archivos (Ollama + ChatGPT Web + Office)
Este proyecto es una aplicación local en Python que funciona como un agente de archivos impulsado por Inteligencia Artificial. Combina lo mejor de dos mundos:

IA Local (Ollama): Actúa como el orquestador principal, resuelve tareas sencillas (resúmenes rápidos, listar archivos) y mantiene tu privacidad.
IA Externa (ChatGPT vía Selenium): Se invoca automáticamente para tareas complejas que requieren mucho razonamiento estructurado (como generar presentaciones PowerPoint completas, informes de Word extensos o bases de datos complejas en Excel), evitando las alucinaciones típicas de los modelos locales en tareas de largo aliento.
Permite la manipulación avanzada de documentos de Word, Excel y PowerPoint mediante una interfaz gráfica amigable (CustomTkinter) y un dispatcher de IA que interpreta instrucciones en lenguaje natural.

1. Arquitectura del Proyecto
El proyecto está diseñado bajo una arquitectura modular, lo que garantiza extensibilidad y separación de responsabilidades. Se implementa un "sandbox" (entorno seguro) mediante la función resolve_path() y BASE_DIRS para evitar la modificación de archivos fuera de las carpetas designadas.

project/
│
├── main.py              # Lógica core, conexión con Ollama y funciones base (cmd_*)
├── config.py            # Configuración de rutas seguras (BASE_DIRS) y URL de Ollama
├── sandbox.py           # Resolución de rutas seguras dentro del sandbox
├── gui.py               # Interfaz gráfica moderna con CustomTkinter
├── requirements.txt     # Dependencias del proyecto
├── README.md            # Documentación
│
├── tools/               # Módulos de manipulación de archivos y orquestación
│   ├── word_tools.py    # Funciones para crear Words (básicos y complejos desde JSON)
│   ├── excel_tools.py   # Funciones para Excel (básicos y complejos desde JSON)
│   ├── ppt_tools.py     # Funciones para PowerPoint (básicos y complejos desde JSON)
│   ├── web_ai_tools.py  # Conexión con ChatGPT Web usando Selenium (El "Skill" externo)
│   ├── ai_tools.py      # Dispatcher de IA (interpreta prompts y decide qué IA usar)
│
├── templates/           # Directorio para plantillas de Office (Sandbox)
├── outputs/             # Directorio principal para salida de archivos (Sandbox)
├── temp/                # Directorio para archivos temporales (Sandbox)
2. Instalación (Anaconda + Pip + Ollama + Chrome)
Paso 1: Instalar Ollama localmente
Descarga e instala Ollama.
Abre una terminal y descarga el modelo llama3:
ollama run llama3
Nota: Asegúrate de que el servicio de Ollama esté ejecutándose (por defecto en http://localhost:11434).
Paso 2: Requisitos para IA Externa (Selenium)
El módulo de IA Externa requiere tener el navegador Google Chrome instalado en tu PC, ya que Selenium abrirá una ventana para interactuar con ChatGPT en tu nombre. La primera vez que uses un comando complejo, el navegador se abrirá pidiéndote iniciar sesión manualmente en ChatGPT. Solo debes hacerlo una vez, ya que guardará la sesión en un perfil de Chrome local dedicado.

Paso 3: Configurar el entorno en Python
Abre tu terminal o Anaconda Prompt.
Crea un entorno virtual (opcional pero recomendado):
conda create -n agente_ia python=3.11
conda activate agente_ia
Instala todas las dependencias:
pip install -r requirements.txt
3. Ejecución
Modo Interfaz Gráfica (GUI)
Para abrir la interfaz amigable, ejecuta:

python gui.py
Desde la GUI podrás seleccionar archivos del sandbox y enviar instrucciones en lenguaje natural en la caja de texto.

Modo Script (Backend)
Puedes importar e invocar las funciones directamente desde un script de Python:

from tools.ai_tools import dispatcher_ia
print(dispatcher_ia("crear ppt compleja sobre el futuro del trabajo"))
4. Ejemplos de Uso (En la GUI o vía Dispatcher)
El dispatcher_ia decide inteligentemente a qué módulo llamar.

Comandos Locales Básicos (Usan Ollama o lógica interna):

"Muestra los archivos en la carpeta" -> Lista el contenido de outputs/.
"Hazme un informe en word sobre finanzas descentralizadas." -> Genera un Word básico usando Ollama.
"Escribe un tema sobre inteligencia artificial en un archivo." -> Genera un archivo .txt usando Ollama.
Comandos Complejos (Usan ChatGPT Web vía Selenium): Si el agente detecta palabras como "complejo", "extenso" o explícitamente "chatgpt", delegará el trabajo "pesado" a ChatGPT para asegurar estructura y evitar alucinaciones, recibiendo la respuesta en JSON y ensamblándola en tu PC.

"Crear ppt compleja sobre la historia de Roma" -> Abre Chrome, le pide a ChatGPT la estructura JSON de la PPT, y luego arma el archivo .pptx diapositiva por diapositiva.
"Genera un word complejo sobre el cambio climático" -> Crea un documento extenso con títulos, subtítulos y listas basado en IA web.
"Quiero un excel complejo sobre un balance financiero anual" -> Crea un .xlsx con hojas separadas y datos estructurados usando IA web.
"Preguntale a chatgpt cómo se hace una tarta de manzana" -> Envía un prompt directo y te devuelve la respuesta en la consola.
5. Instructivo: Cómo agregar una nueva Función (SKILL)
La arquitectura modular permite que agregar nuevas habilidades sea muy fácil.

Supongamos que queremos agregar un skill para Generar un Resumen Ejecutivo en PDF usando la IA Externa.

1. Crear la herramienta en tools/ Crea (o edita) un archivo, ej. tools/pdf_tools.py, y define tu función pura para generar el archivo:

from sandbox import resolve_path
# import librerias_pdf...

def crear_pdf_desde_json(filename, json_data):
    filepath = resolve_path(filename)
    # logica para armar el PDF...
    return f"PDF creado en {filepath}"
2. Orquestar la llamada a ChatGPT (si es complejo) En tools/ai_tools.py (o en un nuevo archivo de comandos), crea el "comando" que usa ask_chatgpt_web:

from tools.web_ai_tools import ask_chatgpt_web, limpiar_json_de_chatgpt
from tools.pdf_tools import crear_pdf_desde_json

def cmd_crear_pdf_complejo(instruccion, filename):
    prompt = f"Genera un resumen ejecutivo en JSON sobre: {instruccion}. Formato: {{\"titulo\": \"...\", \"cuerpo\": \"...\"}}"
    respuesta_ia = ask_chatgpt_web(prompt)
    if "❌ Error" in respuesta_ia: return respuesta_ia

    json_limpio = limpiar_json_de_chatgpt(respuesta_ia)
    return crear_pdf_desde_json(filename, json_limpio)
3. Integrarla al Dispatcher de IA (tools/ai_tools.py) Añade la condición al dispatcher_ia para que el usuario pueda usarlo:

def dispatcher_ia(instruccion):
    instruccion_lower = instruccion.lower()
    # ... código existente ...

    elif "pdf complejo" in instruccion_lower:
        return cmd_crear_pdf_complejo(instruccion, "nuevo_resumen.pdf")

    # ...
4. ¡Listo! Ahora el usuario solo debe abrir gui.py y escribir: "Haz un pdf complejo sobre la revolución industrial", y el agente se encargará del resto de forma autónoma.
