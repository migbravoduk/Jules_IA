import pandas as pd
import matplotlib.pyplot as plt
import os
from pathlib import Path
from config import BASE_DIRS
from tools.api_ai_tools import ask_gemini_api
from tools.word_tools import crear_word_complejo_desde_json
import json
import re

def analizar_datos_csv(filepath: str, instruccion: str):
    """
    Lee un CSV o Excel, extrae estadísticas básicas y usa Gemini para generar un reporte.
    También genera un gráfico básico si los datos lo permiten.
    """
    try:
        if filepath.endswith('.csv'):
            df = pd.read_csv(filepath)
        elif filepath.endswith('.xlsx'):
            df = pd.read_excel(filepath)
        else:
            return "Formato no soportado. Usa CSV o Excel."
    except Exception as e:
        return f"Error leyendo el archivo de datos: {e}"

    # Limitar datos para el prompt
    head = df.head(5).to_csv(index=False)
    stats = df.describe(include='all').to_csv()
    cols = ", ".join(df.columns.tolist())

    print(f"📊 [Data Tools] Datos cargados. Columnas: {cols}")

    # Generar gráfico simple si hay columnas numéricas y categóricas
    num_cols = df.select_dtypes(include='number').columns.tolist()
    cat_cols = df.select_dtypes(exclude='number').columns.tolist()
    grafico_path = ""

    if num_cols and cat_cols:
        try:
            plt.figure(figsize=(10, 6))
            # Agrupar por la primera columna categórica y sumar la primera numérica
            cat = cat_cols[0]
            num = num_cols[0]
            agrupado = df.groupby(cat)[num].sum().nlargest(10)
            
            agrupado.plot(kind='bar', color='skyblue')
            plt.title(f'Top 10: {num} por {cat}')
            plt.ylabel(num)
            plt.xlabel(cat)
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            grafico_filename = f"grafico_{Path(filepath).stem}.png"
            grafico_path_full = BASE_DIRS["temp"] / grafico_filename
            plt.savefig(grafico_path_full)
            grafico_path = str(grafico_path_full)
            print(f"📈 [Data Tools] Gráfico generado en: {grafico_path}")
        except Exception as e:
            print(f"⚠️ No se pudo generar gráfico: {e}")

    # Prompt para IA
    prompt = (
        f"Actúa como un Analista de Datos Experto.\n"
        f"El usuario pide: '{instruccion}'.\n"
        f"Aquí tienes un resumen de los datos del archivo '{Path(filepath).name}':\n\n"
        f"Columnas: {cols}\n\n"
        f"Muestra de datos (5 filas):\n{head}\n\n"
        f"Estadísticas:\n{stats}\n\n"
        f"Genera un reporte analítico. Si se generó un gráfico, su ruta es '{grafico_path}'.\n"
        f"CRÍTICO: Responde ÚNICAMENTE con array JSON para crear un documento Word.\n"
        f"Formato esperado:\n"
        f"[\n"
        f"  {{\"tipo\": \"titulo\", \"texto\": \"Reporte de Datos\"}},\n"
        f"  {{\"tipo\": \"parrafo\", \"texto\": \"Análisis de los datos...\"}},\n"
        f"  {{\"tipo\": \"lista\", \"items\": [\"Hallazgo 1\", \"Hallazgo 2\"]}}\n"
        f"]"
    )

    respuesta = ask_gemini_api(prompt)
    if respuesta.startswith("❌"):
        return respuesta
    
    # Limpiar JSON
    texto = respuesta.strip()
    if "```json" in texto:
        texto = texto.split("```json")[1].split("```")[0].strip()
    elif "```" in texto:
        texto = texto.split("```")[1].split("```")[0].strip()
    
    try:
        json_data = json.loads(texto)
        # Añadir referencia al gráfico si existe
        if grafico_path:
            json_data.append({"tipo": "parrafo", "texto": f"Nota: Se ha generado un gráfico en {grafico_path}"})
            
        salida_docx = BASE_DIRS["outputs"] / f"reporte_datos_{Path(filepath).stem}.docx"
        crear_word_complejo_desde_json(str(salida_docx), json.dumps(json_data))
        return f"✅ Análisis de datos completado. Reporte generado: {salida_docx.name}"
    except Exception as e:
        return f"Error procesando reporte JSON: {e}"
