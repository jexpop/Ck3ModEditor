import os
import re

# -----------------------------
# Expresiones regulares
# -----------------------------
DATE_RE = re.compile(r'(\d+)\.(\d+)\.(\d+)')
TITLE_RE = re.compile(r'^\s*([becdk]_[A-Za-z0-9_]+)\s*=\s*\{')
HOLDER_RE = re.compile(r'holder\s*=\s*(\w+)')
LIEGE_RE = re.compile(r'liege\s*=\s*(\w+)')


# -----------------------------
# Parsear un archivo individual
# -----------------------------
def parse_title_history_file(path):
    """
    Extrae TODOS los títulos dentro del archivo.
    Ejemplo:
        k_iceland.txt contiene:
            c_sudurland = { ... }
            c_vesturland = { ... }
            b_reydarfjall = { ... }
    """
    data = {}
    current_title = None
    current_year = None
    stack = 0

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
            line = raw.strip()

            # Inicio de título
            m = TITLE_RE.match(line)
            if m:
                current_title = m.group(1)
                data[current_title] = {"holder": [], "liege": []}
                stack = 1
                current_year = None
                #print(" Título:", current_title)
                continue

            # Contador de llaves
            if "{" in line:
                stack += line.count("{")
            if "}" in line:
                stack -= line.count("}")
                if stack <= 0:
                    current_title = None
                    current_year = None
                continue

            if not current_title:
                continue

            # Fecha
            m = DATE_RE.search(line)
            if m:
                current_year = int(m.group(1))
                continue

            # Holder
            m = HOLDER_RE.search(line)
            if m and current_year is not None:
                data[current_title]["holder"].append((current_year, m.group(1)))
                continue

            # Liege
            m = LIEGE_RE.search(line)
            if m and current_year is not None:
                data[current_title]["liege"].append((current_year, m.group(1)))
                continue

    return data


# -----------------------------
# Cargar historia del juego y del mod
# -----------------------------
def load_all_title_history(root):
    result = {}

    folder = os.path.join(root, "history", "titles")
    if not os.path.isdir(folder):
        print("NO EXISTE:", folder)
        return result

    #print("Leyendo history/titles desde:", folder)

    for fname in os.listdir(folder):
        if not fname.endswith(".txt"):
            continue

        path = os.path.join(folder, fname)
        file_data = parse_title_history_file(path)
        #print(f"{fname}: {len(file_data)} títulos")

        result.update(file_data)

    #print("TOTAL títulos cargados:", len(result))

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
