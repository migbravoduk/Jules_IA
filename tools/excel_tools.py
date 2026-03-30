import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill
from sandbox import resolve_path
import os

def escribir_excel(filename: str, hoja: str, datos: list, context: str = "outputs") -> str:
    """
    Crea un nuevo archivo Excel o sobrescribe si existe.
    - datos debe ser una lista de listas: [[header1, header2], [val1, val2]]
    """
    try:
        filepath = resolve_path(filename, context)
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = hoja

        for fila in datos:
            ws.append(fila)

        wb.save(filepath)
        return f"Excel escrito con éxito: {filepath}"
    except Exception as e:
        return f"Error escribiendo Excel: {e}"

def actualizar_excel_existente(filename: str, hoja: str, datos: list, context: str = "outputs") -> str:
    """Abre un Excel existente y añade filas al final."""
    try:
        filepath = resolve_path(filename, context)
        if not os.path.exists(filepath):
            return f"Error: No se encontró el archivo {filepath}"

        wb = openpyxl.load_workbook(filepath)
        if hoja in wb.sheetnames:
            ws = wb[hoja]
        else:
            ws = wb.create_sheet(hoja)

        for fila in datos:
            ws.append(fila)

        wb.save(filepath)
        return f"Excel actualizado con éxito: {filepath}"
    except Exception as e:
        return f"Error actualizando Excel: {e}"

def aplicar_formato_excel(filename: str, context: str = "outputs") -> str:
    """
    Aplica formato básico a un Excel:
    - Encabezados en negrita con fondo
    - Alineación centrada
    - Autofit aproximado de columnas
    """
    try:
        filepath = resolve_path(filename, context)
        if not os.path.exists(filepath):
            return f"Error: No se encontró el archivo {filepath}"

        wb = openpyxl.load_workbook(filepath)
        for hoja_nombre in wb.sheetnames:
            ws = wb[hoja_nombre]

            # Formatear encabezado (primera fila)
            fill = PatternFill(start_color="D3D3D3", end_color="D3D3D3", fill_type="solid")
            for cell in ws[1]:
                cell.font = Font(bold=True)
                cell.fill = fill
                cell.alignment = Alignment(horizontal="center", vertical="center")

            # Autofit simple (ajuste de ancho de columnas por contenido)
            for col in ws.columns:
                max_length = 0
                column = col[0].column_letter # Get the column name
                for cell in col:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(cell.value)
                    except:
                        pass
                adjusted_width = (max_length + 2)
                ws.column_dimensions[column].width = adjusted_width

        nuevo_nombre = os.path.splitext(filename)[0] + "_formateado.xlsx"
        nuevo_filepath = resolve_path(nuevo_nombre, context)
        wb.save(nuevo_filepath)
        return f"Excel formateado con éxito. Guardado como: {nuevo_filepath}"
    except Exception as e:
        return f"Error formateando Excel: {e}"
