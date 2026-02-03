import json
import os

PROFILES_PATH = "data/profiles.json"


def load_profiles():
    if not os.path.isfile(PROFILES_PATH):
        return []

    try:
        with open(PROFILES_PATH, "r", encoding="utf-8") as f:
            profiles = json.load(f)
    except json.JSONDecodeError:
        return []

    for p in profiles:
        if "modules" not in p:
            p["modules"] = []
        if "files" not in p:
            p["files"] = []

    return profiles


def save_profiles(profiles):
    os.makedirs("data", exist_ok=True)
    with open(PROFILES_PATH, "w", encoding="utf-8") as f:
        json.dump(profiles, f, indent=4)


def list_profiles():
    return [p["name"] for p in load_profiles()]


def get_profile(name):
    profiles = load_profiles()
    for p in profiles:
        if p["name"] == name:
            if "modules" not in p:
                p["modules"] = []
            if "files" not in p:
                p["files"] = []
            return p
    return None


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


def add_profile(profile):
    profiles = load_profiles()

    if any(p["name"] == profile["name"] for p in profiles):
        return False

    if "modules" not in profile:
        profile["modules"] = []
    if "files" not in profile:
        profile["files"] = []

    profiles.append(profile)
    save_profiles(profiles)
    return True


def delete_profile(name):
    profiles = load_profiles()
    profiles = [p for p in profiles if p["name"] != name]
    save_profiles(profiles)
