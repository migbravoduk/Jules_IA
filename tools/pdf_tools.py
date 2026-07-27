import pdfplumber
import os
from pathlib import Path
from config import BASE_DIRS

def extraer_tablas_a_excel(filepath: str) -> str:
    """
    Extrae tablas de un archivo PDF y las guarda en un archivo de Excel básico
    usando openpyxl directamente.
    """
    if not filepath.endswith('.pdf'):
        return "El archivo debe ser un PDF."
        
    try:
        todas_las_tablas = []
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                tablas_pagina = page.extract_tables()
                for tabla in tablas_pagina:
                    # pdfplumber devuelve None para celdas vacias, las limpiamos a ""
                    tabla_limpia = []
                    for fila in tabla:
                        tabla_limpia.append([celda if celda is not None else "" for celda in fila])
                    todas_las_tablas.append(tabla_limpia)
                    
        if not todas_las_tablas:
            return f"No se encontraron tablas estructuradas en el PDF '{Path(filepath).name}'."
            
        # Combinar todas las tablas en una sola matriz para un Excel simple (Hoja1)
        # Separadas por una fila vacia
        matriz_final = []
        for i, tabla in enumerate(todas_las_tablas):
            matriz_final.append([f"--- Tabla {i+1} ---"])
            matriz_final.extend(tabla)
            matriz_final.append([])
            
        nombre_salida = f"tablas_{Path(filepath).stem}.xlsx"
        # Usamos la funcion base de excel
        # Suponiendo que cmd_escribir_excel acepta una lista de listas
        # pero la firma real en main no permite enviar la matriz directa,
        # así que la guardaremos usando openpyxl directo aquí para más control.
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Tablas Extraidas"
        for fila in matriz_final:
            ws.append(fila)
            
        ruta_salida = BASE_DIRS["outputs"] / nombre_salida
        wb.save(ruta_salida)
        return f"✅ Extracción completada. Tablas guardadas en '{nombre_salida}' en la carpeta outputs."
        
    except Exception as e:
        return f"Error procesando PDF: {e}"
