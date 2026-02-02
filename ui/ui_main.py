import tkinter as tk
from tkinter import ttk

from ui.ui_profile import ProfileTab
from ui.ui_dates import DatesTab
from ui.ui_modules import ModulesTab
from ui.ui_logs import LogsTab
from ui.ui_validation_module import ValidationModuleTab
from ui.ui_validation_full import ValidationFullTab

from utils.profile_ops import load_profiles
from core.processor import load_modules


class ModToolApp:
    def __init__(self, root):
        self.root = root
        root.title("CK3 Mod Tool")

        # Datos globales
        self.profiles = load_profiles()
        self.modules = load_modules()
        self.current_profile = None

        # Notebook principal
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True)

        # Crear pestañas
        self.profile_tab = ProfileTab(self.notebook, self)
        self.dates_tab = DatesTab(self.notebook, self)
        self.modules_tab = ModulesTab(self.notebook, self)
        self.logs_tab = LogsTab(self.notebook, self)
        self.validation_module_tab = ValidationModuleTab(self.notebook, self)
        self.validation_full_tab = ValidationFullTab(self.notebook, self)

        # Añadir pestañas al notebook
        self.notebook.add(self.profile_tab.frame, text="Perfil")
        self.notebook.add(self.dates_tab.frame, text="Fechas")
        self.notebook.add(self.modules_tab.frame, text="Módulos")
        self.notebook.add(self.logs_tab.frame, text="Logs")
        self.notebook.add(self.validation_module_tab.frame, text="Validación")
        self.notebook.add(self.validation_full_tab.frame, text="Validación Total")

    # Método para actualizar todas las pestañas cuando se selecciona un perfil
    def on_profile_selected(self, profile):
        self.current_profile = profile

        self.profile_tab.refresh()
        self.dates_tab.refresh()
        self.modules_tab.refresh()
        self.validation_module_tab.refresh()
        self.validation_full_tab.refresh()
