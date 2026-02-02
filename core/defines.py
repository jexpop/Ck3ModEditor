import os
import shutil
import re


# ---------------------------------------------------------
# Leer END_DATE del juego
# ---------------------------------------------------------
def read_end_date(game_root):
    """
    Lee la fecha END_DATE del archivo:
    <game_root>/common/defines/00_defines.txt

    Devuelve la fecha como string ("1453.1.1") o None.
    """

    defines_path = os.path.join(game_root, "common", "defines", "00_defines.txt")

    if not os.path.isfile(defines_path):
        return None

    try:
        with open(defines_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        with open(defines_path, "r", encoding="latin-1") as f:
            lines = f.readlines()

    for line in lines:
        if "END_DATE" in line:
            m = re.search(r'"([^"]+)"', line)
            if m:
                return m.group(1)

    return None


# ---------------------------------------------------------
# Leer END_DATE del mod
# ---------------------------------------------------------
def read_mod_end_date(mod_root):
    """
    Lee END_DATE desde el mod si existe.
    Devuelve la fecha o None.
    """
    defines_path = os.path.join(mod_root, "common", "defines", "00_defines.txt")

    if not os.path.isfile(defines_path):
        return None

    try:
        with open(defines_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        with open(defines_path, "r", encoding="latin-1") as f:
            lines = f.readlines()

    for line in lines:
        if "END_DATE" in line:
            m = re.search(r'"([^"]+)"', line)
            if m:
                return m.group(1)

    return None


# ---------------------------------------------------------
# Guardar END_DATE en el mod (con backup)
# ---------------------------------------------------------
def write_end_date(game_root, mod_root, backup_root, new_date):
    """
    - Crea backup del archivo original
    - Copia el archivo al mod
    - Sustituye solo la línea END_DATE
    """

    src = os.path.join(game_root, "common", "defines", "00_defines.txt")
    dst_mod = os.path.join(mod_root, "common", "defines", "00_defines.txt")
    dst_backup = os.path.join(backup_root, "common", "defines", "00_defines.txt")

    if not os.path.isfile(src):
        return False

    # Crear carpetas necesarias
    os.makedirs(os.path.dirname(dst_mod), exist_ok=True)
    os.makedirs(os.path.dirname(dst_backup), exist_ok=True)

    # Guardar backup determinista
    shutil.copy2(src, dst_backup)

    # Leer original
    try:
        with open(src, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        with open(src, "r", encoding="latin-1") as f:
            lines = f.readlines()

    # Reemplazar END_DATE
    new_lines = []
    replaced = False

    for line in lines:
        if "END_DATE" in line:
            new_lines.append(f'\tEND_DATE = "{new_date}"\n')
            replaced = True
        else:
            new_lines.append(line)

    if not replaced:
        new_lines.append(f'\tEND_DATE = "{new_date}"\n')

    # Guardar en el mod
    with open(dst_mod, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    return True
