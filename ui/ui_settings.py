import tkinter as tk
from tkinter import ttk
import json
import os

SETTINGS_FILE = "data/settings.json"


def load_settings():
    if not os.path.isfile(SETTINGS_FILE):
        return {"theme": "light"}

    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"theme": "light"}


def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4)


class SettingsTab:
    def __init__(self, parent, app):
        self.app = app
        self.frame = ttk.Frame(parent)

        self.settings = load_settings()

        self.build_ui()

    def build_ui(self):
        frame = self.frame

        tk.Label(frame, text="Personalización de la interfaz").pack(pady=10)

        tk.Label(frame, text="Tema visual:").pack()

        self.theme_var = tk.StringVar(value=self.settings.get("theme", "light"))

        ttk.Radiobutton(frame, text="Claro", variable=self.theme_var, value="light").pack(anchor="w", padx=20)
        ttk.Radiobutton(frame, text="Oscuro elegante", variable=self.theme_var, value="dark").pack(anchor="w", padx=20)

        tk.Button(frame, text="Aplicar tema", command=self.apply_theme).pack(pady=10)

    def apply_theme(self):
        theme = self.theme_var.get()

        self.settings["theme"] = theme
        save_settings(self.settings)

        self.app.apply_theme(theme)
