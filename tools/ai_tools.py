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
import datetime
import string

def obtener_nombre_seguro(instruccion: str, fallback_tema: str) -> str:
    """
    Busca si el usuario pidió un nombre específico ("llámale al archivo 'X'").
    Limpia caracteres inválidos y añade la fecha si lo solicita.
    """
    nombre = fallback_tema

    # 1. Buscar nombre explícito
    match_nombre = re.search(r'll[aá]male[^\"]+?[\"\'](.+?)[\"\']', instruccion, flags=re.IGNORECASE)
    if not match_nombre:
        match_nombre = re.search(r'llamado[\s]+[\"\'](.+?)[\"\']', instruccion, flags=re.IGNORECASE)

    if match_nombre:
        nombre = match_nombre.group(1).strip()
    else:
        # Si usa el fallback_tema (que suele ser un pedazo largo de la instrucción)
        # lo truncamos a 40 caracteres máximo
        nombre = nombre[:40].strip()

    # 2. Reemplazar espacios por guiones bajos
    nombre = nombre.replace(" ", "_")

    # 3. Eliminar caracteres inválidos para Windows/Linux
    valid_chars = f"-_.() {string.ascii_letters}{string.digits}"
    nombre_limpio = ''.join(c for c in nombre if c in valid_chars)

    # 4. Añadir fecha si lo pide
    if "fecha de hoy" in instruccion.lower() or "añadele la fecha" in instruccion.lower() or "añádele la fecha" in instruccion.lower():
        fecha_str = datetime.datetime.now().strftime("%Y-%m-%d")
        nombre_limpio = f"{nombre_limpio}_{fecha_str}"

    return nombre_limpio

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

    # Variables de complejidad: si la instrucción tiene más de 80 caracteres o palabras clave "fuertes".
    es_complejo = len(instruccion) > 80 or any(kw in instruccion_lower for kw in [
        "complejo", "chatgpt", "extenso", "investiga", "noticias", "detallado", "creame un"
    ])

    # --- WORD ---
    if "word" in instruccion_lower or "informe" in instruccion_lower:
        tema = "Tema_general"
        match = re.search(r"sobre (.+?)(?:\.|,|$|ll[aá]male)", instruccion_lower)
        if match: tema = match.group(1).strip()
        nombre_limpio = obtener_nombre_seguro(instruccion, tema)

        if es_complejo:
            return cmd_crear_word_complejo_con_chatgpt(instruccion, f"{nombre_limpio}.docx")
        else:
            return cmd_crear_docx_profesional(titulo=f"Informe: {tema}", tema=tema, filename=f"{nombre_limpio}.docx")

    # --- EXCEL ---
    elif "excel" in instruccion_lower:
        if "formato" in instruccion_lower or "formatear" in instruccion_lower:
            return "Comando de formatear Excel detectado. Falta implementar el flujo completo de selección de archivo."

        tema = "datos_generados"
        match = re.search(r"sobre (.+?)(?:\.|,|$|ll[aá]male)", instruccion_lower)
        if match: tema = match.group(1).strip()
        nombre_limpio = obtener_nombre_seguro(instruccion, tema)

        if es_complejo:
            return cmd_crear_excel_complejo_con_chatgpt(instruccion, f"{nombre_limpio}.xlsx")
        else:
             datos = [["Nombre", "Valor"], ["Dato A", 10], ["Dato B", 20]]
             return cmd_escribir_excel(f"{nombre_limpio}.xlsx", "Hoja1", datos)

    # --- POWERPOINT ---
    elif "ppt" in instruccion_lower or "presentacion" in instruccion_lower or "powerpoint" in instruccion_lower:
        tema = "Tema_general"
        match = re.search(r"sobre (.+?)(?:\.|,|$|ll[aá]male)", instruccion_lower)
        if match: tema = match.group(1).strip()
        nombre_limpio = obtener_nombre_seguro(instruccion, tema)

        if es_complejo:
            return cmd_crear_ppt_compleja_con_chatgpt(instruccion, f"{nombre_limpio}.pptx")
        else:
            return "Comando de actualizar PPT detectado. Falta el diccionario de reemplazos."

    # --- TXT / TEMAS ---
    elif "escribe" in instruccion_lower or "crea un tema" in instruccion_lower:
        tema = "Tema_generico"
        match = re.search(r"sobre (.+?)(?:\.|,|$|ll[aá]male)", instruccion_lower)
        if match: tema = match.group(1).strip()
        nombre_limpio = obtener_nombre_seguro(instruccion, tema)
        return cmd_crear_tema(tema, f"{nombre_limpio}.txt")

    # --- RESUMIR ARCHIVO O WEB ---
    elif "resume el archivo" in instruccion_lower or "resumir el archivo" in instruccion_lower:
        return "Comando de resumir archivo detectado. Falta el nombre del archivo."
    elif "resume la web" in instruccion_lower or "resumir la web" in instruccion_lower or "http" in instruccion_lower:
        match = re.search(r"(https?://\S+)", instruccion_lower)
        if match:
            return cmd_resumir_web(match.group(1))
        return "Comando de resumir web detectado, pero no encontré una URL válida."

    # --- PREGUNTA DIRECTA A CHATGPT ---
    elif "preguntale a chatgpt" in instruccion_lower or "usar ia web" in instruccion_lower:
        prompt = instruccion.replace("preguntale a chatgpt", "").replace("usar ia web", "").strip()
        if not prompt: return "Por favor dime qué quieres preguntarle a ChatGPT."
        return ask_chatgpt_web(prompt)

    # --- FALLBACK: TAREA COMPLEJA GENÉRICA (ASUMIMOS WORD) ---
    elif es_complejo:
        tema = "investigacion_general"
        match = re.search(r"sobre (.+?)(?:\.|,|$|ll[aá]male)", instruccion_lower)
        if match: tema = match.group(1).strip()
        nombre_limpio = obtener_nombre_seguro(instruccion, tema)
        return cmd_crear_word_complejo_con_chatgpt(instruccion, f"{nombre_limpio}.docx")

    else:
        return f"Instrucción no reconocida o no soportada aún por el dispatcher.\nInstrucción recibida: {instruccion}"

# Prueba local
if __name__ == "__main__":
    print(dispatcher_ia("hazme un informe en word sobre stablecoins"))
