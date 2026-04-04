from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from sandbox import resolve_path
import os

def crear_documento_profesional(titulo: str, contenido: str, filename: str, context: str = "outputs") -> str:
    """
    Crea un documento de Word con formato profesional:
    - Título centrado
    - Párrafos justificados
    - Formato limpio
    """
    try:
        doc = Document()

        # Título
        heading = doc.add_heading(titulo, level=0)
        heading.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Contenido (procesar saltos de línea y viñetas)
        lineas = contenido.split('\n')
        for linea in lineas:
            linea = linea.strip()
            if not linea:
                continue

            if linea.startswith("- ") or linea.startswith("* "):
                p = doc.add_paragraph(linea[2:], style='List Bullet')
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            elif linea.startswith("#"):
                # Subtítulos simples
                texto_limpio = linea.lstrip("#").strip()
                doc.add_heading(texto_limpio, level=2)
            else:
                p = doc.add_paragraph(linea)
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

        filepath = resolve_path(filename, context)
        doc.save(filepath)
        return f"Documento Word creado con éxito: {filepath}"

    except Exception as e:
        return f"Error creando documento Word: {e}"

def aplicar_formato_word(filename: str, context: str = "outputs") -> str:
    """
    Lee un documento de Word existente y normaliza su estilo (justificado).
    """
    try:
        filepath = resolve_path(filename, context)
        if not os.path.exists(filepath):
            return f"Error: No se encontró el archivo {filepath}"

        doc = Document(filepath)
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                paragraph.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

        nuevo_nombre = os.path.splitext(filename)[0] + "_formateado.docx"
        nuevo_filepath = resolve_path(nuevo_nombre, context)
        doc.save(nuevo_filepath)

        return f"Formato aplicado con éxito. Guardado como: {nuevo_filepath}"

    except Exception as e:
        return f"Error aplicando formato a Word: {e}"

import json
def crear_word_complejo_desde_json(filename: str, json_str: str, context: str = "outputs") -> str:
    """
    Crea un documento de Word extenso a partir de un JSON estructurado de ChatGPT.
    Estructura esperada:
    [
        {"tipo": "titulo", "texto": "Título Principal"},
        {"tipo": "subtitulo", "texto": "Sección 1"},
        {"tipo": "parrafo", "texto": "Contenido del párrafo..."},
        {"tipo": "lista", "items": ["Punto 1", "Punto 2"]},
        {"tipo": "tabla", "filas": [["A", "B"], ["1", "2"]]}
    ]
    """
    try:
        data = json.loads(json_str)
        if not data:
            return "Error: JSON vacío o mal formado."

        doc = Document()

        for bloque in data:
            tipo = bloque.get("tipo", "parrafo")

            if tipo == "titulo":
                heading = doc.add_heading(bloque.get("texto", ""), level=0)
                heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
            elif tipo == "subtitulo":
                heading = doc.add_heading(bloque.get("texto", ""), level=1) # Más jerarquía
                heading.style.font.bold = True
            elif tipo == "cita":
                # Uso de estilo Quote intenso para emular NotebookLM
                p = doc.add_paragraph(bloque.get("texto", ""), style='Intense Quote')
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            elif tipo == "lista" or tipo == "indice":
                items = bloque.get("items", bloque.get("viñetas", [])) # Soporta lista o indice
                for item in items:
                    p = doc.add_paragraph(item, style='List Bullet')
                    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            elif tipo == "tabla":
                filas = bloque.get("filas", [])
                if filas and len(filas) > 0:
                    num_cols = len(filas[0])
                    # Crear tabla en docx
                    table = doc.add_table(rows=1, cols=num_cols)
                    table.style = 'Table Grid'

                    # Encabezados
                    hdr_cells = table.rows[0].cells
                    for i, encabezado in enumerate(filas[0]):
                        hdr_cells[i].text = str(encabezado)
                        # Opcional: poner encabezados en negrita
                        for paragraph in hdr_cells[i].paragraphs:
                            for run in paragraph.runs:
                                run.font.bold = True

                    # Datos
                    for fila_datos in filas[1:]:
                        row_cells = table.add_row().cells
                        for i, valor in enumerate(fila_datos):
                            # Evitar error si una fila tiene menos elementos que los encabezados
                            if i < num_cols:
                                row_cells[i].text = str(valor)
                # Añadir un espacio después de la tabla
                doc.add_paragraph()
            else: # Párrafo por defecto
                p = doc.add_paragraph(bloque.get("texto", ""))
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

        filepath = resolve_path(filename, context)
        doc.save(filepath)
        return f"Documento Word Complejo creado con éxito: {filepath}"

    except json.JSONDecodeError as e:
         return f"Error parseando JSON de Word: {e}\nJSON Recibido:\n{json_str[:500]}"
    except Exception as e:
        return f"Error creando documento Word complejo: {e}"
