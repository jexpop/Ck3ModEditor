import tkinter as tk
from tkinter import ttk, messagebox
import os
import json

from core.validation import compare_file_contents


def list_files_recursive(base_path):
    result = []
    if not os.path.isdir(base_path):
        return result

    for root, dirs, files in os.walk(base_path):
        for f in files:
            full = os.path.join(root, f)
            rel = os.path.relpath(full, base_path)
            result.append(rel.replace("\\", "/"))

    return result


class ValidationModuleFullTab:
    def __init__(self, parent, app):
        self.app = app
        self.frame = ttk.Frame(parent)

        self.results = []
        self.build_ui()

    # ---------------------------------------------------------
    # UI
    # ---------------------------------------------------------
    def build_ui(self):
        frame = self.frame

        tk.Label(frame, text="Validación total de módulos").pack(pady=5)

        tk.Button(frame, text="Validar todos los módulos", command=self.run_validation).pack(pady=5)

        self.tree = ttk.Treeview(
            frame,
            columns=("module", "mod", "game"),
            show="headings",
            height=20
        )

        self.tree.heading("module", text="Módulo")
        self.tree.heading("mod", text="MOD ↔ Backup")
        self.tree.heading("game", text="Juego ↔ Backup")

        self.tree.column("module", width=200, anchor="w")
        self.tree.column("mod", width=360, anchor="w")
        self.tree.column("game", width=360, anchor="w")

        self.tree.pack(fill="both", expand=True, pady=10)

        tk.Button(frame, text="Ver detalles del módulo seleccionado", command=self.show_details).pack(pady=5)

    # ---------------------------------------------------------
    def refresh(self):
        pass

    # ---------------------------------------------------------
    # Validación total de módulos
    # ---------------------------------------------------------
    def run_validation(self):
        profile = self.app.current_profile
        if not profile:
            return

        game_key = profile["game"]
        game_modules = self.app.modules.get(game_key, {})

        active_modules = profile["modules"]

        self.results = []
        self.tree.delete(*self.tree.get_children())

        for module_name in active_modules:
            if module_name not in game_modules:
                continue

            rel = game_modules[module_name]["path"]

            game_dir = os.path.join(profile["game_root"], rel)
            mod_dir = os.path.join(profile["mod_root"], rel)
            backup_dir = os.path.join(profile["backup_root"], rel)

            files_mod = list_files_recursive(mod_dir)
            files_game = list_files_recursive(game_dir)
            files_backup = list_files_recursive(backup_dir)

            all_files = sorted(set(files_mod + files_game + files_backup))

            detalles_mod = []
            detalles_game = []

            mod_equal = mod_changed = mod_only = backup_only_mod = 0
            game_equal = game_changed = game_only = backup_only_game = 0

            for f in all_files:
                mod_path = os.path.join(mod_dir, f)
                game_path = os.path.join(game_dir, f)
                backup_path = os.path.join(backup_dir, f)

                # -------------------------
                # MOD ↔ BACKUP
                # -------------------------
                if not os.path.isfile(mod_path):
                    if os.path.isfile(backup_path):
                        detalles_mod.append((f, "Eliminado", None))
                        backup_only_mod += 1
                elif not os.path.isfile(backup_path):
                    detalles_mod.append((f, "Añadido", None))
                    mod_only += 1
                else:
                    same, diff = compare_file_contents(mod_path, backup_path)
                    if same:
                        mod_equal += 1
                    else:
                        detalles_mod.append((f, "Modificado", diff))
                        mod_changed += 1

                # -------------------------
                # JUEGO ↔ BACKUP
                # -------------------------
                if not os.path.isfile(game_path):
                    if os.path.isfile(backup_path):
                        detalles_game.append((f, "Eliminado", None))
                        backup_only_game += 1
                elif not os.path.isfile(backup_path):
                    detalles_game.append((f, "Añadido", None))
                    game_only += 1
                else:
                    same, diff = compare_file_contents(game_path, backup_path)
                    if same:
                        game_equal += 1
                    else:
                        detalles_game.append((f, "Modificado", diff))
                        game_changed += 1

            total_mod = mod_equal + mod_changed + mod_only + backup_only_mod
            total_game = game_equal + game_changed + game_only + backup_only_game

            estado_mod = (
                f"{total_mod} archivos — "
                f"{mod_changed} modificados, "
                f"{mod_equal} iguales, "
                f"{mod_only} añadidos, "
                f"{backup_only_mod} eliminados"
            )

            estado_game = (
                f"{total_game} archivos — "
                f"{game_changed} modificados, "
                f"{game_equal} iguales, "
                f"{game_only} añadidos, "
                f"{backup_only_game} eliminados"
            )

            self.results.append((module_name, estado_mod, estado_game, detalles_mod, detalles_game))

            self.tree.insert("", "end", iid=module_name, values=(module_name, estado_mod, estado_game))

    # ---------------------------------------------------------
    # Mostrar detalles del módulo
    # ---------------------------------------------------------
    def show_details(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Info", "Selecciona un módulo")
            return

        module_name = sel[0]

        for name, estado_mod, estado_game, detalles_mod, detalles_game in self.results:
            if name == module_name:

                win = tk.Toplevel(self.frame)
                win.title(f"Detalles — {module_name}")

                nb = ttk.Notebook(win)
                nb.pack(fill="both", expand=True)

                # -------------------------
                # MOD
                # -------------------------
                frame_mod = ttk.Frame(nb)
                nb.add(frame_mod, text="MOD ↔ Backup")

                tree_mod = ttk.Treeview(frame_mod, columns=("estado", "file", "diff"), show="headings")
                tree_mod.heading("estado", text="Estado")
                tree_mod.heading("file", text="Archivo")
                tree_mod.heading("diff", text="diff")

                tree_mod.column("estado", width=120)
                tree_mod.column("file", width=500)
                tree_mod.column("diff", width=0, stretch=False)

                tree_mod.pack(fill="both", expand=True)

                tree_mod.tag_configure("modificado", foreground="#d17b00")
                tree_mod.tag_configure("añadido", foreground="green")
                tree_mod.tag_configure("eliminado", foreground="red")

                for f, estado, diff in detalles_mod:
                    if estado in ("Modificado", "Añadido", "Eliminado"):
                        tag = estado.lower()
                        tree_mod.insert("", "end", values=(estado, f, json.dumps(diff)), tags=(tag,))

                tree_mod.bind("<Double-1>", lambda e, t=tree_mod: self.open_diff_from_tree(t))

                # -------------------------
                # JUEGO
                # -------------------------
                frame_game = ttk.Frame(nb)
                nb.add(frame_game, text="Juego ↔ Backup")

                tree_game = ttk.Treeview(frame_game, columns=("estado", "file", "diff"), show="headings")
                tree_game.heading("estado", text="Estado")
                tree_game.heading("file", text="Archivo")
                tree_game.heading("diff", text="diff")

                tree_game.column("estado", width=120)
                tree_game.column("file", width=500)
                tree_game.column("diff", width=0, stretch=False)

                tree_game.pack(fill="both", expand=True)

                tree_game.tag_configure("modificado", foreground="#d17b00")
                tree_game.tag_configure("añadido", foreground="green")
                tree_game.tag_configure("eliminado", foreground="red")

                for f, estado, diff in detalles_game:
                    if estado in ("Modificado", "Añadido", "Eliminado"):
                        tag = estado.lower()
                        tree_game.insert("", "end", values=(estado, f, json.dumps(diff)), tags=(tag,))

                tree_game.bind("<Double-1>", lambda e, t=tree_game: self.open_diff_from_tree(t))

                return

    # ---------------------------------------------------------
    # Abrir diff desde un Treeview
    # ---------------------------------------------------------
    def open_diff_from_tree(self, tree):
        sel = tree.selection()
        if not sel:
            return

        iid = sel[0]
        diff_raw = tree.set(iid, "diff")
        file_name = tree.set(iid, "file")

        if not diff_raw or diff_raw == "None":
            messagebox.showinfo("Info", "Este archivo no tiene diferencias")
            return

        # Convertir JSON → lista real
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
