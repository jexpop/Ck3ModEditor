import tkinter as tk
from tkinter import ttk
import json

from ui.ui_profile import ProfileTab
from ui.ui_dates import DatesTab
from ui.ui_modules import ModulesTab
from ui.ui_logs import LogsTab
from ui.ui_settings import SettingsTab

from ui.ui_validation_module import ValidationModuleTab
from ui.ui_validation_module_full import ValidationModuleFullTab
from ui.ui_validation_file import ValidationFileTab
from ui.ui_validation_file_full import ValidationFileFullTab

from utils.profile_ops import load_profiles
from core.processor import load_modules

from ui.ui_settings import load_settings


class ModToolApp:
    def __init__(self, root, app):
        self.root = root
        self.app = app
        root.title("CK3 Mod Tool")

        try:
            root.state("zoomed")
        except:
            root.attributes("-zoomed", True)

        # Cargar ajustes
        settings = load_settings()
        self.apply_theme(settings.get("theme", "light"))

        # Datos globales
        self.profiles = load_profiles()
        self.modules = load_modules()

        with open("data/files.json", "r", encoding="utf-8") as f:
            self.files = json.load(f)

        self.current_profile = self.profiles[0] if self.profiles else None

        # Notebook principal
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True)

        self.profile_tab = ProfileTab(self.notebook, self)
        self.dates_tab = DatesTab(self.notebook, self)
        self.modules_tab = ModulesTab(self.notebook, self)
        self.logs_tab = LogsTab(self.notebook, self)
        self.settings_tab = SettingsTab(self.notebook, self)

        self.notebook.add(self.profile_tab.frame, text="Perfil")
        self.notebook.add(self.dates_tab.frame, text="Fechas")
        self.notebook.add(self.modules_tab.frame, text="Módulos")
        self.notebook.add(self.logs_tab.frame, text="Logs")
        self.notebook.add(self.settings_tab.frame, text="Opciones")

        # Validación
        self.validation_container = ttk.Frame(self.notebook)
        self.notebook.add(self.validation_container, text="Validación")

        self.validation_notebook = ttk.Notebook(self.validation_container)
        self.validation_notebook.pack(fill="both", expand=True)

        self.validation_module_tab = ValidationModuleTab(self.validation_notebook, self)
        self.validation_module_full_tab = ValidationModuleFullTab(self.validation_notebook, self)
        self.validation_file_tab = ValidationFileTab(self.validation_notebook, self)
        self.validation_file_full_tab = ValidationFileFullTab(self.validation_notebook, self)

        self.validation_notebook.add(self.validation_module_tab.frame, text="Por módulo")
        self.validation_notebook.add(self.validation_module_full_tab.frame, text="Total (módulos)")
        self.validation_notebook.add(self.validation_file_tab.frame, text="Archivo")
        self.validation_notebook.add(self.validation_file_full_tab.frame, text="Total (archivos)")

        if self.current_profile:
            self.on_profile_selected(self.current_profile)

    # ---------------------------------------------------------
    # APLICAR TEMA
    # ---------------------------------------------------------
    def apply_theme(self, theme):
        style = ttk.Style()

        if theme == "dark":
            style.theme_use("clam")

            bg = "#222222"      # fondo principal
            bg2 = "#2b2b2b"     # paneles
            bg3 = "#3a3a3a"     # botones
            fg = "#d8d8d8"      # texto gris claro
            accent = "#4a90e2"  # azul elegante

            self.root.configure(bg=bg)

            # ttk widgets
            style.configure(".", background=bg2, foreground=fg)
            style.configure("TFrame", background=bg)
            style.configure("TLabel", background=bg, foreground=fg)
            style.configure("TButton", background=bg3, foreground=fg)
            style.map("TButton", background=[("active", "#4a4a4a")])

            style.configure("TNotebook", background=bg)
            style.configure("TNotebook.Tab", background=bg2, foreground=fg)
            style.map("TNotebook.Tab", background=[("selected", bg3)])

            style.configure(
                "Treeview",
                background=bg2,
                foreground=fg,
                fieldbackground=bg2,
                bordercolor=bg3
            )
            style.map(
                "Treeview",
                background=[("selected", accent)],
                foreground=[("selected", "#ffffff")]
            )

            self.apply_theme_to_children(self.root, theme)

        else:
            # Tema claro original
            style.theme_use("default")
            self.root.configure(bg="#f0f0f0")
            self.apply_theme_to_children(self.root, theme)

    # ---------------------------------------------------------
    # APLICAR TEMA A WIDGETS tk.* (SEGURO)
    # ---------------------------------------------------------
    def apply_theme_to_children(self, widget, theme):
        dark = (theme == "dark")

        if dark:
            text_bg = "#222222"
            entry_bg = "#2b2b2b"
            list_bg = "#2b2b2b"
            text_fg = "#d8d8d8"
            entry_fg = "#d8d8d8"
            list_fg = "#d8d8d8"
            btn_bg = "#3a3a3a"
            btn_fg = "#d8d8d8"
            btn_active = "#4a4a4a"
            frame_bg = "#222222"
            sel_bg = "#4a90e2"
        else:
            text_bg = "white"
            entry_bg = "white"
            list_bg = "white"
            text_fg = "black"
            entry_fg = "black"
            list_fg = "black"
            btn_bg = "#e0e0e0"
            btn_fg = "black"
            btn_active = "#d0d0d0"
            frame_bg = "#f0f0f0"
            sel_bg = "#0078d7"

        for child in widget.winfo_children():

            # SOLO widgets tk.* (NO ttk)
            if isinstance(child, tk.Text):
                child.configure(bg=text_bg, fg=text_fg, insertbackground=text_fg)

            elif isinstance(child, tk.Entry):
                child.configure(bg=entry_bg, fg=entry_fg, insertbackground=entry_fg)

            elif isinstance(child, tk.Listbox):
                child.configure(
                    bg=list_bg,
                    fg=list_fg,
                    selectbackground=sel_bg,
                    selectforeground="white"
                )

            elif isinstance(child, tk.Button):
                child.configure(
                    bg=btn_bg,
                    fg=btn_fg,
                    activebackground=btn_active
                )

            elif isinstance(child, tk.Frame):
                child.configure(bg=frame_bg)

            # Recursión segura
            self.apply_theme_to_children(child, theme)

    # ---------------------------------------------------------
    def on_profile_selected(self, profile):
        self.current_profile = profile

        self.profile_tab.refresh()
        self.dates_tab.refresh()
        self.modules_tab.refresh()

        self.validation_module_tab.refresh()
        self.validation_module_full_tab.refresh()
        self.validation_file_tab.refresh()
        self.validation_file_full_tab.refresh()
