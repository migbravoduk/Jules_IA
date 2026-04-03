import os
import json
import requests
from bs4 import BeautifulSoup
from config import BASE_DIRS, OLLAMA_URL, OLLAMA_MODEL
from sandbox import resolve_path
import webbrowser
from pathlib import Path

# --- CORE ---
def ask_ollama(prompt: str, model: str = OLLAMA_MODEL) -> str:
    """Envía un prompt a Ollama local usando requests sin async."""
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        return result.get("response", "Sin respuesta.")
    except Exception as e:
        return f"Error conectando con Ollama: {e}"

from tools.word_tools import crear_documento_profesional, aplicar_formato_word
from tools.excel_tools import escribir_excel, aplicar_formato_excel, actualizar_excel_existente
from tools.ppt_tools import actualizar_ppt, crear_ppt_base

# --- COMANDOS BASE ---

def cmd_listar(context: str = "outputs") -> str:
    """Lista los archivos en el contexto especificado."""
    try:
        if context not in BASE_DIRS:
            return f"Error: Contexto '{context}' no válido."

        path = BASE_DIRS[context]
        files = [f.name for f in path.iterdir() if f.is_file()]

        if not files:
            return f"No hay archivos en {context}."

        return "\n".join(files)
    except Exception as e:
        return f"Error listando archivos: {e}"

def cmd_leer(filename: str, context: str = "outputs") -> str:
    """Lee el contenido de un archivo de texto en el sandbox."""
    try:
        filepath = resolve_path(filename, context)
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error leyendo {filename}: {e}"

def cmd_crear_txt(filename: str, contenido: str, context: str = "outputs") -> str:
    """Crea un archivo de texto en el sandbox."""
    try:
        filepath = resolve_path(filename, context)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(contenido)
        return f"Archivo {filename} creado en {context}."
    except Exception as e:
        return f"Error creando archivo {filename}: {e}"

def cmd_crear_tema(tema: str, filename: str, context: str = "outputs") -> str:
    """Genera contenido sobre un tema usando Ollama y lo guarda en un TXT."""
    prompt = f"Escribe un artículo detallado y estructurado sobre: {tema}. Usa formato claro."
    resultado_ia = ask_ollama(prompt)

    if "Error conectando" in resultado_ia:
        return resultado_ia

    return cmd_crear_txt(filename, resultado_ia, context)

def cmd_resumir(filename: str, context: str = "outputs") -> str:
    """Lee un archivo y usa Ollama para resumirlo."""
    contenido = cmd_leer(filename, context)
    if contenido.startswith("Error"):
        return contenido

    prompt = f"Resume el siguiente texto en viñetas claras y concisas:\n\n{contenido}"
    return ask_ollama(prompt)

def cmd_reescribir(filename: str, instrucciones: str, context: str = "outputs") -> str:
    """Lee un archivo, lo reescribe con IA según instrucciones y lo guarda como _reescrito.txt."""
    contenido = cmd_leer(filename, context)
    if contenido.startswith("Error"):
        return contenido

    prompt = f"Reescribe el siguiente texto siguiendo estas instrucciones: {instrucciones}\n\nTexto original:\n{contenido}"
    resultado_ia = ask_ollama(prompt)

    if "Error conectando" in resultado_ia:
        return resultado_ia

    nuevo_nombre = Path(filename).stem + "_reescrito.txt"
    return cmd_crear_txt(nuevo_nombre, resultado_ia, context)

def cmd_abrir_web(url: str) -> str:
    """Abre una URL en el navegador web por defecto."""
    try:
        webbrowser.open(url)
        return f"Abriendo URL: {url}"
    except Exception as e:
         return f"Error abriendo web: {e}"

def cmd_resumir_web(url: str) -> str:
    """Extrae el texto de una web usando requests+BS4 y lo resume con IA."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        # Extraer párrafos principales
        paragraphs = soup.find_all('p')
        text = "\n".join([p.get_text() for p in paragraphs])

        # Limitar la longitud para evitar problemas con el prompt (aprox. primeros 3000 caracteres)
        text_trunc = text[:3000]

        if not text_trunc.strip():
            return "No se pudo extraer texto relevante de la página."

        prompt = f"Resume los puntos clave del siguiente artículo web de manera concisa:\n\n{text_trunc}"
        return ask_ollama(prompt)

    except Exception as e:
        return f"Error resumiendo web ({url}): {e}"

# --- COMANDOS OFFICE ---

def cmd_crear_docx_profesional(titulo: str, tema: str, filename: str, context: str = "outputs") -> str:
    """Usa IA para generar el contenido de un tema y lo guarda como un documento Word profesional."""
    prompt = f"Escribe un informe profesional sobre: {tema}. Usa viñetas, párrafos claros y subtítulos con #."
    contenido_ia = ask_ollama(prompt)

    if "Error conectando" in contenido_ia:
        return contenido_ia

    return crear_documento_profesional(titulo, contenido_ia, filename, context)

def cmd_escribir_excel(filename: str, hoja: str, datos: list, context: str = "outputs") -> str:
    """Escribe una lista de listas en un archivo Excel."""
    return escribir_excel(filename, hoja, datos, context)

def cmd_formatear_excel(filename: str, context: str = "outputs") -> str:
    """Aplica formato profesional a un archivo Excel existente."""
    return aplicar_formato_excel(filename, context)

def cmd_actualizar_ppt(filename: str, reemplazos_dict: dict, context: str = "outputs") -> str:
    """Busca y reemplaza texto en un archivo PPTX."""
    return actualizar_ppt(filename, reemplazos_dict, context)
