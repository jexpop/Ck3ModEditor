import tkinter as tk
from tkinter import ttk, messagebox

from core.validation import (
    collect_module_files,
    compare_file_contents
)


class ValidationFullTab:
    def __init__(self, parent, app):
        self.app = app
        self.frame = ttk.Frame(parent)

        # Diffs en memoria
        self.full_validation_diffs = {}
        self.full_validation_details = {}

        self.build_ui()

    # ---------------------------------------------------------
    # UI
    # ---------------------------------------------------------
    def build_ui(self):
        frame = self.frame

        tk.Button(frame, text="Validar todos los módulos", command=self.run_full_validation).pack(pady=10)

        # Resumen
        tk.Label(frame, text="Resumen por módulo:").pack()
        self.listbox_summary = tk.Listbox(frame, width=80, height=10)
        self.listbox_summary.pack()
        self.listbox_summary.bind("<<ListboxSelect>>", self.on_module_selected)

        # Detalle
        tk.Label(frame, text="Detalles del módulo seleccionado (solo archivos problemáticos):").pack(pady=10)
        self.listbox_details = tk.Listbox(frame, width=80, height=15)
        self.listbox_details.pack()

        tk.Button(frame, text="Ver diff del archivo seleccionado", command=self.show_selected_diff).pack(pady=10)

    # ---------------------------------------------------------
    # REFRESH
    # ---------------------------------------------------------
    def refresh(self):
        self.listbox_summary.delete(0, tk.END)
        self.listbox_details.delete(0, tk.END)
        self.full_validation_diffs.clear()
        self.full_validation_details.clear()

    # ---------------------------------------------------------
    # VALIDACIÓN TOTAL
    # ---------------------------------------------------------
    def run_full_validation(self):
        self.listbox_summary.delete(0, tk.END)
        self.listbox_details.delete(0, tk.END)
        self.full_validation_diffs.clear()
        self.full_validation_details.clear()

        profile = self.app.current_profile
        if not profile:
            messagebox.showerror("Error", "Selecciona un perfil")
            return

        game_key = profile["game"]
        game_modules = self.app.modules.get(game_key, {})

        if not game_modules:
            messagebox.showerror("Error", "No hay módulos definidos para este juego")
            return

        game_root = profile["game_root"]
        backup_root = profile["backup_root"]

        if not game_root or not backup_root:
            messagebox.showerror("Error", "Configura rutas de juego y backup en el perfil")
            return

        summary = []

        for module_name, cfg in game_modules.items():
            rel_path = cfg["path"]

            # Recolectar archivos
            game_files, backup_files = collect_module_files(game_root, backup_root, rel_path)

            all_keys = set(game_files.keys()) | set(backup_files.keys())

            changed = 0
            only_game = 0
            only_backup = 0

            details = []

            for rel in all_keys:
                g = game_files.get(rel)
                b = backup_files.get(rel)

                if g and b:
                    same, diff_lines = compare_file_contents(g, b)
                    if not same:
                        changed += 1
                        key = f"{module_name}:{rel}"
                        self.full_validation_diffs[key] = diff_lines
                        details.append(f"[!] {rel} — CAMBIADO")
                elif g and not b:
                    only_game += 1
                    details.append(f"[+] {rel} — SOLO EN JUEGO")
                elif b and not g:
                    only_backup += 1
                    details.append(f"[-] {rel} — SOLO EN BACKUP")

            summary.append((module_name, changed, only_game, only_backup))
            self.full_validation_details[module_name] = details

        # Mostrar resumen
        for module_name, changed, only_game, only_backup in summary:
            line = f"{module_name} — Cambiados:{changed}  Nuevos:{only_game}  Eliminados:{only_backup}"
            self.listbox_summary.insert(tk.END, line)

    # ---------------------------------------------------------
    # MOSTRAR DETALLE AL SELECCIONAR MÓDULO
    # ---------------------------------------------------------
    def on_module_selected(self, event=None):
        sel = self.listbox_summary.curselection()
        if not sel:
            return

        line = self.listbox_summary.get(sel[0])
        module_name = line.split(" — ")[0].strip()

        self.listbox_details.delete(0, tk.END)

        details = self.full_validation_details.get(module_name, [])
        for d in details:
            self.listbox_details.insert(tk.END, d)

    # ---------------------------------------------------------
    # MOSTRAR DIFF
    # ---------------------------------------------------------
    def show_selected_diff(self):
        sel = self.listbox_details.curselection()
        if not sel:
            return

        line = self.listbox_details.get(sel[0])
        if "CAMBIADO" not in line:
            messagebox.showinfo("Info", "Solo hay diff para archivos marcados como CAMBIADO")
            return

        rel = line.split(" ", 1)[1].split(" — ")[0].strip()

        sel_mod = self.listbox_summary.curselection()
        if not sel_mod:
            messagebox.showerror("Error", "Selecciona primero un módulo en el resumen")
            return

        mod_line = self.listbox_summary.get(sel_mod[0])
        module_name = mod_line.split(" — ")[0].strip()

        key = f"{module_name}:{rel}"
        if key not in self.full_validation_diffs:
            messagebox.showerror("Error", "No se encontró diff para este archivo")
            return

        diff_lines = self.full_validation_diffs[key]
        self.show_diff_window(f"{module_name}:{rel}", diff_lines)

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
