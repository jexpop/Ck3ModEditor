import tkinter as tk
from tkinter import ttk, messagebox
import os
import json


FILTER_FILE = "data/log_filters.json"


def load_filters():
    if not os.path.isfile(FILTER_FILE):
        return []
    try:
        with open(FILTER_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("filters", [])
    except:
        return []


def save_filters(filters):
    with open(FILTER_FILE, "w", encoding="utf-8") as f:
        json.dump({"filters": filters}, f, indent=4)


class LogsTab:
    def __init__(self, parent, app):
        self.app = app
        self.frame = ttk.Frame(parent)

        self.filters = load_filters()

        self.build_ui()

    # ---------------------------------------------------------
    # UI
    # ---------------------------------------------------------
    def build_ui(self):
        notebook = ttk.Notebook(self.frame)
        notebook.pack(fill="both", expand=True)

        # -------------------------
        # SUBPESTAÑA: VISOR DE LOGS
        # -------------------------
        self.viewer_frame = ttk.Frame(notebook)
        notebook.add(self.viewer_frame, text="Visor de logs")

        self.build_viewer_ui()

        # -------------------------
        # SUBPESTAÑA: CONFIGURACIÓN
        # -------------------------
        self.config_frame = ttk.Frame(notebook)
        notebook.add(self.config_frame, text="Configuración de filtros")

        self.build_config_ui()

    # ---------------------------------------------------------
    # VISOR
    # ---------------------------------------------------------
    def build_viewer_ui(self):
        frame = self.viewer_frame

        tk.Label(frame, text="Visor de error.log del juego").pack(pady=5)

        toolbar = tk.Frame(frame)
        toolbar.pack(fill="x")

        tk.Button(toolbar, text="Recargar", command=self.load_log).pack(side="left", padx=5)

        tk.Label(toolbar, text="Filtrar:").pack(side="left")
        self.filter_var = tk.StringVar()
        tk.Entry(toolbar, textvariable=self.filter_var, width=20).pack(side="left", padx=5)
        tk.Button(toolbar, text="Aplicar", command=self.apply_filter).pack(side="left")

        # Caja de texto
        text_frame = tk.Frame(frame)
        text_frame.pack(fill="both", expand=True)

        self.text = tk.Text(text_frame, wrap="none")
        self.text.pack(side="left", fill="both", expand=True)

        scrollbar_y = tk.Scrollbar(text_frame, orient="vertical", command=self.text.yview)
        scrollbar_y.pack(side="right", fill="y")
        self.text.configure(yscrollcommand=scrollbar_y.set)

        scrollbar_x = tk.Scrollbar(frame, orient="horizontal", command=self.text.xview)
        scrollbar_x.pack(fill="x")
        self.text.configure(xscrollcommand=scrollbar_x.set)

        # Colores
        self.text.tag_config("ERROR", foreground="red")
        self.text.tag_config("WARNING", foreground="orange")
        self.text.tag_config("INFO", foreground="gray")

    # ---------------------------------------------------------
    # CONFIGURACIÓN
    # ---------------------------------------------------------
    def build_config_ui(self):
        frame = self.config_frame

        tk.Label(frame, text="Filtros de líneas a omitir en error.log").pack(pady=5)

        self.listbox = tk.Listbox(frame, height=10, width=80)
        self.listbox.pack(pady=5)

        for f in self.filters:
            self.listbox.insert("end", f)

        entry_frame = tk.Frame(frame)
        entry_frame.pack(pady=5)

        tk.Label(entry_frame, text="Nuevo filtro:").pack(side="left")
        self.new_filter_var = tk.StringVar()
        tk.Entry(entry_frame, textvariable=self.new_filter_var, width=40).pack(side="left", padx=5)

        tk.Button(entry_frame, text="Añadir", command=self.add_filter).pack(side="left")

        tk.Button(frame, text="Eliminar seleccionado", command=self.remove_filter).pack(pady=5)

    # ---------------------------------------------------------
    # Obtener ruta real del error.log
    # ---------------------------------------------------------
    def get_error_log_path(self):
        profile = self.app.current_profile
        if not profile:
            return None

        mod_root = profile["mod_root"]
        if not mod_root:
            return None

        base_dir = os.path.dirname(mod_root)      # /mod
        base_dir = os.path.dirname(base_dir)      # raíz del juego

        return os.path.join(base_dir, "logs", "error.log")

    # ---------------------------------------------------------
    # Cargar error.log
    # ---------------------------------------------------------
    def load_log(self):
        self.text.config(state="normal")
        self.text.delete("1.0", "end")

        log_path = self.get_error_log_path()

        if not log_path or not os.path.isfile(log_path):
            self.text.insert("end", "No se encontró error.log\n")
            self.text.config(state="disabled")
            return

        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:

                # 🔥 Aplicar filtros configurados
                if any(filt.lower() in line.lower() for filt in self.filters):
                    continue

                tag = None
                upper = line.upper()

                if "ERROR" in upper:
                    tag = "ERROR"
                elif "WARN" in upper:
                    tag = "WARNING"
                elif "INFO" in upper:
                    tag = "INFO"

                if tag:
                    self.text.insert("end", line, tag)
                else:
                    self.text.insert("end", line)

        self.text.config(state="disabled")

    # ---------------------------------------------------------
    # Aplicar filtro manual
    # ---------------------------------------------------------
    def apply_filter(self):
        filtro = self.filter_var.get().strip().lower()

        self.text.config(state="normal")
        self.text.delete("1.0", "end")

        log_path = self.get_error_log_path()
        if not log_path or not os.path.isfile(log_path):
            self.text.insert("end", "No se encontró error.log\n")
            self.text.config(state="disabled")
            return

        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:

                # 🔥 Aplicar filtros configurados
                if any(filt.lower() in line.lower() for filt in self.filters):
                    continue

                if filtro in line.lower():
                    tag = None
                    upper = line.upper()

                    if "ERROR" in upper:
                        tag = "ERROR"
                    elif "WARN" in upper:
                        tag = "WARNING"
                    elif "INFO" in upper:
                        tag = "INFO"

                    if tag:
                        self.text.insert("end", line, tag)
                    else:
                        self.text.insert("end", line)

        self.text.config(state="disabled")

    # ---------------------------------------------------------
    # Añadir filtro
    # ---------------------------------------------------------
    def add_filter(self):
        new = self.new_filter_var.get().strip()
        if not new:
            return

        self.filters.append(new)
        save_filters(self.filters)

        self.listbox.insert("end", new)
        self.new_filter_var.set("")

    # ---------------------------------------------------------
    # Eliminar filtro
    # ---------------------------------------------------------
    def remove_filter(self):
        sel = self.listbox.curselection()
        if not sel:
            return

        idx = sel[0]
        value = self.listbox.get(idx)

        self.filters.remove(value)
        save_filters(self.filters)

        self.listbox.delete(idx)
