import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import json

from core.validation import compare_file_contents
from utils.profile_ops import update_profile, get_profile


FILES_JSON = "data/files.json"


class ValidationFileTab:
    def __init__(self, parent, app):
        self.app = app
        self.frame = ttk.Frame(parent)

        self.diff_lines = None
        self.build_ui()

    # ---------------------------------------------------------
    # UI
    # ---------------------------------------------------------
    def build_ui(self):
        frame = self.frame

        tk.Label(frame, text="Archivo a validar:").pack(pady=5)

        self.combo_files = ttk.Combobox(frame, values=[], state="readonly", width=80)
        self.combo_files.pack(pady=5)

        btn_frame = tk.Frame(frame)
        btn_frame.pack(pady=5)

        tk.Button(btn_frame, text="Añadir archivo…", command=self.add_new_file).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Activar archivo", command=self.activate_file).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Desactivar archivo", command=self.deactivate_file).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Excepción de ruta…", command=self.set_path_exception).pack(side="left", padx=5)

        mode_frame = tk.Frame(frame)
        mode_frame.pack(pady=10)

        tk.Label(mode_frame, text="Validar contra:").pack(side="left", padx=5)

        self.validation_mode = tk.StringVar(value="game")

        tk.Radiobutton(mode_frame, text="Juego", variable=self.validation_mode, value="game").pack(side="left", padx=5)
        tk.Radiobutton(mode_frame, text="Mod", variable=self.validation_mode, value="mod").pack(side="left", padx=5)

        tk.Button(frame, text="Validar archivo", command=self.validate_file).pack(pady=10)

        self.label_result = tk.Label(frame, text="", font=("Arial", 11))
        self.label_result.pack(pady=10)

        tk.Button(frame, text="Ver diff", command=self.show_diff).pack(pady=5)

    # ---------------------------------------------------------
    def refresh(self):
        profile = self.app.current_profile
        if not profile:
            return

        game_key = profile["game"]
        game_files = self.app.files.get(game_key, {})

        self.combo_files["values"] = list(game_files.keys())

        if profile["files"]:
            self.combo_files.set(profile["files"][0])
        else:
            self.combo_files.set("")

        self.label_result.config(text="")
        self.diff_lines = None

    # ---------------------------------------------------------
    def add_new_file(self):
        profile = self.app.current_profile
        if not profile:
            messagebox.showerror("Error", "Selecciona un perfil")
            return

        game_root = profile["game_root"]

        path = filedialog.askopenfilename(initialdir=game_root)
        if not path:
            return

        rel = os.path.relpath(path, game_root).replace("\\", "/")

        with open(FILES_JSON, "r", encoding="utf-8") as f:
            files_data = json.load(f)

        game_key = profile["game"]

        if game_key not in files_data:
            files_data[game_key] = {}

        name = os.path.splitext(os.path.basename(rel))[0]

        base_name = name
        i = 1
        while name in files_data[game_key]:
            name = f"{base_name}_{i}"
            i += 1

        files_data[game_key][name] = {"path": rel}

        with open(FILES_JSON, "w", encoding="utf-8") as f:
            json.dump(files_data, f, indent=4)

        self.app.files = files_data

        profile["files"].append(name)
        update_profile(profile)
        self.app.current_profile = get_profile(profile["name"])

        self.refresh()

    # ---------------------------------------------------------
    def activate_file(self):
        profile = self.app.current_profile
        if not profile:
            return

        sel = self.combo_files.get()
        if not sel:
            return

        if sel not in profile["files"]:
            profile["files"].append(sel)
            update_profile(profile)
            self.app.current_profile = get_profile(profile["name"])

        self.refresh()

    # ---------------------------------------------------------
    def deactivate_file(self):
        profile = self.app.current_profile
        if not profile:
            return

        sel = self.combo_files.get()
        if not sel:
            return

        if sel in profile["files"]:
            profile["files"].remove(sel)
            update_profile(profile)
            self.app.current_profile = get_profile(profile["name"])

        self.refresh()

    # ---------------------------------------------------------
    # Excepción de ruta (ruta alternativa en el MOD)
    # ---------------------------------------------------------
    def set_path_exception(self):
        profile = self.app.current_profile
        if not profile:
            return

        sel = self.combo_files.get()
        if not sel:
            return

        game_key = profile["game"]
        game_files = self.app.files.get(game_key, {})

        current = game_files[sel].get("map_to", "")

        win = tk.Toplevel(self.frame)
        win.title("Excepción de ruta (MOD)")

        tk.Label(win, text="Ruta alternativa en el MOD:").pack(pady=5)

        entry = tk.Entry(win, width=80)
        entry.pack(pady=5)
        entry.insert(0, current)

        def save():
            new_path = entry.get().strip()

            with open(FILES_JSON, "r", encoding="utf-8") as f:
                files_data = json.load(f)

            if new_path:
                files_data[game_key][sel]["map_to"] = new_path
            else:
                files_data[game_key][sel].pop("map_to", None)

            with open(FILES_JSON, "w", encoding="utf-8") as f:
                json.dump(files_data, f, indent=4)

            self.app.files = files_data
            win.destroy()

        tk.Button(win, text="Guardar", command=save).pack(pady=10)

    # ---------------------------------------------------------
    # Validar archivo
    # ---------------------------------------------------------
    def validate_file(self):
        profile = self.app.current_profile
        if not profile:
            return

        sel = self.combo_files.get()
        if not sel:
            return

        game_key = profile["game"]
        game_files = self.app.files.get(game_key, {})

        data = game_files[sel]
        rel_game = data["path"]                 # ruta en juego/backup
        rel_mod = data.get("map_to", rel_game)  # ruta en mod (alternativa si existe)

        game_path = os.path.join(profile["game_root"], rel_game)
        backup_path = os.path.join(profile["backup_root"], rel_game)
        mod_path = os.path.join(profile["mod_root"], rel_mod)

        mode = self.validation_mode.get()

        if mode == "game":
            left_path = game_path
            left_label = "JUEGO"
        else:
            left_path = mod_path
            left_label = "MOD"

        # Para el mensaje usamos siempre la ruta lógica del juego
        rel_display = rel_game if mode == "game" else rel_mod

        if not os.path.isfile(left_path):
            self.label_result.config(text=f"[+] SOLO EN {left_label} — {rel_display}", fg="blue")
            self.diff_lines = None
            return

        if not os.path.isfile(backup_path):
            self.label_result.config(text=f"[-] SOLO EN BACKUP — {rel_game}", fg="purple")
            self.diff_lines = None
            return

        same, diff = compare_file_contents(left_path, backup_path)

        if same:
            self.label_result.config(text=f"[=] IGUAL — {rel_display}", fg="green")
            self.diff_lines = None
        else:
            self.label_result.config(text=f"[!] CAMBIADO — {rel_display}", fg="red")
            self.diff_lines = diff

    # ---------------------------------------------------------
    # Mostrar diff
    # ---------------------------------------------------------
    def show_diff(self):
        if not self.diff_lines:
            messagebox.showinfo("Info", "No hay diff disponible")
            return

        win = tk.Toplevel(self.frame)
        win.title("Diff del archivo")

        text = tk.Text(win, width=120, height=40)
        text.pack(fill="both", expand=True)

        for line in self.diff_lines:
            if line.startswith("+") and not line.startswith("+++"):
                text.insert(tk.END, line, "added")
            elif line.startswith("-") and not line.startswith("---"):
                text.insert(tk.END, line, "removed")
            else:
                text.insert(tk.END, line)
            text.insert(tk.END, "\n")

        text.tag_config("added", foreground="green")
        text.tag_config("removed", foreground="red")

        text.config(state="disabled")
