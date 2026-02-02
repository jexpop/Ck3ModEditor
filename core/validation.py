import os
import difflib


# ---------------------------------------------------------
# Recolectar archivos de un módulo
# ---------------------------------------------------------
def collect_module_files(game_root, backup_root, rel_path):
    """
    Devuelve dos diccionarios:
    - game_files[rel] = ruta absoluta en el juego
    - backup_files[rel] = ruta absoluta en el backup
    """

    src_game = os.path.join(game_root, rel_path)
    src_backup = os.path.join(backup_root, rel_path)

    game_files = {}
    backup_files = {}

    # Archivos del juego
    if os.path.isdir(src_game):
        for base, _, files in os.walk(src_game):
            for f in files:
                full = os.path.join(base, f)
                rel = os.path.relpath(full, src_game)
                game_files[rel] = full

    # Archivos del backup
    if os.path.isdir(src_backup):
        for base, _, files in os.walk(src_backup):
            for f in files:
                full = os.path.join(base, f)
                rel = os.path.relpath(full, src_backup)
                backup_files[rel] = full

    return game_files, backup_files


# ---------------------------------------------------------
# Comparar contenido de dos archivos
# ---------------------------------------------------------
def compare_file_contents(game_path, backup_path):
    """
    Compara dos archivos línea a línea.
    Devuelve:
    - True, [] si son iguales
    - False, diff_lines si son diferentes
    """

    game_lines = read_file_lines(game_path)
    backup_lines = read_file_lines(backup_path)

    if game_lines == backup_lines:
        return True, []

    diff = list(difflib.unified_diff(
        backup_lines,
        game_lines,
        fromfile="backup",
        tofile="game",
        lineterm=""
    ))

    return False, diff


# ---------------------------------------------------------
# Lectura segura de archivos
# ---------------------------------------------------------
def read_file_lines(path):
    """
    Lee un archivo intentando UTF-8 y luego Latin-1.
    Devuelve lista de líneas.
    """

    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.readlines()
    except UnicodeDecodeError:
        with open(path, "r", encoding="latin-1") as f:
            return f.readlines()
