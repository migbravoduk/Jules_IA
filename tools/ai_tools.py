from main import (
    cmd_listar, cmd_leer, cmd_crear_tema, cmd_resumir,
    cmd_reescribir, cmd_abrir_web, cmd_resumir_web,
    cmd_crear_docx_profesional, cmd_escribir_excel,
    cmd_formatear_excel, cmd_actualizar_ppt
)
from tools.web_ai_tools import ask_chatgpt_web, ask_gemini_web
from tools.ppt_tools import crear_ppt_compleja_desde_json
from tools.word_tools import crear_word_complejo_desde_json
from tools.excel_tools import crear_excel_complejo_desde_json
from main import ask_ollama # Para usar a Ollama como clasificador de intenciones
import re
import json
import datetime
import string

def clasificar_intencion_con_ollama(instruccion: str) -> str:
    """
    Le pregunta a la IA local (Ollama) qué tipo de documento final quiere el usuario.
    Retorna 'WORD', 'EXCEL', 'PPT', o 'DESCONOCIDO'.
    """
    prompt = (
        f"Analiza la siguiente instrucción del usuario: '{instruccion}'.\n"
        f"El usuario quiere que le generes un archivo. ¿Cuál es el formato FINAL que espera?\n"
        f"Responde ESTRICTAMENTE con una sola palabra de esta lista: WORD, EXCEL, PPT.\n"
        f"Si la instrucción pide 'una tabla de excel pegada en un word', el archivo final es un WORD.\n"
        f"Si pide 'una presentación', es PPT.\n"
        f"Si no es ninguno o es ambiguo, responde DESCONOCIDO.\n"
        f"Respuesta:"
    )
    respuesta = ask_ollama(prompt)
    if not respuesta or "Error" in respuesta:
        return "DESCONOCIDO"

    respuesta_upper = respuesta.upper()
    if "WORD" in respuesta_upper: return "WORD"
    if "EXCEL" in respuesta_upper: return "EXCEL"
    if "PPT" in respuesta_upper: return "PPT"

    return "DESCONOCIDO"

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

def enviar_a_ia_externa(prompt: str, motor: str) -> str:
    """Envía el prompt a ChatGPT o Gemini según el motor seleccionado."""
    if motor == "gemini":
        return ask_gemini_web(prompt)
    return ask_chatgpt_web(prompt)

def cmd_crear_ppt_compleja_con_chatgpt(instruccion: str, filename: str, motor: str = "chatgpt") -> str:
    """Orquesta la creación de una PPT compleja usando IA Externa."""
    prompt = (
        f"Actúa como un investigador y diseñador experto de nivel 'NotebookLM'. "
        f"Tu objetivo es crear una presentación exhaustiva y sofisticada basada en esta instrucción: '{instruccion}'.\n"
        f"La presentación debe ser larga, detallada y estructurada para una audiencia ejecutiva o académica.\n"
        f"Usa datos profundos. El JSON debe ser un array de objetos.\n"
        f"El primer objeto debe ser tipo portada. Luego incluye un tipo 'indice', y los demás tipo 'contenido' o 'cita'.\n"
        f"Genera la respuesta estrictamente en formato JSON, sin texto fuera del JSON.\n"
        f"Formato esperado:\n"
        f"[\n"
        f"  {{\"tipo\": \"portada\", \"titulo\": \"...\", \"subtitulo\": \"...\"}},\n"
        f"  {{\"tipo\": \"indice\", \"titulo\": \"Índice de Contenidos\", \"viñetas\": [\"1. Tema\", \"2. Tema\"]}},\n"
        f"  {{\"tipo\": \"cita\", \"texto\": \"Una frase inspiradora o cita clave relacionada al tema\"}},\n"
        f"  {{\"tipo\": \"contenido\", \"titulo\": \"...\", \"viñetas\": [\"Dato analítico 1\", \"Dato analítico 2\"]}}\n"
        f"]"
    )

    respuesta = enviar_a_ia_externa(prompt, motor)
    if respuesta.startswith("❌"):
        return respuesta

    texto_json = limpiar_json_de_chatgpt(respuesta)
    return crear_ppt_compleja_desde_json(filename, texto_json)

def cmd_crear_word_complejo_con_chatgpt(instruccion: str, filename: str, motor: str = "chatgpt") -> str:
    """Orquesta la creación de un Word complejo usando IA Externa."""
    prompt = (
        f"Actúa como un investigador experto creando un documento de estudio avanzado tipo 'NotebookLM'.\n"
        f"El usuario pide lo siguiente: '{instruccion}'.\n"
        f"Genera un informe MUY EXTENSO, profundo y analítico. Debe incluir:\n"
        f"- Título Principal (tipo 'titulo')\n"
        f"- Múltiples Subtítulos para dividir el análisis (tipo 'subtitulo')\n"
        f"- Citas clave o 'takeaways' (tipo 'cita')\n"
        f"- Explicaciones detalladas en párrafos profundos (tipo 'parrafo')\n"
        f"- Listas de puntos clave estructurados (tipo 'lista')\n"
        f"- Si se requieren datos comparativos, usa tipo 'tabla'.\n"
        f"Genera esto estrictamente en formato JSON puro. Ejemplo de esquema:\n"
        f"[\n"
        f"  {{\"tipo\": \"titulo\", \"texto\": \"Título\"}},\n"
        f"  {{\"tipo\": \"cita\", \"texto\": \"Frase destacada o Insight clave\"}},\n"
        f"  {{\"tipo\": \"subtitulo\", \"texto\": \"Sección 1: Contexto\"}},\n"
        f"  {{\"tipo\": \"parrafo\", \"texto\": \"Análisis extenso...\"}},\n"
        f"  {{\"tipo\": \"lista\", \"items\": [\"Punto detallado 1\", \"Punto detallado 2\"]}},\n"
        f"  {{\"tipo\": \"tabla\", \"filas\": [[\"A\", \"B\"], [\"1\", \"2\"]]}}\n"
        f"]"
    )
    respuesta = enviar_a_ia_externa(prompt, motor)
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

def cmd_revisar_mejorar_archivo_con_chatgpt(instruccion: str, filename_origen: str) -> str:
    """
    Lee un archivo desde 'inputs' o 'outputs', envía su contenido a ChatGPT junto
    con la instrucción del usuario, y crea un nuevo archivo de Word con la mejora o análisis.
    """
    import os
    from main import cmd_leer

    # Intentar leer desde 'inputs' primero
    contenido = cmd_leer(filename_origen, context="inputs")
    if contenido.startswith("Error leyendo"):
        # Intentar desde 'outputs'
        contenido = cmd_leer(filename_origen, context="outputs")
        if contenido.startswith("Error leyendo"):
             return f"No se encontró el archivo '{filename_origen}' ni en inputs ni en outputs para mejorarlo."

    # Preparamos el prompt para pedir un Word estructurado
    prompt = (
        f"Actúa como un revisor experto. El usuario te pide lo siguiente: '{instruccion}'.\n"
        f"Aplica esto al siguiente texto original:\n\n---\n{contenido}\n---\n\n"
        f"Genera la respuesta estrictamente en formato JSON para crear un documento Word, "
        f"sin explicaciones adicionales, sin bloques de código Markdown, SOLO EL JSON PURO. "
        f"Formato esperado:\n"
        f"[\n"
        f"  {{\"tipo\": \"titulo\", \"texto\": \"Análisis o Mejora\"}},\n"
        f"  {{\"tipo\": \"parrafo\", \"texto\": \"Contenido...\"}}\n"
        f"]"
    )

    respuesta = ask_chatgpt_web(prompt)
    if respuesta.startswith("❌"):
        return respuesta

    texto_json = limpiar_json_de_chatgpt(respuesta)

    # Guardamos en un nuevo archivo Word indicando que es una revisión
    nuevo_nombre = f"revision_{os.path.splitext(filename_origen)[0]}.docx"
    return crear_word_complejo_desde_json(nuevo_nombre, texto_json)

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
        "complejo", "chatgpt", "gemini", "extenso", "investiga", "noticias", "detallado", "creame un"
    ])

    motor_ia = "gemini" if "gemini" in instruccion_lower else "chatgpt"

    # 1. Usar Ollama para clasificar la intención principal (¿Word, Excel o PPT?)
    # Esto evita confusión semántica ("tabla de excel pegada en un word" -> WORD)
    tipo_documento = clasificar_intencion_con_ollama(instruccion)

    # Fallback semántico si Ollama falla o responde DESCONOCIDO
    if tipo_documento == "DESCONOCIDO":
        if "word" in instruccion_lower or "informe" in instruccion_lower: tipo_documento = "WORD"
        elif "excel" in instruccion_lower: tipo_documento = "EXCEL"
        elif "ppt" in instruccion_lower or "presentacion" in instruccion_lower or "powerpoint" in instruccion_lower: tipo_documento = "PPT"

    # --- WORD ---
    if tipo_documento == "WORD":
        tema = "Tema_general"
        match = re.search(r"sobre (.+?)(?:\.|,|$|ll[aá]male)", instruccion_lower)
        if match: tema = match.group(1).strip()
        nombre_limpio = obtener_nombre_seguro(instruccion, tema)

        if es_complejo:
            return cmd_crear_word_complejo_con_chatgpt(instruccion, f"{nombre_limpio}.docx", motor=motor_ia)
        else:
            return cmd_crear_docx_profesional(titulo=f"Informe: {tema}", tema=tema, filename=f"{nombre_limpio}.docx")

    # --- EXCEL ---
    elif tipo_documento == "EXCEL":
        if "formato" in instruccion_lower or "formatear" in instruccion_lower:
            return "Comando de formatear Excel detectado. Falta implementar el flujo completo de selección de archivo."

        tema = "datos_generados"
        match = re.search(r"sobre (.+?)(?:\.|,|$|ll[aá]male)", instruccion_lower)
        if match: tema = match.group(1).strip()
        nombre_limpio = obtener_nombre_seguro(instruccion, tema)

        if es_complejo:
            return cmd_crear_excel_complejo_con_chatgpt(instruccion, f"{nombre_limpio}.xlsx") # Solo soportado en ChatGPT por ahora
        else:
             datos = [["Nombre", "Valor"], ["Dato A", 10], ["Dato B", 20]]
             return cmd_escribir_excel(f"{nombre_limpio}.xlsx", "Hoja1", datos)

    # --- POWERPOINT ---
    elif tipo_documento == "PPT":
        tema = "Tema_general"
        match = re.search(r"sobre (.+?)(?:\.|,|$|ll[aá]male)", instruccion_lower)
        if match: tema = match.group(1).strip()
        nombre_limpio = obtener_nombre_seguro(instruccion, tema)

        if es_complejo:
            return cmd_crear_ppt_compleja_con_chatgpt(instruccion, f"{nombre_limpio}.pptx", motor=motor_ia)
        else:
            return "Comando de actualizar PPT detectado. Falta el diccionario de reemplazos."

    # --- TXT / TEMAS ---
    elif "escribe" in instruccion_lower or "crea un tema" in instruccion_lower:
        tema = "Tema_generico"
        match = re.search(r"sobre (.+?)(?:\.|,|$|ll[aá]male)", instruccion_lower)
        if match: tema = match.group(1).strip()
        nombre_limpio = obtener_nombre_seguro(instruccion, tema)
        return cmd_crear_tema(tema, f"{nombre_limpio}.txt")

    # --- REVISAR / MEJORAR / RESUMIR ARCHIVO CON CHATGPT ---
    elif any(kw in instruccion_lower for kw in ["revisa el archivo", "mejora el archivo", "lee el archivo", "analiza el archivo", "resume el archivo", "resumir el archivo"]):
        # Extraer posible nombre de archivo de la instrucción (ej. "lee el archivo reporte.txt y resúmelo")
        match_archivo = re.search(r'archivo\s+([a-zA-Z0-9_.\-]+)', instruccion_lower)
        if match_archivo:
             nombre_archivo = match_archivo.group(1)
             return cmd_revisar_mejorar_archivo_con_chatgpt(instruccion, nombre_archivo)
        else:
             return "Para revisar o mejorar un archivo debes indicar su nombre con su extensión (ej. 'revisa el archivo datos.txt'). Asegúrate de que esté en la carpeta 'inputs' o 'outputs'."

    # --- RESUMIR WEB ---
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
