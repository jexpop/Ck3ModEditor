import os
import shutil


# ---------------------------------------------------------
# Crear carpeta si no existe
# ---------------------------------------------------------
def ensure_dir(path):
    """
    Crea una carpeta si no existe.
    """
    os.makedirs(path, exist_ok=True)


# ---------------------------------------------------------
# Copiar archivo con preservación de metadatos
# ---------------------------------------------------------
def copy_file(src, dst):
    """
    Copia un archivo preservando metadatos.
    Crea las carpetas necesarias automáticamente.
    """
    ensure_dir(os.path.dirname(dst))
    shutil.copy2(src, dst)


# ---------------------------------------------------------
# Leer archivo con fallback de codificación
# ---------------------------------------------------------
def read_text_file(path):
    """
    Lee un archivo intentando UTF-8 y luego Latin-1.
    Devuelve el contenido como string.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        with open(path, "r", encoding="latin-1") as f:
            return f.read()


# ---------------------------------------------------------
# Leer archivo línea a línea con fallback
# ---------------------------------------------------------
def read_text_lines(path):
    """
    Igual que read_text_file, pero devuelve lista de líneas.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.readlines()
    except UnicodeDecodeError:
        with open(path, "r", encoding="latin-1") as f:
            return f.readlines()


# ---------------------------------------------------------
# Escribir archivo asegurando ruta
# ---------------------------------------------------------
def write_text_file(path, content):
    """
    Escribe un archivo asegurando que la ruta existe.
    """
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


# ---------------------------------------------------------
# Comprobar si un archivo existe
# ---------------------------------------------------------
def file_exists(path):
    return os.path.isfile(path)


# ---------------------------------------------------------
# Comprobar si una carpeta existe
# ---------------------------------------------------------
def dir_exists(path):
    return os.path.isdir(path)
