import os
import shutil
import re
from datetime import datetime


# ---------------------------------------------------------
# Cargar módulos desde data/modules.json
# ---------------------------------------------------------
def load_modules():
    import json
    if not os.path.isfile("data/modules.json"):
        return {}
    with open("data/modules.json", "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------
# Procesado de un módulo
# ---------------------------------------------------------
def process_module(game_key, module_name, game_root, mod_root, backup_root, offset, profile_name):
    """
    Procesa un módulo:
    - Copia archivos del juego al backup SIEMPRE
    - Copia archivos al mod SOLO si realmente cambian (offset aplicado)
    - NO crea carpetas vacías en el mod
    - Genera logs
    """

    # Cargar módulos
    modules = load_modules()
    if game_key not in modules or module_name not in modules[game_key]:
        return

    cfg = modules[game_key][module_name]
    rel_path = cfg["path"]
    ignore_ext = cfg.get("ignore_ext", [])

    src = os.path.join(game_root, rel_path)
    dst_mod = os.path.join(mod_root, rel_path)
    dst_backup = os.path.join(backup_root, rel_path)

    # Crear carpeta base del backup (SIEMPRE)
    os.makedirs(dst_backup, exist_ok=True)

    # ---------------------------------------------------------
    # LOGS
    # ---------------------------------------------------------
    log_path = os.path.join("logs", profile_name)
    os.makedirs(log_path, exist_ok=True)

    log_file = os.path.join(log_path, f"{module_name}.log")
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    with open(log_file, "a", encoding="utf-8") as log:
        log.write(f"\n--- Procesado {module_name} --- {datetime.now()}\n")

        if not os.path.isdir(src):
            log.write(f"ERROR: No existe la carpeta del juego: {src}\n")
            return

        # ---------------------------------------------------------
        # RECORRER ARCHIVOS DEL MÓDULO
        # ---------------------------------------------------------
        for base, _, files in os.walk(src):
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext in ignore_ext:
                    continue

                full_src = os.path.join(base, f)
                rel = os.path.relpath(full_src, src)

                full_mod = os.path.join(dst_mod, rel)
                full_backup = os.path.join(dst_backup, rel)

                # Crear carpeta destino del backup
                os.makedirs(os.path.dirname(full_backup), exist_ok=True)

                # ---------------------------------------------------------
                # COPIA SIEMPRE AL BACKUP
                # ---------------------------------------------------------
                shutil.copy2(full_src, full_backup)

                # ---------------------------------------------------------
                # PROCESAR ARCHIVOS DE TEXTO
                # ---------------------------------------------------------
                if ext in [".txt", ".yml"]:
                    # Leer original
                    try:
                        with open(full_src, "r", encoding="utf-8") as f_in:
                            original = f_in.read()
                    except UnicodeDecodeError:
                        with open(full_src, "r", encoding="latin-1") as f_in:
                            original = f_in.read()

                    # Aplicar offset
                    processed = apply_offset_to_file(full_src, offset)

                    # ¿Hubo cambios reales?
                    if processed != original:
                        # Crear carpeta SOLO si se va a copiar al mod
                        os.makedirs(os.path.dirname(full_mod), exist_ok=True)

                        with open(full_mod, "w", encoding="utf-8") as out:
                            out.write(processed)

                        log.write(f"Procesado (cambia fecha): {rel}\n")
                    else:
                        log.write(f"Sin cambios de fecha (no copiado al mod): {rel}\n")

                else:
                    # ---------------------------------------------------------
                    # ARCHIVOS NO TEXTUALES → copiar siempre al mod
                    # ---------------------------------------------------------
                    os.makedirs(os.path.dirname(full_mod), exist_ok=True)
                    shutil.copy2(full_src, full_mod)
                    log.write(f"Copiado sin cambios: {rel}\n")


# ---------------------------------------------------------
# Aplicar offset a un archivo
# ---------------------------------------------------------
def apply_offset_to_file(path, offset):
    """
    Aplica offset a fechas con formato:
    - 867.1.1
    - 1066.9.15
    - 1453.1.1
    """

    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
    except UnicodeDecodeError:
        with open(path, "r", encoding="latin-1") as f:
            text = f.read()

    # Regex para fechas tipo 1066.9.15
    pattern = r"\b(\d{3,4})\.(\d{1,2})\.(\d{1,2})\b"

    def repl(match):
        year = int(match.group(1)) + offset
        month = match.group(2)
        day = match.group(3)
        return f"{year}.{month}.{day}"

    return re.sub(pattern, repl, text)
