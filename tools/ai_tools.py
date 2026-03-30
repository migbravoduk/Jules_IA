from main import (
    cmd_listar, cmd_leer, cmd_crear_tema, cmd_resumir,
    cmd_reescribir, cmd_abrir_web, cmd_resumir_web,
    cmd_crear_docx_profesional, cmd_escribir_excel,
    cmd_formatear_excel, cmd_actualizar_ppt
)
from tools.web_ai_tools import ask_chatgpt_web
from tools.ppt_tools import crear_ppt_compleja_desde_json
from tools.word_tools import crear_word_complejo_desde_json
from tools.excel_tools import crear_excel_complejo_desde_json
import re
import json

def limpiar_json_de_chatgpt(respuesta: str) -> str:
    """Limpia la respuesta de ChatGPT si viene con bloques Markdown de código."""
    texto_json = respuesta.strip()
    if texto_json.startswith("```json"):
        texto_json = texto_json[7:]
    elif texto_json.startswith("```"):
         texto_json = texto_json[3:]
    if texto_json.endswith("```"):
        texto_json = texto_json[:-3]
    return texto_json.strip()

def cmd_crear_ppt_compleja_con_chatgpt(instruccion: str, filename: str) -> str:
    """Orquesta la creación de una PPT compleja usando ChatGPT vía Selenium."""
    prompt = (
        f"Actúa como un experto creador de presentaciones profesionales. "
        f"El usuario te pide lo siguiente: '{instruccion}'. "
        f"Genera la estructura de la presentación estrictamente en formato JSON, "
        f"sin explicaciones adicionales, sin bloques de código Markdown, SOLO EL JSON PURO. "
        f"El JSON debe ser un array de objetos. El primer objeto debe ser tipo portada, los demás tipo contenido. "
        f"Formato esperado:\n"
        f"[\n"
        f"  {{\"tipo\": \"portada\", \"titulo\": \"...\", \"subtitulo\": \"...\"}},\n"
        f"  {{\"tipo\": \"contenido\", \"titulo\": \"...\", \"viñetas\": [\"...\", \"...\"]}}\n"
        f"]"
    )

    # 1. Llamar a ChatGPT
    respuesta = ask_chatgpt_web(prompt)
    if respuesta.startswith("❌"):
        return respuesta

    # 2. Limpiar respuesta
    texto_json = limpiar_json_de_chatgpt(respuesta)

    # 3. Crear PPT
    return crear_ppt_compleja_desde_json(filename, texto_json)

def cmd_crear_word_complejo_con_chatgpt(instruccion: str, filename: str) -> str:
    """Orquesta la creación de un Word complejo usando ChatGPT vía Selenium."""
    prompt = (
        f"Actúa como un experto redactor de informes profesionales. "
        f"El usuario te pide lo siguiente: '{instruccion}'. "
        f"Genera la estructura de un documento extenso estrictamente en formato JSON, "
        f"sin explicaciones adicionales, sin bloques de código Markdown, SOLO EL JSON PURO. "
        f"Formato esperado:\n"
        f"[\n"
        f"  {{\"tipo\": \"titulo\", \"texto\": \"Título Principal\"}},\n"
        f"  {{\"tipo\": \"subtitulo\", \"texto\": \"Sección 1\"}},\n"
        f"  {{\"tipo\": \"parrafo\", \"texto\": \"Contenido del párrafo...\"}},\n"
        f"  {{\"tipo\": \"lista\", \"items\": [\"Punto 1\", \"Punto 2\"]}}\n"
        f"]"
    )
    respuesta = ask_chatgpt_web(prompt)
    if respuesta.startswith("❌"):
        return respuesta
    texto_json = limpiar_json_de_chatgpt(respuesta)
    return crear_word_complejo_desde_json(filename, texto_json)

def cmd_crear_excel_complejo_con_chatgpt(instruccion: str, filename: str) -> str:
    """Orquesta la creación de un Excel complejo usando ChatGPT vía Selenium."""
    prompt = (
        f"Actúa como un analista de datos experto. "
        f"El usuario te pide generar un excel con lo siguiente: '{instruccion}'. "
        f"Genera la estructura de los datos estrictamente en formato JSON, "
        f"sin explicaciones adicionales, sin bloques de código Markdown, SOLO EL JSON PURO. "
        f"La respuesta debe ser una lista de hojas. Formato esperado:\n"
        f"[\n"
        f"  {{\"hoja\": \"Resumen Financiero\", \"datos\": [\n"
        f"      [\"Mes\", \"Ingresos\", \"Egresos\", \"Balance\"],\n"
        f"      [\"Enero\", 15000, 10000, 5000]\n"
        f"  ]}}\n"
        f"]"
    )
    respuesta = ask_chatgpt_web(prompt)
    if respuesta.startswith("❌"):
        return respuesta
    texto_json = limpiar_json_de_chatgpt(respuesta)
    return crear_excel_complejo_desde_json(filename, texto_json)

def dispatcher_ia(instruccion: str) -> str:
    """
    Dispatcher simple basado en palabras clave.
    Toma la instrucción del usuario en lenguaje natural y decide qué comando ejecutar.
    """
    instruccion_lower = instruccion.lower()

    # --- LISTAR ---
    if "lista" in instruccion_lower or "mostrar archivos" in instruccion_lower:
        return cmd_listar()

    # --- WORD COMPLEJO (CHATGPT) ---
    elif ("word complejo" in instruccion_lower or "informe complejo" in instruccion_lower or
          "documento extenso" in instruccion_lower or ("word" in instruccion_lower and "chatgpt" in instruccion_lower)):
        tema = "Tema general"
        match = re.search(r"sobre (.+?)( en word|\.docx|$)", instruccion_lower)
        if match:
            tema = match.group(1).strip()
        filename = f"{tema.replace(' ', '_')}_gpt.docx"
        return cmd_crear_word_complejo_con_chatgpt(instruccion, filename)

    # --- WORD BÁSICO (OLLAMA) ---
    elif "word" in instruccion_lower or "informe profesional" in instruccion_lower:
        tema = "Tema general"
        match = re.search(r"sobre (.+?)( en word| \.docx|$)", instruccion_lower)
        if match:
            tema = match.group(1).strip()

        filename = f"{tema.replace(' ', '_')}.docx"
        return cmd_crear_docx_profesional(titulo=f"Informe: {tema}", tema=tema, filename=filename)

    # --- EXCEL COMPLEJO (CHATGPT) ---
    elif ("excel complejo" in instruccion_lower or "datos complejos" in instruccion_lower or
          ("excel" in instruccion_lower and "chatgpt" in instruccion_lower)):
        tema = "datos_generados"
        match = re.search(r"sobre (.+?)( en excel|\.xlsx|$)", instruccion_lower)
        if match:
            tema = match.group(1).strip()
        filename = f"{tema.replace(' ', '_')}_gpt.xlsx"
        return cmd_crear_excel_complejo_con_chatgpt(instruccion, filename)

    # --- EXCEL BÁSICO ---
    elif "excel" in instruccion_lower:
        if "formato" in instruccion_lower or "formatear" in instruccion_lower:
            return "Comando de formatear Excel detectado. Falta implementar el flujo completo de selección de archivo."
        else:
             # Ejemplo genérico
             datos = [["Nombre", "Valor"], ["Dato A", 10], ["Dato B", 20]]
             return cmd_escribir_excel("ejemplo_generado.xlsx", "Hoja1", datos)

    # --- POWERPOINT COMPLEJO (NUEVO SKILL VÍA CHATGPT) ---
    elif ("ppt compleja" in instruccion_lower or "presentacion compleja" in instruccion_lower or
          ("ppt" in instruccion_lower and "chatgpt" in instruccion_lower)):
        tema = "Tema general"
        match = re.search(r"sobre (.+?)( en ppt|\.pptx|$)", instruccion_lower)
        if match:
            tema = match.group(1).strip()

        filename = f"{tema.replace(' ', '_')}_gpt.pptx"
        return cmd_crear_ppt_compleja_con_chatgpt(instruccion, filename)

    # --- POWERPOINT BÁSICO ---
    elif "ppt" in instruccion_lower or "presentacion" in instruccion_lower or "powerpoint" in instruccion_lower:
        return "Comando de actualizar PPT detectado. Falta el diccionario de reemplazos."

    # --- TXT / TEMAS ---
    elif "escribe" in instruccion_lower or "crea un tema" in instruccion_lower:
        match = re.search(r"sobre (.+?)( en un archivo|$)", instruccion_lower)
        tema = match.group(1).strip() if match else "Tema generico"
        filename = f"{tema.replace(' ', '_')}.txt"
        return cmd_crear_tema(tema, filename)

    # --- RESUMIR ---
    elif "resume" in instruccion_lower:
         if "web" in instruccion_lower or "http" in instruccion_lower:
             match = re.search(r"(https?://\S+)", instruccion_lower)
             if match:
                 return cmd_resumir_web(match.group(1))
             return "Comando de resumir web detectado, pero no encontré una URL válida."
         else:
             return "Comando de resumir archivo detectado. Falta el nombre del archivo."

    # --- PREGUNTA DIRECTA A CHATGPT (NUEVO) ---
    elif "preguntale a chatgpt" in instruccion_lower or "usar ia web" in instruccion_lower:
        prompt = instruccion.replace("preguntale a chatgpt", "").replace("usar ia web", "").strip()
        if not prompt:
             return "Por favor dime qué quieres preguntarle a ChatGPT."
        return ask_chatgpt_web(prompt)

    else:
        return f"Instrucción no reconocida o no soportada aún por el dispatcher.\nInstrucción recibida: {instruccion}"

# Prueba local
if __name__ == "__main__":
    print(dispatcher_ia("hazme un informe en word sobre stablecoins"))
