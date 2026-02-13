from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QTabWidget, QVBoxLayout
)
from PyQt6.QtCore import Qt
import json

# Pestañas Qt
from ui.ui_profile_qt import ProfileTabQt
from ui.history import HistoryTabQt
from ui.ui_dates_qt import DatesTabQt
from ui.ui_modules_qt import ModulesTabQt
from ui.ui_logs_qt import LogsTabQt
from ui.ui_settings_qt import SettingsTabQt, load_settings
from ui.ui_validation_qt import ValidationTabQt

# Datos
from utils.profile_ops import load_profiles
from core.processor import load_modules


class ModToolAppQt(QMainWindow):
    def __init__(self, app):
        super().__init__()

        self.app = app
        self.setWindowTitle("CK3 Mod Tool (Qt)")

        # Maximizar ventana
        self.showMaximized()

        # Cargar ajustes
        settings = load_settings()
        self.theme = settings.get("theme", "light")

        # Datos globales
        self.profiles = load_profiles()
        self.modules = load_modules()

        with open("data/files.json", "r", encoding="utf-8") as f:
            self.files = json.load(f)

        self.current_profile = self.profiles[0] if self.profiles else None

        # Widget central
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)

        # Notebook principal
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # -----------------------------
        # PESTAÑAS
        # -----------------------------

        # Perfil
        self.profile_tab = ProfileTabQt(self)
        self.tabs.addTab(self.profile_tab, "Perfil")

        # Historia BASE
        self.history_tab_base = HistoryTabQt(self, mode="base")
        self.tabs.addTab(self.history_tab_base, "Historia (Base)")

        # Historia MOD
        self.history_tab_mod = HistoryTabQt(self, mode="mod")
        self.tabs.addTab(self.history_tab_mod, "Historia (Mod)")

        # Fechas
        self.dates_tab = DatesTabQt(self)
        self.tabs.addTab(self.dates_tab, "Fechas")

        # Módulos
        self.modules_tab = ModulesTabQt(self)
        self.tabs.addTab(self.modules_tab, "Módulos")

        # Validación
        self.validation_tab = ValidationTabQt(self)
        self.tabs.addTab(self.validation_tab, "Validación")

        # Logs
        self.logs_tab = LogsTabQt(self)
        self.tabs.addTab(self.logs_tab, "Logs")

        # Opciones
        self.settings_tab = SettingsTabQt(self)
        self.tabs.addTab(self.settings_tab, "Opciones")

        # Aplicar tema inicial
        self.apply_theme(self.theme)

        # Cargar primer perfil
        if self.current_profile:
            self.on_profile_selected(self.current_profile)

        # Evitar que Qt reduzca la ventana después de mostrarla
        self.setMinimumSize(self.screen().size())


    # ---------------------------------------------------------
    # Cuando cambia el perfil
    # ---------------------------------------------------------
    def on_profile_selected(self, profile):
        self.current_profile = profile

        self.profile_tab.refresh()
        self.history_tab_base.refresh()
        self.history_tab_mod.refresh()
        self.dates_tab.refresh()
        self.modules_tab.refresh()
        self.validation_tab.refresh()
        # logs no necesita refresh

    # ---------------------------------------------------------
    # Temas
    # ---------------------------------------------------------
    def apply_theme(self, theme):
        self.theme = theme

        # (todo tu código de temas aquí sin cambios)
        # ...
