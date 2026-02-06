import tkinter as tk
from tkinter import ttk, messagebox
import os

from core.validation import compare_file_contents


class ValidationFileFullTab:
    def __init__(self, parent, app):
        self.app = app
        self.frame = ttk.Frame(parent)

        # (file_key, estado_mod, diff_mod, estado_game, diff_game)
        self.results = []
        self.build_ui()

    # ---------------------------------------------------------
    # UI
    # ---------------------------------------------------------
    def build_ui(self):
        frame = self.frame

        tk.Label(frame, text="Validación total de archivos").pack(pady=5)

        tk.Button(frame, text="Validar todos los archivos", command=self.run_validation).pack(pady=5)

        # Tabla con 3 columnas: archivo, mod, juego
        self.tree = ttk.Treeview(
            frame,
            columns=("archivo", "mod", "game"),
            show="headings",
            height=20
        )

        self.tree.heading("archivo", text="Archivo")
        self.tree.heading("mod", text="MOD ↔ Backup")
        self.tree.heading("game", text="Juego ↔ Backup")

        self.tree.column("archivo", width=260, anchor="w")
        self.tree.column("mod", width=160, anchor="center")
        self.tree.column("game", width=160, anchor="center")

        self.tree.pack(fill="both", expand=True, pady=10)

        tk.Button(frame, text="Ver diff del archivo seleccionado", command=self.show_diff).pack(pady=5)

    # ---------------------------------------------------------
    # REFRESH
    # ---------------------------------------------------------
    def refresh(self):
        pass

    # ---------------------------------------------------------
    # Validación total
    # ---------------------------------------------------------
    def run_validation(self):
        profile = self.app.current_profile
        if not profile:
            return

        game_key = profile["game"]
        game_files = self.app.files.get(game_key, {})

        active_files = profile["files"]

        self.results = []
        self.tree.delete(*self.tree.get_children())

        for file_key in active_files:
            if file_key not in game_files:
                continue

            rel = game_files[file_key]["path"]

            game_path = os.path.join(profile["game_root"], rel)
            mod_path = os.path.join(profile["mod_root"], rel)
            backup_path = os.path.join(profile["backup_root"], rel)

            # -------------------------
            # MOD ↔ BACKUP
            # -------------------------
            if not os.path.isfile(mod_path):
                estado_mod = "[+] Solo en JUEGO"
                diff_mod = None
            elif not os.path.isfile(backup_path):
                estado_mod = "[-] Solo en BACKUP"
                diff_mod = None
            else:
                same, diff_mod = compare_file_contents(mod_path, backup_path)
                estado_mod = "[=] Igual" if same else "[!] Cambiado"

            # -------------------------
            # JUEGO ↔ BACKUP
            # -------------------------
            if not os.path.isfile(game_path):
                estado_game = "[+] Solo en MOD"
                diff_game = None
            elif not os.path.isfile(backup_path):
                estado_game = "[-] Solo en BACKUP"
                diff_game = None
            else:
                same, diff_game = compare_file_contents(game_path, backup_path)
                estado_game = "[=] Igual" if same else "[!] Cambiado"

            # Guardar resultado
            self.results.append((file_key, estado_mod, diff_mod, estado_game, diff_game))

            # Añadir a tabla: primera columna = nombre del archivo
            self.tree.insert(
                "",
                "end",
                iid=file_key,
                values=(file_key, estado_mod, estado_game)
            )

    # ---------------------------------------------------------
    # Mostrar diff
    # ---------------------------------------------------------
    def show_diff(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Info", "Selecciona un archivo")
            return

        file_key = sel[0]

        for name, estado_mod, diff_mod, estado_game, diff_game in self.results:
            if name == file_key:

                win = tk.Toplevel(self.frame)
                win.title(f"Diff — {file_key}")

                tk.Label(win, text="Selecciona comparación:").pack(pady=5)

                def open_diff(diff, title):
                    if not diff:
                        messagebox.showinfo("Info", "No hay diff disponible")
                        return

                    dwin = tk.Toplevel(win)
                    dwin.title(title)

                    text = tk.Text(dwin, width=120, height=40)
                    text.pack(fill="both", expand=True)

                    for line in diff:
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

                tk.Button(
                    win,
                    text="MOD ↔ Backup",
                    command=lambda: open_diff(diff_mod, f"MOD ↔ Backup — {file_key}")
                ).pack(pady=5)

                tk.Button(
                    win,
                    text="Juego ↔ Backup",
                    command=lambda: open_diff(diff_game, f"Juego ↔ Backup — {file_key}")
                ).pack(pady=5)

                return
