import os
import re

# -----------------------------
# Expresiones regulares
# -----------------------------
DATE_RE = re.compile(r'(\d+)\.(\d+)\.(\d+)')
TITLE_RE = re.compile(r'^(\w+)\s*=\s*\{')
HOLDER_RE = re.compile(r'holder\s*=\s*(\d+)')
LIEGE_RE = re.compile(r'liege\s*=\s*"?(.*?)"?$')


# -----------------------------
# Parsear un archivo individual
# -----------------------------
def parse_title_history_file(path):
    data = {}
    current_title = None
    current_year = None

    # CK3 tiene archivos con codificaciones raras → errors="ignore"
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()

            # Detectar inicio de título
            m = TITLE_RE.match(line)
            if m:
                current_title = m.group(1)
                data[current_title] = {"holder": [], "liege": []}
                continue

            # Detectar fecha
            m = DATE_RE.search(line)
            if m:
                current_year = int(m.group(1))
                continue

            # Detectar holder
            m = HOLDER_RE.search(line)
            if m and current_title and current_year is not None:
                data[current_title]["holder"].append((current_year, int(m.group(1))))
                continue

            # Detectar liege
            m = LIEGE_RE.search(line)
            if m and current_title and current_year is not None:
                data[current_title]["liege"].append((current_year, m.group(1)))
                continue

    return data


# -----------------------------
# Cargar historia del juego y del mod
# -----------------------------
def load_all_title_history(game_root, mod_root=None):
    """
    Carga todos los archivos de history/titles/ del juego y del mod.
    El mod sobrescribe al juego.
    """
    result = {}

    # -----------------------------
    # 1. Cargar historia del juego
    # -----------------------------
    game_folder = os.path.join(game_root, "history", "titles")
    if os.path.isdir(game_folder):
        for fname in os.listdir(game_folder):
            if fname.endswith(".txt"):
                path = os.path.join(game_folder, fname)
                file_data = parse_title_history_file(path)
                for title, info in file_data.items():
                    result[title] = info

    # -----------------------------
    # 2. Cargar historia del mod (sobrescribe)
    # -----------------------------
    if mod_root:
        mod_folder = os.path.join(mod_root, "history", "titles")
        if os.path.isdir(mod_folder):
            for fname in os.listdir(mod_folder):
                if fname.endswith(".txt"):
                    path = os.path.join(mod_folder, fname)
                    file_data = parse_title_history_file(path)
                    for title, info in file_data.items():
                        result[title] = info  # sobrescribe al juego

    # -----------------------------
    # Ordenar listas por fecha
    # -----------------------------
    for title, info in result.items():
        info["holder"].sort()
        info["liege"].sort()

    return result


# -----------------------------
# Obtener holder en un año concreto
# -----------------------------
def get_holder_at_year(history, year):
    holder_list = history.get("holder", [])
    last = None
    for y, h in holder_list:
        if y <= year:
            last = h
        else:
            break
    return last
