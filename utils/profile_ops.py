import json
import os


PROFILES_PATH = "data/profiles.json"


# ---------------------------------------------------------
# Cargar perfiles
# ---------------------------------------------------------
def load_profiles():
    if not os.path.isfile(PROFILES_PATH):
        return []

    try:
        with open(PROFILES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []


# ---------------------------------------------------------
# Guardar perfiles
# ---------------------------------------------------------
def save_profiles(profiles):
    os.makedirs("data", exist_ok=True)
    with open(PROFILES_PATH, "w", encoding="utf-8") as f:
        json.dump(profiles, f, indent=4)


# ---------------------------------------------------------
# Listar nombres de perfiles
# ---------------------------------------------------------
def list_profiles():
    profiles = load_profiles()
    return [p["name"] for p in profiles]


# ---------------------------------------------------------
# Obtener un perfil por nombre
# ---------------------------------------------------------
def get_profile(name):
    profiles = load_profiles()
    for p in profiles:
        if p["name"] == name:
            return p
    return None


# ---------------------------------------------------------
# Actualizar un perfil existente
# ---------------------------------------------------------
def update_profile(profile):
    profiles = load_profiles()
    updated = False

    for i, p in enumerate(profiles):
        if p["name"] == profile["name"]:
            profiles[i] = profile
            updated = True
            break

    if not updated:
        profiles.append(profile)

    save_profiles(profiles)


# ---------------------------------------------------------
# Añadir un perfil nuevo
# ---------------------------------------------------------
def add_profile(profile):
    profiles = load_profiles()

    # Evitar duplicados
    if any(p["name"] == profile["name"] for p in profiles):
        return False

    profiles.append(profile)
    save_profiles(profiles)
    return True


# ---------------------------------------------------------
# Eliminar un perfil
# ---------------------------------------------------------
def delete_profile(name):
    profiles = load_profiles()
    profiles = [p for p in profiles if p["name"] != name]
    save_profiles(profiles)
