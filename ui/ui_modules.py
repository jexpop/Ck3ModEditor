import tkinter as tk
from tkinter import ttk, messagebox
import json
import os


class ModulesTab:
    def __init__(self, parent, app):
        self.app = app
        self.frame = ttk.Frame(parent)

        self.build_ui()

    # ---------------------------------------------------------
    # UI
    # ---------------------------------------------------------
    def build_ui(self):
        frame = self.frame

        tk.Label(frame, text="Juego del perfil actual:").pack()
        self.label_game = tk.Label(frame, text="")
        self.label_game.pack()

        # Lista de módulos
        self.listbox = tk.Listbox(frame, width=50, height=15)
        self.listbox.pack()
        self.listbox.bind("<<ListboxSelect>>", self.on_module_selected)

        # Campos de edición
        tk.Label(frame, text="Nombre del módulo:").pack()
        self.entry_name = tk.Entry(frame, width=40)
        self.entry_name.pack()

        tk.Label(frame, text="Ruta relativa:").pack()
        self.entry_path = tk.Entry(frame, width=40)
        self.entry_path.pack()

        tk.Label(frame, text="Extensiones ignoradas (coma):").pack()
        self.entry_ignore = tk.Entry(frame, width=40)
        self.entry_ignore.pack()

        # Botones
        tk.Button(frame, text="Añadir módulo", command=self.add_module).pack(pady=5)
        tk.Button(frame, text="Guardar cambios", command=self.save_module).pack(pady=5)
        tk.Button(frame, text="Eliminar módulo", command=self.delete_module).pack(pady=5)

    # ---------------------------------------------------------
    # REFRESH
    # ---------------------------------------------------------
    def refresh(self):
        profile = self.app.current_profile
        if not profile:
            return

        game_key = profile["game"]
        self.label_game.config(text=game_key)

        self.load_modules()

    # ---------------------------------------------------------
    # Cargar módulos en la lista
    # ---------------------------------------------------------
    def load_modules(self):
        self.listbox.delete(0, tk.END)

        profile = self.app.current_profile
        if not profile:
            return

        game_key = profile["game"]
        game_modules = self.app.modules.get(game_key, {})

        for name in game_modules.keys():
            self.listbox.insert(tk.END, name)

    # ---------------------------------------------------------
    # Selección de módulo
    # ---------------------------------------------------------
    def on_module_selected(self, event=None):
        sel = self.listbox.curselection()
        if not sel:
            return

        name = self.listbox.get(sel[0])
        profile = self.app.current_profile
        game_key = profile["game"]

        if name not in self.app.modules.get(game_key, {}):
            return

        cfg = self.app.modules[game_key][name]

        self.entry_name.delete(0, tk.END)
        self.entry_name.insert(0, name)

        self.entry_path.delete(0, tk.END)
        self.entry_path.insert(0, cfg.get("path", ""))

        ignore = ", ".join(cfg.get("ignore_ext", []))
        self.entry_ignore.delete(0, tk.END)
        self.entry_ignore.insert(0, ignore)

    # ---------------------------------------------------------
    # Añadir módulo
    # ---------------------------------------------------------
    def add_module(self):
        profile = self.app.current_profile
        if not profile:
            messagebox.showerror("Error", "No hay perfil seleccionado")
            return

        name = self.entry_name.get().strip()
        path = self.entry_path.get().strip()
        ignore = [ext.strip() for ext in self.entry_ignore.get().split(",") if ext.strip()]

        if not name or not path:
            messagebox.showerror("Error", "Nombre y ruta son obligatorios")
            return

        game_key = profile["game"]

        if game_key not in self.app.modules:
            self.app.modules[game_key] = {}

        self.app.modules[game_key][name] = {
            "path": path,
            "ignore_ext": ignore
        }

        self.save_modules_file()
        self.load_modules()

    # ---------------------------------------------------------
    # Guardar módulo
    # ---------------------------------------------------------
    def save_module(self):
        profile = self.app.current_profile
        if not profile:
            messagebox.showerror("Error", "No hay perfil seleccionado")
            return

        name = self.entry_name.get().strip()
        path = self.entry_path.get().strip()
        ignore = [ext.strip() for ext in self.entry_ignore.get().split(",") if ext.strip()]

        game_key = profile["game"]

        if name not in self.app.modules.get(game_key, {}):
            messagebox.showerror("Error", "El módulo no existe")
            return

        self.app.modules[game_key][name]["path"] = path
        self.app.modules[game_key][name]["ignore_ext"] = ignore

        self.save_modules_file()
        self.load_modules()

    # ---------------------------------------------------------
    # Eliminar módulo
    # ---------------------------------------------------------
    def delete_module(self):
        profile = self.app.current_profile
        if not profile:
            messagebox.showerror("Error", "No hay perfil seleccionado")
            return

        sel = self.listbox.curselection()
        if not sel:
            return

        name = self.listbox.get(sel[0])
        game_key = profile["game"]

        if name in self.app.modules.get(game_key, {}):
            del self.app.modules[game_key][name]

        self.save_modules_file()
        self.load_modules()

    # ---------------------------------------------------------
    # Guardar modules.json
    # ---------------------------------------------------------
    def save_modules_file(self):
        with open("data/modules.json", "w", encoding="utf-8") as f:
            json.dump(self.app.modules, f, indent=4)
