import tkinter as tk
from tkinter import ttk, messagebox

from core.validation import (
    collect_module_files,
    compare_file_contents
)


class ValidationModuleTab:
    def __init__(self, parent, app):
        self.app = app
        self.frame = ttk.Frame(parent)

        self.validation_diffs = {}

        self.build_ui()

    # ---------------------------------------------------------
    # UI
    # ---------------------------------------------------------
    def build_ui(self):
        frame = self.frame

        tk.Label(frame, text="Módulo a validar (Juego vs Backup):").pack()
        self.combo_modules = ttk.Combobox(frame, values=[], state="readonly")
        self.combo_modules.pack()

        tk.Button(frame, text="Comparar ficheros", command=self.run_validation).pack(pady=10)

        self.listbox_results = tk.Listbox(frame, width=80, height=20)
        self.listbox_results.pack()

        tk.Button(frame, text="Ver diferencias", command=self.show_selected_diff).pack(pady=10)

    # ---------------------------------------------------------
    # REFRESH
    # ---------------------------------------------------------
    def refresh(self):
        profile = self.app.current_profile
        if not profile:
            self.combo_modules["values"] = []
            return

        game_key = profile["game"]
        game_modules = self.app.modules.get(game_key, {})

        self.combo_modules["values"] = list(game_modules.keys())
        if game_modules:
            self.combo_modules.current(0)

        self.listbox_results.delete(0, tk.END)
        self.validation_diffs.clear()

    # ---------------------------------------------------------
    # VALIDACIÓN POR MÓDULO
    # ---------------------------------------------------------
    def run_validation(self):
        self.listbox_results.delete(0, tk.END)
        self.validation_diffs.clear()

        profile = self.app.current_profile
        if not profile:
            messagebox.showerror("Error", "Selecciona un perfil")
            return

        module_name = self.combo_modules.get()
        if not module_name:
            messagebox.showerror("Error", "Selecciona un módulo")
            return

        game_key = profile["game"]
        game_modules = self.app.modules.get(game_key, {})

        if module_name not in game_modules:
            messagebox.showerror("Error", "Módulo no encontrado")
            return

        # Obtener rutas
        rel_path = game_modules[module_name]["path"]
        game_root = profile["game_root"]
        backup_root = profile["backup_root"]

        if not game_root or not backup_root:
            messagebox.showerror("Error", "Configura rutas de juego y backup en el perfil")
            return

        # Recolectar archivos
        game_files, backup_files = collect_module_files(game_root, backup_root, rel_path)

        all_keys = sorted(set(game_files.keys()) | set(backup_files.keys()))

        for rel in all_keys:
            g = game_files.get(rel)
            b = backup_files.get(rel)

            if g and b:
                same, diff_lines = compare_file_contents(g, b)
                if same:
                    display = f"[=] {rel} — IGUAL"
                else:
                    display = f"[!] {rel} — CAMBIADO"
                    self.validation_diffs[rel] = diff_lines
            elif g and not b:
                display = f"[+] {rel} — SOLO EN JUEGO"
            else:
                display = f"[-] {rel} — SOLO EN BACKUP"

            self.listbox_results.insert(tk.END, display)

    # ---------------------------------------------------------
    # MOSTRAR DIFF
    # ---------------------------------------------------------
    def show_selected_diff(self):
        sel = self.listbox_results.curselection()
        if not sel:
            return

        line = self.listbox_results.get(sel[0])
        if "CAMBIADO" not in line:
            messagebox.showinfo("Info", "Solo hay diff para archivos marcados como CAMBIADO")
            return

        rel = line.split(" ", 1)[1].split(" — ")[0].strip()

        if rel not in self.validation_diffs:
            messagebox.showerror("Error", "No se encontró diff para este archivo")
            return

        diff_lines = self.validation_diffs[rel]
        self.show_diff_window(rel, diff_lines)

    # ---------------------------------------------------------
    # VENTANA DE DIFF
    # ---------------------------------------------------------
    def show_diff_window(self, rel, diff_lines):
        win = tk.Toplevel(self.frame)
        win.title(f"Diferencias: {rel}")

        text = tk.Text(win, width=120, height=40)
        text.pack(fill="both", expand=True)

        for line in diff_lines:
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
