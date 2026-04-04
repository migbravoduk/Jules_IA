from pptx import Presentation
from sandbox import resolve_path
import os
import json

def crear_ppt_base(filename: str, titulo: str, subtitulo: str, context: str = "outputs") -> str:
    """Crea una presentación PPTX básica con un slide de título."""
    try:
        prs = Presentation()
        title_slide_layout = prs.slide_layouts[0]
        slide = prs.slides.add_slide(title_slide_layout)
        title = slide.shapes.title
        subtitle = slide.placeholders[1]

        title.text = titulo
        subtitle.text = subtitulo

        filepath = resolve_path(filename, context)
        prs.save(filepath)
        return f"PPT creado con éxito: {filepath}"
    except Exception as e:
        return f"Error creando PPT: {e}"

def actualizar_ppt(filename: str, reemplazos_dict: dict, context: str = "outputs") -> str:
    """
    Busca texto en todos los shapes de la presentación y lo reemplaza con el diccionario.
    - reemplazos_dict: {"{{TITULO}}": "Nuevo Título"}
    """
    try:
        filepath = resolve_path(filename, context)
        if not os.path.exists(filepath):
            return f"Error: No se encontró el archivo {filepath}"

        prs = Presentation(filepath)
        reemplazos = 0

        for slide in prs.slides:
            for shape in slide.shapes:
                if not shape.has_text_frame:
                    continue
                for paragraph in shape.text_frame.paragraphs:
                    for run in paragraph.runs:
                        for key, value in reemplazos_dict.items():
                            if key in run.text:
                                run.text = run.text.replace(key, value)
                                reemplazos += 1

        nuevo_nombre = os.path.splitext(filename)[0] + "_actualizado.pptx"
        nuevo_filepath = resolve_path(nuevo_nombre, context)
        prs.save(nuevo_filepath)
        return f"PPT actualizado con {reemplazos} reemplazos. Guardado como: {nuevo_filepath}"
    except Exception as e:
        return f"Error actualizando PPT: {e}"

def insertar_texto_en_slide(filename: str, titulo: str, viñetas: list, context: str = "outputs") -> str:
    """Añade un nuevo slide con título y viñetas al final de la presentación."""
    try:
        filepath = resolve_path(filename, context)
        if not os.path.exists(filepath):
            return f"Error: No se encontró el archivo {filepath}"

        prs = Presentation(filepath)
        bullet_slide_layout = prs.slide_layouts[1] # Título y contenido
        slide = prs.slides.add_slide(bullet_slide_layout)
        shapes = slide.shapes

        title_shape = shapes.title
        body_shape = shapes.placeholders[1]

        title_shape.text = titulo
        tf = body_shape.text_frame

        for idx, viñeta in enumerate(viñetas):
            if idx == 0:
                tf.text = viñeta
            else:
                p = tf.add_paragraph()
                p.text = viñeta
                p.level = 0

        prs.save(filepath)
        return f"Slide insertado con éxito en: {filepath}"
    except Exception as e:
        return f"Error insertando slide en PPT: {e}"

def crear_ppt_compleja_desde_json(filename: str, json_str: str, context: str = "outputs") -> str:
    """
    Toma un string JSON con la estructura de la PPT y crea el archivo completo.
    Estructura JSON esperada:
    [
        {"tipo": "portada", "titulo": "...", "subtitulo": "..."},
        {"tipo": "contenido", "titulo": "...", "viñetas": ["...", "..."]},
        ...
    ]
    """
    try:
        data = json.loads(json_str)
        if not data:
            return "Error: JSON vacío."

        filepath = resolve_path(filename, context)
        prs = Presentation()

        for slide_data in data:
            tipo = slide_data.get("tipo", "contenido")
            titulo = slide_data.get("titulo", "")

            if tipo == "portada":
                layout = prs.slide_layouts[0] # Titulo + Subtitulo
                slide = prs.slides.add_slide(layout)
                slide.shapes.title.text = titulo
                if "subtitulo" in slide_data and len(slide.placeholders) > 1:
                    slide.placeholders[1].text = slide_data["subtitulo"]
            elif tipo == "cita":
                # Diseño visual de cita: Layout de solo título centrado o Título principal
                layout = prs.slide_layouts[2] # Header de sección
                slide = prs.slides.add_slide(layout)
                slide.shapes.title.text = slide_data.get("texto", titulo)
            else:
                # Contenido o Indice normal
                layout = prs.slide_layouts[1] # Titulo + Viñetas
                slide = prs.slides.add_slide(layout)
                slide.shapes.title.text = titulo

                viñetas = slide_data.get("viñetas", [])
                if viñetas and len(slide.placeholders) > 1:
                    tf = slide.placeholders[1].text_frame
                    # Ajuste para evitar aglomeraciones:
                    tf.word_wrap = True
                    from pptx.util import Pt
                    for idx, viñeta in enumerate(viñetas):
                        if idx == 0:
                            tf.text = viñeta
                            tf.paragraphs[0].space_after = Pt(10)
                        else:
                            p = tf.add_paragraph()
                            p.text = viñeta
                            p.level = 0
                            p.space_after = Pt(10) # Espaciado más profesional entre viñetas

        prs.save(filepath)
        return f"PPT Complejo creado con éxito: {filepath}"
    except json.JSONDecodeError as e:
         return f"Error parseando JSON de PPT: {e}\nJSON Recibido:\n{json_str[:500]}"
    except Exception as e:
         return f"Error creando PPT complejo: {e}"
