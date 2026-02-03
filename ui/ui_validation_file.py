import tkinter as tk
from tkinter import ttk, messagebox
import os

from core.validation import compare_file_contents
from utils.profile_ops import update_profile, get_profile


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

        tk.Label(frame, text="Archivo a validar (Juego ↔ Backup):").pack(pady=5)

        # Combo con archivos definidos en files.json
        self.combo_files = ttk.Combobox(frame, values=[], state="readonly", width=80)
        self.combo_files.pack(pady=5)

        # Activar/desactivar archivo en el perfil
        btn_frame = tk.Frame(frame)
        btn_frame.pack(pady=5)

        tk.Button(btn_frame, text="Activar archivo", command=self.activate_file).pack(side="left", padx=5)
        tk.Button(btn_frame, text="Desactivar archivo", command=self.deactivate_file).pack(side="left", padx=5)

        tk.Button(frame, text="Validar archivo", command=self.validate_file).pack(pady=10)

        self.label_result = tk.Label(frame, text="", font=("Arial", 11))
        self.label_result.pack(pady=10)

        tk.Button(frame, text="Ver diff", command=self.show_diff).pack(pady=5)

    # ---------------------------------------------------------
    # REFRESH
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
    # Activar archivo
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
    # Desactivar archivo
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

        rel = game_files[sel]["path"]

        game_path = os.path.join(profile["game_root"], rel)
        backup_path = os.path.join(profile["backup_root"], rel)

        if not os.path.isfile(game_path):
            self.label_result.config(text=f"ERROR: No existe en el juego — {rel}", fg="red")
            return

        if not os.path.isfile(backup_path):
            self.label_result.config(text=f"[+] SOLO EN JUEGO — {rel}", fg="blue")
            self.diff_lines = None
            return

        same, diff = compare_file_contents(game_path, backup_path)

        if same:
            self.label_result.config(text=f"[=] IGUAL — {rel}", fg="green")
            self.diff_lines = None
        else:
            self.label_result.config(text=f"[!] CAMBIADO — {rel}", fg="red")
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
