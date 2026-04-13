# 🤖 Vader_Brain — Asistente IA Local de Documentos Office

Vader_Brain es un agente de IA de escritorio que combina una **IA local (Ollama)** con **Gemini/ChatGPT vía Selenium** para crear documentos Office de alta calidad (Word, Excel, PowerPoint) con solo describirlos en lenguaje natural.

Cuenta con una **interfaz gráfica moderna** (`CustomTkinter`) y un sistema de **tres niveles de generación** que escala la potencia de la IA según la complejidad de tu pedido.

---

## 🏗 Arquitectura

```text
Vader_Brain/
│
├── main.py              # Core: Ollama + comandos base (leer, listar, txt)
├── config.py            # Rutas del sandbox y configuración de Ollama
├── sandbox.py           # Resolución segura de rutas (previene path traversal)
├── gui.py               # Interfaz gráfica (punto de entrada principal)
├── requirements.txt     # Dependencias del proyecto
│
└── tools/               # Skills del agente
    ├── ai_tools.py      # 🧠 Dispatcher + Deep Research para Word, Excel y PPT
    ├── web_ai_tools.py  # 🌐 Conexión Selenium con Gemini y ChatGPT
    ├── word_tools.py    # 📄 Generador Word con formato APA completo
    ├── excel_tools.py   # 📊 Generador Excel multi-hoja con auto-formato
    └── ppt_tools.py     # 📊 Generador PPT con slides, tablas y referencias
```

```text
outputs/     # Archivos generados por el agente
inputs/      # Archivos a analizar o mejorar
templates/   # Plantillas base de Office
temp/        # Archivos temporales
```

---

## ⚙️ Tres Niveles de Generación

El `dispatcher_ia` escala automáticamente la complejidad según tu instrucción:

| Nivel | Activador | Motor | Descripción |
|---|---|---|---|
| **Básico** | Instrucción corta (<80 chars) | Ollama (local) | Rápido y privado. Sin internet. |
| **Complejo** | Instrucción larga o keywords (`detallado`, `con referencias`, `formato apa`…) | Gemini (web) | Una llamada a Gemini, JSON estructurado. |
| **Deep Research** | Keywords explícitas (`investiga a fondo`, `deep research`, `análisis profundo`, `reporte completo`, `con tablas de datos`…) | Gemini (web, iterativo) | Múltiples llamadas: primero planifica el índice, luego genera cada sección/hoja/slide por separado. |

### Soporte completo por tipo de documento:

| Tipo | Básico | Complejo | Deep Research |
|---|---|---|---|
| **Word** (.docx) | ✅ Ollama | ✅ Gemini JSON | ✅ Iterativo por secciones |
| **Excel** (.xlsx) | ✅ Plantilla base | ✅ Gemini JSON | ✅ Iterativo hoja por hoja |
| **PowerPoint** (.pptx) | ✅ Gemini JSON | ✅ Gemini JSON | ✅ Iterativo slide por slide |

---

## 📦 Instalación

### Paso 1: Ollama (IA local opcional)
1. Descarga e instala [Ollama](https://ollama.com/).
2. Descarga el modelo `llama3`:
   ```bash
   ollama run llama3
   ```
   *(Ollama corre en `http://localhost:11434` por defecto. Se usa para clasificar intenciones y tareas simples.)*

### Paso 2: Google Chrome
Selenium abre Chrome para interactuar con Gemini o ChatGPT. La primera vez que uses un skill avanzado, **inicia sesión manualmente** en la ventana que se abre; la sesión queda guardada en un perfil dedicado (`ChromeBotProfile`).

> **Motor por defecto: Gemini.** Si quieres usar ChatGPT explícitamente, menciona "chatgpt" en tu instrucción.

### Paso 3: Entorno Python
```bash
conda create -n vader python=3.11
conda activate vader
pip install -r requirements.txt
```

---

## 🚀 Ejecución

Usa el lanzador automático (instala dependencias y abre la GUI):
```bash
iniciar_vader_brain.bat
```

O directamente:
```bash
python gui.py
```

---

## 💬 Ejemplos de Instrucciones

### ⚡ Rápido (Ollama local)
```
Hazme un informe en word sobre finanzas descentralizadas.
Muestra los archivos en la carpeta.
```

### 🔵 Complejo (Gemini, una llamada)
```
Créame un word detallado sobre el mercado del litio en Chile con referencias APA.
Crea una presentación sobre el futuro de la IA con datos reales.
Genera un excel con datos reales sobre exportaciones chilenas del 2020 al 2024. Llámale 'Exportaciones_Chile'.
```

### 🔴 Deep Research (Gemini, iterativo — múltiples llamadas)
```
Investiga a fondo el impacto de la inteligencia artificial en el mercado laboral y hazme un word.
Deep research sobre la adopción de criptomonedas en Latinoamérica en formato ppt.
Análisis profundo del sistema financiero chileno con múltiples hojas en excel.
Reporte completo sobre establecoins y su regulación global en word con tablas de datos.
```

### 🔧 Otras acciones
```
Revisa el archivo reporte.txt y mejóralo.
Resume la web https://www.bcch.cl/
Pregúntale a gemini qué es la tasa de política monetaria.
```

---

## 🧩 Modo Desarrollador: Añadir un nuevo Skill

La arquitectura es modular. Para añadir, por ejemplo, soporte a PDFs:

**1. Crea la herramienta** en `tools/pdf_tools.py`:
```python
from sandbox import resolve_path

def crear_pdf_desde_json(filename, json_data):
    filepath = resolve_path(filename)
    # lógica con reportlab...
    return f"PDF creado en {filepath}"
```

**2. Crea la función de orquestación con Deep Research** en `tools/ai_tools.py`:
```python
from tools.pdf_tools import crear_pdf_desde_json

def cmd_crear_pdf_deep_research(instruccion: str, filename: str, motor: str = "gemini") -> str:
    # Paso 1: pedir índice de secciones
    prompt_indice = (
        f"Planifica las secciones de un PDF ejecutivo sobre: '{instruccion}'.\n"
        f"CRÍTICO: Responde ÚNICAMENTE con array JSON. Sin markdown.\n"
        f"[{{\"seccion\": \"1. Introducción\"}}, {{\"seccion\": \"2. Análisis\"}}]"
    )
    resp = enviar_a_ia_externa(prompt_indice, motor)
    indice = json.loads(limpiar_json_de_chatgpt(resp))

    # Paso 2: generar cada sección
    pdf_json = []
    for item in indice:
        # ... prompt por sección y acumulación de bloques
        pass

    return crear_pdf_desde_json(filename, json.dumps(pdf_json))
```

**3. Añádelo al Dispatcher** en `dispatcher_ia()`:
```python
elif tipo_documento == "PDF":
    tema, nombre_limpio = _extraer_tema_y_nombre("tema_general")
    if es_deep_research:
        return cmd_crear_pdf_deep_research(instruccion, f"{nombre_limpio}.pdf", motor=motor_ia)
    # ...
```

---

## 📋 Dependencias

| Paquete | Uso |
|---|---|
| `python-docx` | Generación de documentos Word con formato APA |
| `python-pptx` | Creación de presentaciones PowerPoint |
| `openpyxl` | Generación y formato de archivos Excel |
| `lxml` | Manipulación XML de celdas de tabla en PPT |
| `customtkinter` | Interfaz gráfica moderna |
| `selenium` | Automatización de Chrome para Gemini/ChatGPT |
| `webdriver-manager` | Gestión automática del ChromeDriver |
| `pyperclip` | Pegado de prompts en el navegador |
| `requests` | Comunicación con Ollama API |
| `beautifulsoup4` | Extracción de texto de páginas web |
| `pandas` | Utilidades de datos |
