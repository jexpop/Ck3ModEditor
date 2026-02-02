import os


# ---------------------------------------------------------
# Normalizar rutas
# ---------------------------------------------------------
def normalize(path):
    """
    Normaliza una ruta para evitar problemas entre Windows/Linux.
    """
    if not path:
        return ""
    return os.path.normpath(path)


# ---------------------------------------------------------
# Construir ruta dentro del juego
# ---------------------------------------------------------
def game_path(profile, *parts):
    """
    Devuelve una ruta dentro del directorio del juego del perfil.
    """
    root = normalize(profile.get("game_root", ""))
    return normalize(os.path.join(root, *parts))


# ---------------------------------------------------------
# Construir ruta dentro del mod
# ---------------------------------------------------------
def mod_path(profile, *parts):
    """
    Devuelve una ruta dentro del directorio del mod del perfil.
    """
    root = normalize(profile.get("mod_root", ""))
    return normalize(os.path.join(root, *parts))


# ---------------------------------------------------------
# Construir ruta dentro del backup
# ---------------------------------------------------------
def backup_path(profile, *parts):
    """
    Devuelve una ruta dentro del directorio de backups del perfil.
    """
    root = normalize(profile.get("backup_root", ""))
    return normalize(os.path.join(root, *parts))


# ---------------------------------------------------------
# Comprobar si una ruta existe
# ---------------------------------------------------------
def exists(path):
    return os.path.exists(normalize(path))


# ---------------------------------------------------------
# Resolver ruta relativa dentro de un módulo
# ---------------------------------------------------------
def resolve_relative(base, rel):
    """
    Devuelve una ruta absoluta a partir de una base y una ruta relativa.
    """
    return normalize(os.path.join(base, rel))
