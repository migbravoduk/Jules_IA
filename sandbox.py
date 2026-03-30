import os
from pathlib import Path
from config import BASE_DIRS

def resolve_path(filename: str, context: str = "outputs") -> Path:
    """
    Resuelve una ruta de archivo dentro del sandbox permitido (`BASE_DIRS`).
    Evita el acceso a directorios superiores usando '..'.

    Args:
        filename (str): Nombre del archivo o ruta relativa.
        context (str): Contexto o directorio base ("proyecto", "templates", "outputs", "temp").

    Returns:
        Path: Ruta absoluta y segura dentro del sandbox.

    Raises:
        ValueError: Si el contexto no es válido o si se intenta salir del sandbox.
    """
    if context not in BASE_DIRS:
        raise ValueError(f"Contexto '{context}' no válido. Use uno de: {list(BASE_DIRS.keys())}")

    base_path = BASE_DIRS[context].resolve()
    # Construir la ruta y resolverla para eliminar '..'
    target_path = (base_path / filename).resolve()

    # Verificar si la ruta resuelta está dentro del directorio base
    # os.path.commonpath asegura que la ruta base sea un ancestro común
    try:
        common_path = os.path.commonpath([str(base_path), str(target_path)])
        if common_path != str(base_path):
             raise ValueError(f"Acceso denegado: intento de salir del sandbox ({filename})")
    except ValueError:
        raise ValueError(f"Acceso denegado o rutas inválidas: {filename}")

    return target_path

# Prueba rápida interna (se puede borrar después)
if __name__ == "__main__":
    try:
        print("Ruta segura:", resolve_path("test.txt"))
        print("Intento fallido:", resolve_path("../fuera.txt"))
    except Exception as e:
        print("Error detectado:", e)
