import tkinter as tk
from tkinter import ttk, messagebox
import os
import json

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

        tk.Label(frame, text="Módulo a validar:").pack()

        self.combo_modules = ttk.Combobox(frame, values=[], state="readonly")
        self.combo_modules.pack()

        tk.Label(frame, text="Comparación:").pack(pady=5)

        self.combo_compare = ttk.Combobox(
            frame,
            values=[
                "Juego ↔ Mod",
                "Mod ↔ Backup",
                "Juego ↔ Backup"
            ],
            state="readonly"
        )
        self.combo_compare.current(0)
        self.combo_compare.pack()

        tk.Button(frame, text="Comparar ficheros", command=self.run_validation).pack(pady=10)

        # Treeview con colores
        self.tree = ttk.Treeview(
            frame,
            columns=("estado", "file", "diff"),
            show="headings",
            height=20
        )

        self.tree.heading("estado", text="Estado")
        self.tree.heading("file", text="Archivo")
        self.tree.heading("diff", text="diff")

        self.tree.column("estado", width=120)
        self.tree.column("file", width=500)
        self.tree.column("diff", width=0, stretch=False)

        self.tree.pack(fill="both", expand=True)

        # Colores
        self.tree.tag_configure("modificado", foreground="#d17b00")
        self.tree.tag_configure("añadido", foreground="green")
        self.tree.tag_configure("eliminado", foreground="red")

        self.tree.bind("<Double-1>", self.open_diff_from_tree)

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

        self.tree.delete(*self.tree.get_children())
        self.validation_diffs.clear()

    # ---------------------------------------------------------
    # VALIDACIÓN POR MÓDULO
    # ---------------------------------------------------------
    def run_validation(self):
        self.tree.delete(*self.tree.get_children())
        self.validation_diffs.clear()

        profile = self.app.current_profile
        if not profile:
            messagebox.showerror("Error", "Selecciona un perfil")
            return

        module_name = self.combo_modules.get()
        if not module_name:
            messagebox.showerror("Error", "Selecciona un módulo")
            return

        comparison = self.combo_compare.get()

        game_key = profile["game"]
        game_modules = self.app.modules.get(game_key, {})

        if module_name not in game_modules:
            messagebox.showerror("Error", "Módulo no encontrado")
            return

        rel_path = game_modules[module_name]["path"]

        game_root = profile["game_root"]
        mod_root = profile["mod_root"]
        backup_root = profile["backup_root"]

        if not game_root or not mod_root or not backup_root:
            messagebox.showerror("Error", "Configura rutas de juego, mod y backup en el perfil")
            return

        # Recolectar archivos
        game_files, backup_files = collect_module_files(game_root, backup_root, rel_path)

        # Recolectar archivos del mod
        mod_files, _ = collect_module_files(mod_root, mod_root, rel_path)

        # Elegir comparación
        if comparison == "Juego ↔ Mod":
            left = game_files
            right = mod_files
        elif comparison == "Mod ↔ Backup":
            left = mod_files
            right = backup_files
        else:  # Juego ↔ Backup
            left = game_files
            right = backup_files

        all_keys = sorted(set(left.keys()) | set(right.keys()))

        for rel in all_keys:
            l = left.get(rel)
            r = right.get(rel)

            if l and r:
                same, diff_lines = compare_file_contents(l, r)
                if same:
                    continue  # ocultar iguales
                estado = "Modificado"
                self.validation_diffs[rel] = diff_lines
            elif l and not r:
                estado = "Eliminado"
                diff_lines = None
            else:
                estado = "Añadido"
                diff_lines = None

            tag = estado.lower()
            self.tree.insert("", "end", values=(estado, rel, json.dumps(diff_lines)), tags=(tag,))

    # ---------------------------------------------------------
    # MOSTRAR DIFF
    # ---------------------------------------------------------
    def open_diff_from_tree(self, event):
        sel = self.tree.selection()
        if not sel:
            return

        iid = sel[0]
        diff_raw = self.tree.set(iid, "diff")
        file_name = self.tree.set(iid, "file")

        if not diff_raw or diff_raw == "None":
            messagebox.showinfo("Info", "Este archivo no tiene diferencias")
            return

        try:
            diff = json.loads(diff_raw)
        except:
            diff = diff_raw.split("\n")

        win = tk.Toplevel(self.frame)
        win.title(f"Diferencias — {file_name}")

        text = tk.Text(win, width=120, height=40)
        text.pack(fill="both", expand=True)

        for line in diff:
            if line.startswith("+") and not line.startswith("+++"):
                text.insert("end", line + "\n", "added")
            elif line.startswith("-") and not line.startswith("---"):
                text.insert("end", line + "\n", "removed")
            else:
                text.insert("end", line + "\n")

        text.tag_config("added", foreground="green")
        text.tag_config("removed", foreground="red")
        text.config(state="disabled")
