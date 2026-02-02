import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from utils.profile_ops import (
    list_profiles,
    get_profile,
    update_profile,
    add_profile,
    delete_profile
)


class ProfileTab:
    def __init__(self, parent, app):
        self.app = app
        self.frame = ttk.Frame(parent)

        self.profile_vars = {}
        self.profile_module_vars = {}

        self.build_ui()

    # ---------------------------------------------------------
    # UI
    # ---------------------------------------------------------
    def build_ui(self):
        frame = self.frame

        # Selector de perfil
        tk.Label(frame, text="Seleccionar perfil:").pack()
        self.profile_combo = ttk.Combobox(
            frame, values=list_profiles(), state="readonly"
        )
        self.profile_combo.pack()
        self.profile_combo.bind("<<ComboboxSelected>>", self.on_profile_selected)

        # Entradas de rutas
        self.entry_game_root = self._add_path_selector(frame, "Raíz del juego")
        self.entry_mod_root = self._add_path_selector(frame, "Raíz del mod")
        self.entry_backup_root = self._add_path_selector(frame, "Carpeta de backups")

        # Botones de gestión de perfiles
        tk.Button(frame, text="Guardar perfil", command=self.save_profile).pack(pady=5)
        tk.Button(frame, text="Crear perfil nuevo", command=self.create_profile).pack(pady=5)
        tk.Button(frame, text="Renombrar perfil", command=self.rename_profile).pack(pady=5)
        tk.Button(frame, text="Eliminar perfil", command=self.delete_profile_action).pack(pady=5)

        # Módulos por defecto
        tk.Label(frame, text="Módulos activados por defecto:").pack(pady=10)
        self.profile_modules_frame = tk.Frame(frame)
        self.profile_modules_frame.pack()

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------
    def _add_path_selector(self, parent, label):
        tk.Label(parent, text=label).pack()
        entry = tk.Entry(parent, width=60)
        entry.pack()
        tk.Button(parent, text="Seleccionar", command=lambda e=entry: self._select_folder(e)).pack()
        return entry

    def _select_folder(self, entry):
        path = filedialog.askdirectory()
        if path:
            entry.delete(0, tk.END)
            entry.insert(0, path)

    # ---------------------------------------------------------
    # Eventos
    # ---------------------------------------------------------
    def on_profile_selected(self, event=None):
        name = self.profile_combo.get()
        profile = get_profile(name)

        if not profile:
            return

        self.app.on_profile_selected(profile)

    # ---------------------------------------------------------
    # Refrescar UI cuando cambia el perfil
    # ---------------------------------------------------------
    def refresh(self):
        profile = self.app.current_profile
        if not profile:
            return

        # Rellenar rutas
        self.entry_game_root.delete(0, tk.END)
        self.entry_game_root.insert(0, profile["game_root"])

        self.entry_mod_root.delete(0, tk.END)
        self.entry_mod_root.insert(0, profile["mod_root"])

        self.entry_backup_root.delete(0, tk.END)
        self.entry_backup_root.insert(0, profile["backup_root"])

        # Cargar módulos por defecto
        self.load_profile_modules()

    def load_profile_modules(self):
        for w in self.profile_modules_frame.winfo_children():
            w.destroy()

        profile = self.app.current_profile
        if not profile:
            return

        game_key = profile["game"]
        game_modules = self.app.modules.get(game_key, {})

        self.profile_module_vars = {}

        for module_name in game_modules.keys():
            var = tk.IntVar(value=1 if module_name in profile["modules"] else 0)
            chk = tk.Checkbutton(self.profile_modules_frame, text=module_name, variable=var)
            chk.pack(anchor="w")
            self.profile_module_vars[module_name] = var

    # ---------------------------------------------------------
    # Guardar perfil
    # ---------------------------------------------------------
    def save_profile(self):
        profile = self.app.current_profile
        if not profile:
            messagebox.showerror("Error", "No hay perfil seleccionado")
            return

        profile["game_root"] = self.entry_game_root.get()
        profile["mod_root"] = self.entry_mod_root.get()
        profile["backup_root"] = self.entry_backup_root.get()

        # Guardar módulos por defecto
        selected_modules = [
            name for name, var in self.profile_module_vars.items() if var.get() == 1
        ]
        profile["modules"] = selected_modules

        update_profile(profile)
        messagebox.showinfo("OK", "Perfil guardado")

    # ---------------------------------------------------------
    # Crear perfil
    # ---------------------------------------------------------
    def create_profile(self):
        new_profile = {
            "name": "Nuevo Perfil",
            "game": "CK3",
            "game_root": "",
            "mod_root": "",
            "backup_root": "",
            "year_offset": 10000,
            "modules": []
        }
        add_profile(new_profile)

        self.profile_combo["values"] = list_profiles()
        self.profile_combo.set("Nuevo Perfil")

        self.app.on_profile_selected(new_profile)

    # ---------------------------------------------------------
    # Renombrar perfil
    # ---------------------------------------------------------
    def rename_profile(self):
        profile = self.app.current_profile
        if not profile:
            messagebox.showerror("Error", "No hay perfil seleccionado")
            return

        win = tk.Toplevel(self.frame)
        win.title("Renombrar perfil")

        tk.Label(win, text="Nuevo nombre:").pack()
        entry = tk.Entry(win)
        entry.insert(0, profile["name"])
        entry.pack()

        def do_rename():
            new_name = entry.get().strip()
            if not new_name:
                messagebox.showerror("Error", "Nombre vacío")
                return

            # Actualizar
            old_name = profile["name"]
            profile["name"] = new_name
            update_profile(profile)

            # Refrescar combo
            self.profile_combo["values"] = list_profiles()
            self.profile_combo.set(new_name)

            win.destroy()

        tk.Button(win, text="Aceptar", command=do_rename).pack(pady=5)

    # ---------------------------------------------------------
    # Eliminar perfil
    # ---------------------------------------------------------
    def delete_profile_action(self):
        profile = self.app.current_profile
        if not profile:
            messagebox.showerror("Error", "No hay perfil seleccionado")
            return

        name = profile["name"]

        if not messagebox.askyesno("Confirmar", f"¿Eliminar el perfil '{name}'?"):
            return

        delete_profile(name)

        # Reset UI
        self.app.current_profile = None
        self.profile_combo["values"] = list_profiles()
        self.profile_combo.set("")

        self.entry_game_root.delete(0, tk.END)
        self.entry_mod_root.delete(0, tk.END)
        self.entry_backup_root.delete(0, tk.END)

        for w in self.profile_modules_frame.winfo_children():
            w.destroy()
