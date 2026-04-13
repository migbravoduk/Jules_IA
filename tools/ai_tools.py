from main import (
    cmd_listar, cmd_leer, cmd_crear_tema, cmd_resumir,
    cmd_reescribir, cmd_abrir_web, cmd_resumir_web,
    cmd_crear_docx_profesional, cmd_escribir_excel,
    cmd_formatear_excel, cmd_actualizar_ppt
)
from tools.web_ai_tools import ask_chatgpt_web, ask_gemini_web
from tools.ppt_tools import crear_ppt_compleja_desde_json
from tools.word_tools import crear_word_complejo_desde_json, extraer_texto_word
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

def cmd_crear_ppt_compleja_con_chatgpt(instruccion: str, filename: str, motor: str = "gemini") -> str:
    """Orquesta la creación de una PPT compleja usando IA Externa."""
    prompt = (
        f"Actúa como un diseñador de presentaciones ejecutivas experto.\n"
        f"Instrucción del usuario: '{instruccion}'.\n"
        f"REGLAS OBLIGATORIAS:\n"
        f"  - Genera entre 7 y 10 slides de contenido como mínimo.\n"
        f"  - Cada viñeta: MÁXIMO 12 palabras. Concisa, impactante, basada en datos.\n"
        f"  - Máximo 5 viñetas por slide de contenido.\n"
        f"  - Incluye UN slide de cita inspiradora.\n"
        f"  - Incluye slides de tipo 'tabla_slide' cuando haya datos numéricos o comparaciones.\n"
        f"  - Al FINAL incluye un objeto tipo 'referencias' con al menos 5 fuentes APA reales.\n"
        f"CRÍTICO: Responde ÚNICAMENTE con el array JSON válido. Sin texto introductorio, sin explicaciones, sin bloques de código markdown.\n"
        f"Formato del array JSON:\n"
        f"[\n"
        f"  {{\"tipo\": \"portada\", \"titulo\": \"...\", \"subtitulo\": \"...\"}},\n"
        f"  {{\"tipo\": \"indice\", \"titulo\": \"Índice\", \"viñetas\": [\"1. Tema\", \"2. Tema\"]}},\n"
        f"  {{\"tipo\": \"cita\", \"texto\": \"Frase clave corta e impactante\"}},\n"
        f"  {{\"tipo\": \"contenido\", \"titulo\": \"...\", \"viñetas\": [\"Dato clave 1\", \"Dato clave 2\"]}},\n"
        f"  {{\"tipo\": \"tabla_slide\", \"titulo\": \"Tabla Comparativa\", \"headers\": [\"Columna A\", \"Columna B\"], \"filas\": [[\"Val 1\", \"Val 2\"]]}},\n"
        f"  {{\"tipo\": \"referencias\", \"items\": [\"Autor, A. (Año). Título. Fuente.\"]}}\n"
        f"]"
    )

    respuesta = enviar_a_ia_externa(prompt, motor)
    if respuesta.startswith("❌"):
        return respuesta

    texto_json = limpiar_json_de_chatgpt(respuesta)
    return crear_ppt_compleja_desde_json(filename, texto_json)

def cmd_crear_word_complejo_con_chatgpt(instruccion: str, filename: str, motor: str = "gemini") -> str:
    """Orquesta la creación de un Word complejo usando IA Externa."""
    prompt = (
        f"Actúa como un investigador académico experto generando un informe formal en formato APA.\n"
        f"El usuario pide: '{instruccion}'.\n"
        f"Genera un informe EXTENSO y analítico con al menos 4 secciones. REGLAS:\n"
        f"  - Párrafos profundos, mínimo 4 oraciones cada uno.\n"
        f"  - Incluye tablas comparativas (tipo 'tabla') cuando haya datos numéricos o comparaciones.\n"
        f"  - Incluye al menos 1 cita destacada (tipo 'cita') por sección.\n"
        f"  - AL FINAL incluye un bloque 'referencias' con mínimo 5 fuentes en formato APA real.\n"
        f"CRÍTICO: Responde ÚNICAMENTE con el array JSON válido. Sin texto introductorio, sin explicaciones, sin bloques de código markdown (no uses ```json).\n"
        f"Esquema JSON:\n"
        f"[\n"
        f"  {{\"tipo\": \"titulo\", \"texto\": \"Título del Informe\"}},\n"
        f"  {{\"tipo\": \"cita\", \"texto\": \"Insight clave introductorio\"}},\n"
        f"  {{\"tipo\": \"subtitulo\", \"texto\": \"1. Nombre de Sección\"}},\n"
        f"  {{\"tipo\": \"parrafo\", \"texto\": \"Análisis extenso de al menos 4 oraciones...\"}},\n"
        f"  {{\"tipo\": \"lista\", \"items\": [\"Punto clave 1\", \"Punto clave 2\"]}},\n"
        f"  {{\"tipo\": \"tabla\", \"titulo\": \"Tabla 1: Nombre\", \"filas\": [[\"Col A\", \"Col B\"], [\"Val 1\", \"Val 2\"]]}},\n"
        f"  {{\"tipo\": \"referencias\", \"items\": [\"Autor, A. (Año). Título. Revista, vol(n), pp. https://doi.org/...\"]}}\n"
        f"]"
    )
    respuesta = enviar_a_ia_externa(prompt, motor)
    if respuesta.startswith("❌"):
        return respuesta
    texto_json = limpiar_json_de_chatgpt(respuesta)
    return crear_word_complejo_desde_json(filename, texto_json)

def cmd_crear_excel_complejo_con_chatgpt(instruccion: str, filename: str, motor: str = "gemini") -> str:
    """Orquesta la creación de un Excel complejo usando IA Externa (Gemini por defecto)."""
    prompt = (
        f"Actúa como un analista de datos experto.\n"
        f"El usuario pide generar un Excel con: '{instruccion}'.\n"
        f"Genera múltiples hojas con datos reales y representativos.\n"
        f"CRÍTICO: Responde ÚNICAMENTE con el array JSON válido, sin texto antes ni después, sin bloques de código markdown (no uses ```json).\n"
        f"Formato esperado (array de hojas):\n"
        f"[\n"
        f"  {{\"hoja\": \"Nombre Hoja 1\", \"datos\": [\n"
        f"      [\"Columna A\", \"Columna B\", \"Columna C\"],\n"
        f"      [\"Valor 1\", 15000, 5000],\n"
        f"      [\"Valor 2\", 18000, 6500]\n"
        f"  ]}}\n"
        f"]"
    )
    respuesta = enviar_a_ia_externa(prompt, motor)
    if respuesta.startswith("❌"):
        return respuesta
    texto_json = limpiar_json_de_chatgpt(respuesta)
    return crear_excel_complejo_desde_json(filename, texto_json)

def cmd_crear_excel_deep_research(instruccion: str, filename: str, motor: str = "gemini") -> str:
    """
    Modo Deep Research para Excel: planifica las hojas necesarias primero,
    luego genera los datos de cada hoja en iteraciones separadas.
    Produce un Excel mult-hoja con datos ricos y reales.
    """
    print("🧠 [Deep Research Excel] Planificando hojas del Excel...")

    # Paso 1: Pedir a la IA un índice con las hojas que debe tener el Excel
    prompt_indice = (
        f"Actúa como un analista de datos experto planificando un Excel sobre: '{instruccion}'.\n"
        f"Diseña entre 3 y 6 hojas de datos necesarias para cubrir el tema a fondo.\n"
        f"Para cada hoja, define su nombre y las columnas que debe tener.\n"
        f"CRÍTICO: Responde ÚNICAMENTE con el array JSON. Sin texto antes ni después, sin markdown.\n"
        f"Formato estricto:\n"
        f"[\n"
        f"  {{\"hoja\": \"Resumen General\", \"columnas\": [\"Indicador\", \"Valor\", \"Variación\", \"Fuente\"]}},\n"
        f"  {{\"hoja\": \"Serie Histórica\", \"columnas\": [\"Año\", \"Dato A\", \"Dato B\"]}}\n"
        f"]"
    )

    resp_indice = enviar_a_ia_externa(prompt_indice, motor)
    if resp_indice.startswith("❌"): return resp_indice

    try:
        indice_hojas = json.loads(limpiar_json_de_chatgpt(resp_indice))
    except Exception as e:
        return f"Error en Deep Research Excel (No se pudo parsear índice): {e}\nRespuesta IA: {resp_indice[:300]}"

    if not indice_hojas:
        return "Error: El índice de hojas devuelto está vacío."

    print(f"📊 [Deep Research Excel] Se generarán {len(indice_hojas)} hojas. Empezando...")
    excel_final_json = []

    # Paso 2: Generar los datos de cada hoja en iteraciones separadas
    for item in indice_hojas:
        nombre_hoja = item.get("hoja", "Hoja")
        columnas = item.get("columnas", [])
        columnas_str = ", ".join(f'"{c}"' for c in columnas)
        print(f"✍️ [Deep Research Excel] Generando datos para hoja: '{nombre_hoja}'...")

        prompt_hoja = (
            f"Actúa como un analista de datos experto. Genera los datos para la hoja '{nombre_hoja}' "
            f"de un Excel sobre: '{instruccion}'.\n"
            f"Las columnas son: [{columnas_str}].\n"
            f"REGLAS:\n"
            f"  - Genera mínimo 10 filas de datos reales y representativos.\n"
            f"  - Los datos numéricos deben ser cohérentes y basados en información real.\n"
            f"  - La primera fila del array 'datos' debe ser la fila de encabezados.\n"
            f"CRÍTICO: Responde ÚNICAMENTE con este objeto JSON (sin array exterior, sin texto extra, sin markdown):\n"
            f"{{\"hoja\": \"{nombre_hoja}\", \"datos\": ["
            f"[{columnas_str}], "
            f"[\"Valor A\", \"Valor B\"]]}}"
        )

        resp_hoja = enviar_a_ia_externa(prompt_hoja, motor)
        if resp_hoja.startswith("❌"):
            print(f"⚠️ Error generando hoja '{nombre_hoja}', saltando...")
            continue

        try:
            hoja_data = json.loads(limpiar_json_de_chatgpt(resp_hoja))
            if isinstance(hoja_data, dict) and "hoja" in hoja_data and "datos" in hoja_data:
                excel_final_json.append(hoja_data)
            elif isinstance(hoja_data, list):
                # A veces la IA devuelve un array directamente
                excel_final_json.extend(hoja_data)
        except Exception as e:
            print(f"⚠️ Error parseando hoja '{nombre_hoja}': {e}")

    if not excel_final_json:
        return "Error: No se pudo generar ningún dato para el Excel."

    print(f"🏗️ [Deep Research Excel] Ensamblando Excel con {len(excel_final_json)} hojas...")
    return crear_excel_complejo_desde_json(filename, json.dumps(excel_final_json))

def cmd_crear_word_deep_research(instruccion: str, filename: str, motor: str = "gemini") -> str:
    """Modo Deep Research para Word: Divide la tarea en Índice y luego itera por cada sección."""
    print("🧠 [Deep Research] Generando índice / outline...")
    prompt_indice = (
        f"Actúa como un investigador experto planificando un estudio detallado sobre: '{instruccion}'.\n"
        f"Genera entre 5 y 7 secciones principales para analizar este tema a fondo.\n"
        f"CRÍTICO: Responde ÚNICAMENTE con el array JSON. Sin texto antes ni después, sin markdown.\n"
        f"Formato estricto:\n"
        f"[\n"
        f"  {{\"seccion\": \"1. Historia y Contexto\"}},\n"
        f"  {{\"seccion\": \"2. Análisis Técnico\"}}\n"
        f"]"
    )
    resp_indice = enviar_a_ia_externa(prompt_indice, motor)
    if resp_indice.startswith("❌"): return resp_indice

    try:
        texto_json_indice = limpiar_json_de_chatgpt(resp_indice)
        indice = json.loads(texto_json_indice)
    except Exception as e:
        return f"Error en Deep Research (No se pudo parsear el índice): {e}\nRespuesta IA: {resp_indice}"

    if not indice: return "Error: El índice devuelto está vacío."

    print(f"📚 [Deep Research] Índice detectado con {len(indice)} secciones. Empezando redacción profunda...")
    documento_final_json = []

    # Agregar Título Principal al documento
    match_tema = re.search(r"sobre (.+?)(?:\.|,|$)", instruccion.lower())
    tema_detectado = match_tema.group(1).title() if match_tema else "Reporte de Análisis"
    documento_final_json.append({"tipo": "titulo", "texto": f"Deep Research: {tema_detectado}"})

    referencias_globales = []  # Se acumulan de todas las secciones

    for item in indice:
        tema_seccion = item.get("seccion", "Tema Desconocido")
        print(f"✍️ [Deep Research] Investigando y redactando: {tema_seccion}...")

        prompt_seccion = (
            f"Actúa como un investigador académico redactando la sección '{tema_seccion}' "
            f"de un informe APA sobre: '{instruccion}'.\n"
            f"REGLAS:\n"
            f"  - Escribe mínimo 3 párrafos profundos (tipo 'parrafo'), cada uno con al menos 4 oraciones.\n"
            f"  - Si hay datos numéricos o comparaciones, incluye una tabla (tipo 'tabla') con datos reales.\n"
            f"  - Incluye una cita destacada (tipo 'cita') con un insight o dato clave.\n"
            f"  - Incluye una lista de puntos clave (tipo 'lista') al final de la sección.\n"
            f"  - Incluye 2-3 referencias APA reales en tipo 'referencias'.\n"
            f"CRÍTICO: Responde ÚNICAMENTE con el array JSON válido. Sin texto antes ni después, sin bloques markdown.\n"
            f"Esquema:\n"
            f"[\n"
            f"  {{\"tipo\": \"subtitulo\", \"texto\": \"{tema_seccion}\"}},\n"
            f"  {{\"tipo\": \"cita\", \"texto\": \"Dato o insight clave de la sección\"}},\n"
            f"  {{\"tipo\": \"parrafo\", \"texto\": \"Análisis profundo con al menos 4 oraciones...\"}},\n"
            f"  {{\"tipo\": \"tabla\", \"titulo\": \"Tabla: Nombre descriptivo\", \"filas\": [[\"Encabezado A\", \"Encabezado B\"], [\"Dato 1\", \"Dato 2\"]]}},\n"
            f"  {{\"tipo\": \"lista\", \"items\": [\"Punto clave 1\", \"Punto clave 2\", \"Punto clave 3\"]}},\n"
            f"  {{\"tipo\": \"referencias\", \"items\": [\"Autor, A. (Año). Título. Revista, vol(n), pp.\"]}}\n"
            f"]"
        )

        resp_seccion = enviar_a_ia_externa(prompt_seccion, motor)
        if resp_seccion.startswith("❌"):
            print(f"⚠️ Error generando sección '{tema_seccion}', saltando...")
            continue

        try:
            texto_json_seccion = limpiar_json_de_chatgpt(resp_seccion)
            contenido_seccion = json.loads(texto_json_seccion)
            if isinstance(contenido_seccion, list):
                # Separar referencias para consolidarlas al final
                for bloque in contenido_seccion:
                    if bloque.get("tipo") == "referencias":
                        referencias_globales.extend(bloque.get("items", []))
                    else:
                        documento_final_json.append(bloque)
            else:
                documento_final_json.append(contenido_seccion)
        except Exception as e:
            print(f"⚠️ Error parseando sección '{tema_seccion}': {e}")

    # Añadir sección de Referencias consolidada al final
    if referencias_globales:
        # Eliminar duplicados manteniendo orden
        seen = set()
        refs_unicas = [r for r in referencias_globales if not (r in seen or seen.add(r))]
        documento_final_json.append({"tipo": "referencias", "items": refs_unicas})

    print(f"🏗️ [Deep Research] Ensamblando documento Word con {len(documento_final_json)} bloques de contenido...")
    return crear_word_complejo_desde_json(filename, json.dumps(documento_final_json))

def cmd_crear_ppt_deep_research(instruccion: str, filename: str, motor: str = "gemini") -> str:
    """Modo Deep Research para PPT: Extrae slide-titles primero y luego rellena el contenido."""
    print("🧠 [Deep Research] Generando estructura de la presentación...")
    prompt_indice = (
        f"Actúa como un diseñador de presentaciones estratégico. Plantea la estructura para un PowerPoint ejecutivo sobre: '{instruccion}'.\n"
        f"Genera entre 7 y 9 slides (incluyendo portada). Incluye al menos 2 slides de datos/tabla.\n"
        f"CRÍTICO: Responde ÚNICAMENTE con el array JSON. Sin texto antes ni después, sin markdown.\n"
        f"Formato estricto:\n"
        f"[\n"
        f"  {{\"slide\": \"Portada Principal\", \"tipo_sugerido\": \"portada\"}},\n"
        f"  {{\"slide\": \"Contexto Histórico\", \"tipo_sugerido\": \"contenido\"}},\n"
        f"  {{\"slide\": \"Datos Clave en Cifras\", \"tipo_sugerido\": \"tabla_slide\"}}\n"
        f"]"
    )
    resp_indice = enviar_a_ia_externa(prompt_indice, motor)
    if resp_indice.startswith("❌"): return resp_indice

    try:
        texto_json_indice = limpiar_json_de_chatgpt(resp_indice)
        indice = json.loads(texto_json_indice)
    except Exception as e:
         return f"Error en Deep Research PPT (No se pudo parsear índice): {e}\nRespuesta IA: {resp_indice[:400]}"

    ppt_final_json = []

    for i, item in enumerate(indice):
        titulo_slide = item.get("slide", f"Slide {i+1}")
        tipo_sugerido = item.get("tipo_sugerido", "contenido")
        print(f"✍️ [Deep Research] Generando contenido para slide: {titulo_slide} (tipo: {tipo_sugerido})...")

        # El primero lo forzamos a portada
        if i == 0:
            prompt_slide = (
                f"Genera la portada para una presentación ejecutiva sobre '{instruccion}'.\n"
                f"CRÍTICO: Responde ÚNICAMENTE con este objeto JSON (sin array, sin texto extra, sin markdown):\n"
                f"{{\"tipo\": \"portada\", \"titulo\": \"{titulo_slide}\", \"subtitulo\": \"Análisis Estratégico y Detallado\"}}"
            )
        elif tipo_sugerido == "tabla_slide":
            prompt_slide = (
                f"Genera un slide de tabla de datos para '{titulo_slide}' en una presentación sobre '{instruccion}'.\n"
                f"La tabla debe tener datos reales, mínimo 4 filas de datos (sin contar encabezados).\n"
                f"CRÍTICO: Responde ÚNICAMENTE con este objeto JSON (sin array, sin texto extra, sin markdown):\n"
                f"{{\"tipo\": \"tabla_slide\", \"titulo\": \"{titulo_slide}\", "
                f"\"headers\": [\"Columna A\", \"Columna B\", \"Columna C\"], "
                f"\"filas\": [[\"Dato 1A\", \"Dato 1B\", \"Dato 1C\"], [\"Dato 2A\", \"Dato 2B\", \"Dato 2C\"]]}}"
            )
        else:
            prompt_slide = (
                f"Actúa como analista experto. Genera el contenido para el slide '{titulo_slide}' "
                f"de una presentación ejecutiva sobre '{instruccion}'.\n"
                f"REGLAS OBLIGATORIAS:\n"
                f"  - Máximo 5 viñetas.\n"
                f"  - Cada viñeta: MÁXIMO 12 palabras. Datos concretos, sin relleno.\n"
                f"  - Si es un slide de cita/frase impactante, usa tipo 'cita'.\n"
                f"CRÍTICO: Responde ÚNICAMENTE con este objeto JSON (sin array, sin texto extra, sin markdown):\n"
                f"{{\"tipo\": \"contenido\", \"titulo\": \"{titulo_slide}\", "
                f"\"viñetas\": [\"Dato clave 1\", \"Dato clave 2\", \"Dato clave 3\"]}}"
            )

        resp_slide = enviar_a_ia_externa(prompt_slide, motor)
        if resp_slide.startswith("❌"): continue

        try:
            texto_json_slide = limpiar_json_de_chatgpt(resp_slide)
            contenido_slide = json.loads(texto_json_slide)
            if isinstance(contenido_slide, list) and len(contenido_slide) > 0:
                ppt_final_json.append(contenido_slide[0])
            elif isinstance(contenido_slide, dict):
                ppt_final_json.append(contenido_slide)
        except Exception as e:
            print(f"⚠️ Error parseando slide '{titulo_slide}': {e}")

    # Pedir referencias al final en una sola llamada
    print("📚 [Deep Research PPT] Generando slide(s) de Referencias...")
    prompt_refs = (
        f"Genera una lista de al menos 6 referencias bibliográficas reales en formato APA "
        f"sobre el tema: '{instruccion}'.\n"
        f"CRÍTICO: Responde ÚNICAMENTE con este objeto JSON (sin array exterior, sin texto extra, sin markdown):\n"
        f"{{\"tipo\": \"referencias\", \"items\": ["
        f"\"Autor, A. (Año). Título. Revista, vol(n), pp. https://doi.org/...\"]}}"
    )
    resp_refs = enviar_a_ia_externa(prompt_refs, motor)
    if not resp_refs.startswith("❌"):
        try:
            refs_json = json.loads(limpiar_json_de_chatgpt(resp_refs))
            if isinstance(refs_json, dict):
                ppt_final_json.append(refs_json)
        except Exception:
            pass

    print(f"🏗️ [Deep Research] Ensamblando presentación de {len(ppt_final_json)} slides...")
    return crear_ppt_compleja_desde_json(filename, json.dumps(ppt_final_json))

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
        f"CRÍTICO: Responde ÚNICAMENTE con el array JSON válido para crear un documento Word. Sin texto antes ni después, sin bloques markdown.\n"
        f"Formato esperado:\n"
        f"[\n"
        f"  {{\"tipo\": \"titulo\", \"texto\": \"Análisis o Mejora\"}},\n"
        f"  {{\"tipo\": \"cita\", \"texto\": \"Insight clave del contenido\"}},\n"
        f"  {{\"tipo\": \"subtitulo\", \"texto\": \"Sección\"}},\n"
        f"  {{\"tipo\": \"parrafo\", \"texto\": \"Contenido...\"}},\n"
        f"  {{\"tipo\": \"referencias\", \"items\": [\"Fuente APA real\"]}}\n"
        f"]"
    )

    respuesta = enviar_a_ia_externa(prompt, "gemini")
    if respuesta.startswith("❌"):
        return respuesta

    texto_json = limpiar_json_de_chatgpt(respuesta)

    # Guardamos en un nuevo archivo Word indicando que es una revión
    nuevo_nombre = f"revision_{os.path.splitext(filename_origen)[0]}.docx"
    return crear_word_complejo_desde_json(nuevo_nombre, texto_json)

def cmd_profundizar_word_con_gemini(filename: str, instruccion_adicional: str = "", motor: str = "gemini") -> str:
    """
    Lee el contenido de un .docx (desde inputs/ o outputs/), lo envía a Gemini
    en modo Deep Research y genera un nuevo documento Word ampliado y mejorado.

    El proceso es iterativo (igual que Deep Research):
      1. Extrae el texto original del Word.
      2. Pide a Gemini un índice de mejoras/secciones a profundizar.
      3. Genera cada sección mejorada en llamadas separadas.
      4. Ensambla el documento Word final enriquecido.
    """
    print(f"📤 [Profundizar Word] Extrayendo contenido de '{filename}'...")
    contenido_original = extraer_texto_word(filename)
    if contenido_original.startswith("Error"):
        return contenido_original

    # Limitar el contenido a 8000 chars para no saturar el prompt del índice
    contenido_truncado = contenido_original[:8000]
    instruccion_extra = f" Además, el usuario pide: {instruccion_adicional}." if instruccion_adicional else ""

    # Paso 1: Generar índice de secciones a profundizar
    print("🧠 [Profundizar Word] Planificando secciones mejoradas...")
    prompt_indice = (
        f"Analiza el siguiente documento Word y genera un plan de mejora académica.{instruccion_extra}\n"
        f"\n--- CONTENIDO ORIGINAL ---\n{contenido_truncado}\n--- FIN ---\n\n"
        f"Identifica entre 4 y 7 secciones que deben profundizarse, ampliarse o mejorarse.\n"
        f"CRÍTICO: Responde ÚNICAMENTE con el array JSON. Sin texto antes ni después, sin markdown.\n"
        f"Formato:\n"
        f"[\n"
        f"  {{\"seccion\": \"1. Título o tema de la sección a profundizar\"}},\n"
        f"  {{\"seccion\": \"2. Otro tema\"}}\n"
        f"]"
    )
    resp_indice = enviar_a_ia_externa(prompt_indice, motor)
    if resp_indice.startswith("❌"): return resp_indice

    try:
        indice = json.loads(limpiar_json_de_chatgpt(resp_indice))
    except Exception as e:
        return f"Error al planificar mejoras: {e}\nRespuesta: {resp_indice[:300]}"

    if not indice:
        return "Error: El índice de mejoras está vacío."

    print(f"📚 [Profundizar Word] Se mejorarán {len(indice)} secciones. Generando...")

    documento_final_json = []
    match_titulo = re.search(r'^#\s+(.+)', contenido_original[:500], re.MULTILINE)
    titulo_doc = match_titulo.group(1).strip() if match_titulo else os.path.splitext(filename)[0].replace("_", " ")
    documento_final_json.append({"tipo": "titulo", "texto": f"{titulo_doc} (Versión Mejorada)"})
    documento_final_json.append({"tipo": "cita", "texto": "Documento ampliado y profundizado por Gemini AI"})

    referencias_globales = []

    # Paso 2: Generar cada sección por separado
    for item in indice:
        seccion = item.get("seccion", "Sección")
        print(f"✍️ [Profundizar Word] Ampliando sección: {seccion}...")

        prompt_seccion = (
            f"Estás mejorando y profundizando el siguiente documento: '{titulo_doc}'.{instruccion_extra}\n"
            f"\n--- CONTEXTO DEL DOCUMENTO ORIGINAL ---\n{contenido_truncado[:3000]}\n--- FIN ---\n\n"
            f"Redacta la sección '{seccion}' de forma profunda y académica (estilo APA).\n"
            f"REGLAS:\n"
            f"  - Mínimo 3 párrafos profundos de al menos 4 oraciones cada uno.\n"
            f"  - Si hay datos numéricos o comparaciones, incluye una tabla (tipo 'tabla').\n"
            f"  - Incluye una cita destacada (tipo 'cita') con un insight clave.\n"
            f"  - Incluye 2-3 referencias APA reales en tipo 'referencias'.\n"
            f"CRÍTICO: Responde ÚNICAMENTE con el array JSON. Sin texto antes ni después, sin markdown.\n"
            f"Esquema:\n"
            f"[\n"
            f"  {{\"tipo\": \"subtitulo\", \"texto\": \"{seccion}\"}},\n"
            f"  {{\"tipo\": \"cita\", \"texto\": \"Insight clave\"}},\n"
            f"  {{\"tipo\": \"parrafo\", \"texto\": \"Análisis profundo...\"}},\n"
            f"  {{\"tipo\": \"tabla\", \"titulo\": \"Tabla: Nombre\", \"filas\": [[\"Col\", \"Val\"], [\"A\", \"1\"]]}},\n"
            f"  {{\"tipo\": \"lista\", \"items\": [\"Punto 1\", \"Punto 2\"]}},\n"
            f"  {{\"tipo\": \"referencias\", \"items\": [\"Autor, A. (Año). Título. Revista.\"]}}\n"
            f"]"
        )

        resp_seccion = enviar_a_ia_externa(prompt_seccion, motor)
        if resp_seccion.startswith("❌"):
            print(f"⚠️ Error en sección '{seccion}', saltando...")
            continue

        try:
            bloques = json.loads(limpiar_json_de_chatgpt(resp_seccion))
            if isinstance(bloques, list):
                for b in bloques:
                    if b.get("tipo") == "referencias":
                        referencias_globales.extend(b.get("items", []))
                    else:
                        documento_final_json.append(b)
        except Exception as e:
            print(f"⚠️ Error parseando sección '{seccion}': {e}")

    # Agregar referencias consolidadas
    if referencias_globales:
        seen = set()
        refs_unicas = [r for r in referencias_globales if not (r in seen or seen.add(r))]
        documento_final_json.append({"tipo": "referencias", "items": refs_unicas})

    # Nombre del archivo de salida
    nombre_salida = f"mejorado_{os.path.splitext(filename)[0]}.docx"
    print(f"🏗️ [Profundizar Word] Ensamblando documento mejorado ({len(documento_final_json)} bloques)...")
    return crear_word_complejo_desde_json(nombre_salida, json.dumps(documento_final_json))

def dispatcher_ia(instruccion: str) -> str:
    """
    Dispatcher inteligente basado en palabras clave + clasificación Ollama.
    Toma la instrucción del usuario en lenguaje natural y decide qué comando ejecutar.
    Todos los tipos de documento (Word, Excel, PPT) soportan los tres niveles:
      - Básico: Ollama local
      - Complejo: Una llamada a Gemini/ChatGPT con JSON estructurado
      - Deep Research: Múltiples llamadas iterativas a Gemini por sección/hoja/slide
    """
    instruccion_lower = instruccion.lower()

    # --- LISTAR ---
    if "lista" in instruccion_lower or "mostrar archivos" in instruccion_lower:
        return cmd_listar()

    # --- Detectar nivel de complejidad ---
    # Deep Research: keywords explícitas o combinación de largo + profundidad
    KEYWORDS_DEEP = [
        "investiga a fondo", "deep research", "análisis profundo", "analisis profundo",
        "investigación detallada", "investigacion detallada",
        "informe completo", "reporte completo", "estudio completo",
        "con tablas de datos", "con múltiples hojas", "con multiples hojas"
    ]
    es_deep_research = any(kw in instruccion_lower for kw in KEYWORDS_DEEP)

    KEYWORDS_COMPLEJO = [
        "complejo", "chatgpt", "gemini", "extenso", "investiga", "noticias",
        "detallado", "creame un", "créame un", "genera un informe", "genera una presentación",
        "genera un excel", "crea un informe", "crea una presentación",
        "con referencias", "con datos reales", "formato apa"
    ]
    es_complejo = es_deep_research or len(instruccion) > 80 or any(kw in instruccion_lower for kw in KEYWORDS_COMPLEJO)

    motor_ia = "chatgpt" if "chatgpt" in instruccion_lower else "gemini"

    # Clasificar tipo de documento con Ollama (o fallback semántico)
    tipo_documento = clasificar_intencion_con_ollama(instruccion)

    # Fallback semántico si Ollama falla o responde DESCONOCIDO
    if tipo_documento == "DESCONOCIDO":
        if any(kw in instruccion_lower for kw in ["word", "informe", "reporte", "documento", "memo"]): tipo_documento = "WORD"
        elif any(kw in instruccion_lower for kw in ["excel", "hoja de cálculo", "tabla de datos", "base de datos", "dataset"]): tipo_documento = "EXCEL"
        elif any(kw in instruccion_lower for kw in ["ppt", "presentación", "presentacion", "powerpoint", "diapositivas", "slides"]): tipo_documento = "PPT"

    # ─── Helper: extraer tema y nombre de archivo ───
    def _extraer_tema_y_nombre(fallback: str):
        match = re.search(r"sobre (.+?)(?:\.|,|$|ll[aá]male)", instruccion_lower)
        tema = match.group(1).strip() if match else fallback
        return tema, obtener_nombre_seguro(instruccion, tema)

    # --- WORD ---
    if tipo_documento == "WORD":
        tema, nombre_limpio = _extraer_tema_y_nombre("tema_general")
        if es_deep_research:
            return cmd_crear_word_deep_research(instruccion, f"{nombre_limpio}.docx", motor=motor_ia)
        elif es_complejo:
            return cmd_crear_word_complejo_con_chatgpt(instruccion, f"{nombre_limpio}.docx", motor=motor_ia)
        else:
            return cmd_crear_docx_profesional(titulo=f"Informe: {tema}", tema=tema, filename=f"{nombre_limpio}.docx")

    # --- EXCEL ---
    elif tipo_documento == "EXCEL":
        if "formato" in instruccion_lower or "formatear" in instruccion_lower:
            return "Comando de formatear Excel detectado. Selecciona el archivo primero en la GUI y usa 'formatear'."
        tema, nombre_limpio = _extraer_tema_y_nombre("datos_generados")
        if es_deep_research:
            return cmd_crear_excel_deep_research(instruccion, f"{nombre_limpio}.xlsx", motor=motor_ia)
        elif es_complejo:
            return cmd_crear_excel_complejo_con_chatgpt(instruccion, f"{nombre_limpio}.xlsx", motor=motor_ia)
        else:
            datos = [["Nombre", "Valor"], ["Dato A", 10], ["Dato B", 20]]
            return cmd_escribir_excel(f"{nombre_limpio}.xlsx", "Hoja1", datos)

    # --- POWERPOINT ---
    elif tipo_documento == "PPT":
        tema, nombre_limpio = _extraer_tema_y_nombre("tema_general")
        if es_deep_research:
            return cmd_crear_ppt_deep_research(instruccion, f"{nombre_limpio}.pptx", motor=motor_ia)
        elif es_complejo:
            return cmd_crear_ppt_compleja_con_chatgpt(instruccion, f"{nombre_limpio}.pptx", motor=motor_ia)
        else:
            return cmd_crear_ppt_compleja_con_chatgpt(instruccion, f"{nombre_limpio}.pptx", motor=motor_ia)

    # --- TXT / TEMAS ---
    elif "escribe" in instruccion_lower or "crea un tema" in instruccion_lower:
        tema, nombre_limpio = _extraer_tema_y_nombre("tema_generico")
        return cmd_crear_tema(tema, f"{nombre_limpio}.txt")

    # --- MEJORAR / PROFUNDIZAR WORD CON GEMINI ---
    elif any(kw in instruccion_lower for kw in [
        "profundiza el word", "profundiza el documento", "mejora el word",
        "amplía el word", "amplia el word", "sube el word",
        "profundiza el archivo", "mejora el archivo word",
        "profundizar word", "mejorar word"
    ]):
        match_archivo = re.search(r'(?:word|documento|archivo)\s+([a-zA-Z0-9_.\-áéíóúñ]+\.docx?)', instruccion_lower)
        if not match_archivo:
            match_archivo = re.search(r'([a-zA-Z0-9_.\-]+\.docx?)', instruccion_lower)
        if match_archivo:
            nombre_archivo = match_archivo.group(1)
            # Extraer instruccion adicional si la hay
            instruccion_extra = re.sub(r'(?:profundiza|mejora|amplía|amplia|sube)[^:]*(?:word|documento|archivo)[^:]*(?:\s+\S+\.docx?)?\s*', "", instruccion_lower).strip()
            return cmd_profundizar_word_con_gemini(nombre_archivo, instruccion_extra, motor=motor_ia)
        return (
            "Para profundizar un Word, coloca el archivo en la carpeta 'inputs/' y usa:\n"
            "'Profundiza el word [nombre_archivo].docx'\n"
            "Ejemplo: 'Profundiza el word reporte_mercado.docx y añade datos de 2024'"
        )

    # --- REVISAR / MEJORAR / RESUMIR ARCHIVO (generico) ---
    elif any(kw in instruccion_lower for kw in [
        "revisa el archivo", "mejora el archivo", "lee el archivo",
        "analiza el archivo", "resume el archivo", "resumir el archivo"
    ]):
        match_archivo = re.search(r'archivo\s+([a-zA-Z0-9_.\-]+)', instruccion_lower)
        if match_archivo:
            return cmd_revisar_mejorar_archivo_con_chatgpt(instruccion, match_archivo.group(1))
        return "Para revisar o mejorar un archivo indica su nombre con extensión (ej. 'revisa el archivo datos.txt')."

    # --- RESUMIR WEB ---
    elif "resume la web" in instruccion_lower or "resumir la web" in instruccion_lower or "http" in instruccion_lower:
        match = re.search(r"(https?://\S+)", instruccion_lower)
        if match:
            return cmd_resumir_web(match.group(1))
        return "Comando de resumir web detectado, pero no encontré una URL válida."

    # --- PREGUNTA DIRECTA A IA ---
    elif any(kw in instruccion_lower for kw in ["preguntale a chatgpt", "preguntale a gemini", "usar ia web"]):
        prompt_directo = instruccion
        for kw in ["preguntale a chatgpt", "preguntale a gemini", "usar ia web"]:
            prompt_directo = prompt_directo.replace(kw, "").replace(kw.replace("a", "á"), "")
        prompt_directo = prompt_directo.strip()
        if not prompt_directo: return f"Por favor dime qué quieres preguntarle."
        return enviar_a_ia_externa(prompt_directo, motor_ia)

    # --- FALLBACK: Instrucción compleja sin tipo detectado (asumimos WORD) ---
    elif es_deep_research:
        tema, nombre_limpio = _extraer_tema_y_nombre("investigacion_generica")
        return cmd_crear_word_deep_research(instruccion, f"{nombre_limpio}.docx", motor=motor_ia)

    elif es_complejo:
        tema, nombre_limpio = _extraer_tema_y_nombre("investigacion_general")
        return cmd_crear_word_complejo_con_chatgpt(instruccion, f"{nombre_limpio}.docx", motor=motor_ia)

    else:
        return f"Instrucción no reconocida. Por favor especifica el tipo de archivo (word, excel, ppt) y el tema.\nInstrucción recibida: {instruccion}"

# Prueba local
if __name__ == "__main__":
    print(dispatcher_ia("hazme un informe en word sobre stablecoins"))
