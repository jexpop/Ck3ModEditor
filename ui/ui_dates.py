import tkinter as tk
from tkinter import ttk, messagebox
import os
import shutil

from core.processor import process_module
from core.defines import read_end_date, read_mod_end_date, write_end_date


class DatesTab:
    def __init__(self, parent, app):
        self.app = app
        self.frame = ttk.Frame(parent)

        self.module_vars = {}

        self.build_ui()

    # ---------------------------------------------------------
    # UI
    # ---------------------------------------------------------
    def build_ui(self):
        frame = self.frame

        # Notebook interno
        self.sub_notebook = ttk.Notebook(frame)
        self.sub_notebook.pack(fill="both", expand=True)

        # Subpestañas
        self.tab_process = ttk.Frame(self.sub_notebook)
        self.tab_logs = ttk.Frame(self.sub_notebook)

        self.sub_notebook.add(self.tab_process, text="Procesado")
        self.sub_notebook.add(self.tab_logs, text="Logs")

        # Construir subpestañas
        self.build_process_tab()
        self.build_logs_tab()

    # ---------------------------------------------------------
    # SUBPESTAÑA: PROCESADO
    # ---------------------------------------------------------
    def build_process_tab(self):
        frame = self.tab_process

        # Offset
        tk.Label(frame, text="Offset de año:").pack()
        self.entry_offset = tk.Entry(frame)
        self.entry_offset.pack()

        # END_DATE
        tk.Label(frame, text="Fecha final del juego (END_DATE):").pack(pady=5)
        self.entry_end_date = tk.Entry(frame)
        self.entry_end_date.pack()

        # Indicador de origen
        self.label_end_date_source = tk.Label(frame, text="", fg="#666")
        self.label_end_date_source.pack(pady=2)

        tk.Button(frame, text="Guardar END_DATE en el mod", command=self.save_end_date).pack(pady=5)

        # ---------------------------------------------------------
        # MÓDULOS A PROCESAR (CON SCROLL + GRID DE 8 COLUMNAS)
        # ---------------------------------------------------------
        tk.Label(frame, text="Módulos a procesar:").pack(pady=10)

        container = tk.Frame(frame)
        container.pack(fill="both", expand=True)

        # Canvas con altura fija
        self.canvas = tk.Canvas(container, height=220)
        self.canvas.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        scrollbar.pack(side="right", fill="y")

        self.canvas.configure(yscrollcommand=scrollbar.set)

        # Frame interno
        self.modules_frame = tk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.modules_frame,
            anchor="nw"
        )

        # Ajustar scroll
        def update_scroll_region(event):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        self.modules_frame.bind("<Configure>", update_scroll_region)

        # Botón procesar
        tk.Button(frame, text="Procesar", command=self.run_processing).pack(pady=10)

    # ---------------------------------------------------------
    # SUBPESTAÑA: LOGS
    # ---------------------------------------------------------
    def build_logs_tab(self):
        frame = self.tab_logs
        tk.Label(frame, text="Los logs se guardan en logs/<perfil>/<modulo>.log").pack(pady=10)

    # ---------------------------------------------------------
    # REFRESH
    # ---------------------------------------------------------
    def refresh(self):
        profile = self.app.current_profile
        if not profile:
            return

        # Offset
        self.entry_offset.delete(0, tk.END)
        self.entry_offset.insert(0, str(profile["year_offset"]))

        # END_DATE: primero la del mod, luego la del juego
        mod_date = read_mod_end_date(profile["mod_root"])
        game_date = read_end_date(profile["game_root"])

        if mod_date:
            final_date = mod_date
            source = "(mod)"
        elif game_date:
            final_date = game_date
            source = "(juego)"
        else:
            final_date = ""
            source = "(no encontrado)"

        self.entry_end_date.delete(0, tk.END)
        self.entry_end_date.insert(0, final_date)
        self.label_end_date_source.config(text=f"Origen: {source}")

        # Módulos
        self.load_modules_for_process()

    # ---------------------------------------------------------
    # MÓDULOS PARA PROCESADO
    # ---------------------------------------------------------
    def load_modules_for_process(self):
        for widget in self.modules_frame.winfo_children():
            widget.destroy()

        profile = self.app.current_profile
        if not profile:
            return

        game_key = profile["game"]
        game_modules = self.app.modules.get(game_key, {})

        self.module_vars = {}
        self.module_widgets = []

        for module_name in sorted(game_modules.keys()):
            default_active = module_name in profile["modules"]
            var = tk.IntVar(value=1 if default_active else 0)

            chk = tk.Checkbutton(self.modules_frame, text=module_name, variable=var)
            self.module_vars[module_name] = var
            self.module_widgets.append(chk)

        # Distribuir en 8 columnas
        self.reflow_modules()

    # ---------------------------------------------------------
    # DISTRIBUCIÓN EN 8 COLUMNAS
    # ---------------------------------------------------------
    def reflow_modules(self):
        cols = 8
        row = 0
        col = 0

        for w in self.module_widgets:
            w.grid(row=row, column=col, sticky="w", padx=10, pady=3)
            col += 1
            if col >= cols:
                col = 0
                row += 1

    # ---------------------------------------------------------
    # PROCESADO
    # ---------------------------------------------------------
    def run_processing(self):
        profile = self.app.current_profile
        if not profile:
            messagebox.showerror("Error", "Selecciona un perfil")
            return

        try:
            offset = int(self.entry_offset.get())
        except ValueError:
            messagebox.showerror("Error", "Offset inválido")
            return

        # Guardar offset en el perfil
        profile["year_offset"] = offset
        from utils.profile_ops import update_profile
        update_profile(profile)

        game_root = profile["game_root"]
        mod_root = profile["mod_root"]
        backup_root = profile["backup_root"]
        game_key = profile["game"]
        profile_name = profile["name"]

        for module_name, var in self.module_vars.items():
            if var.get() == 1:
                process_module(
                    game_key,
                    module_name,
                    game_root,
                    mod_root,
                    backup_root,
                    offset,
                    profile_name
                )

        messagebox.showinfo("OK", "Procesado completado")

    # ---------------------------------------------------------
    # END_DATE
    # ---------------------------------------------------------
    def save_end_date(self):
        profile = self.app.current_profile
        if not profile:
            messagebox.showerror("Error", "Selecciona un perfil")
            return

        new_date = self.entry_end_date.get().strip()
        if not new_date:
            messagebox.showerror("Error", "Fecha inválida")
            return

        ok = write_end_date(
            game_root=profile["game_root"],
            mod_root=profile["mod_root"],
            backup_root=profile["backup_root"],
            new_date=new_date
        )

        if ok:
            messagebox.showinfo("OK", "END_DATE guardado en el mod")
        else:
            messagebox.showerror("Error", "No se pudo guardar END_DATE")
