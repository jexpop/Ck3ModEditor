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

        # Pestañas Qt
        self.profile_tab = ProfileTabQt(self)
        self.tabs.addTab(self.profile_tab, "Perfil")

        self.history_tab = HistoryTabQt(self)
        self.tabs.addTab(self.history_tab, "Historia")

        self.dates_tab = DatesTabQt(self)
        self.tabs.addTab(self.dates_tab, "Fechas")

        self.modules_tab = ModulesTabQt(self)
        self.tabs.addTab(self.modules_tab, "Módulos")

        self.validation_tab = ValidationTabQt(self)
        self.tabs.addTab(self.validation_tab, "Validación")

        self.logs_tab = LogsTabQt(self)
        self.tabs.addTab(self.logs_tab, "Logs")

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
        self.history_tab.refresh()
        self.dates_tab.refresh()
        self.modules_tab.refresh()
        self.validation_tab.refresh()
        # logs no necesita refresh

    # ---------------------------------------------------------
    # Temas
    # ---------------------------------------------------------
    def apply_theme(self, theme):
        self.theme = theme  # Guardamos el tema actual

        # ============================
        #  TEMA OSCURO
        # ============================
        if theme == "dark":
            self.setStyleSheet("""
                QWidget {
                    background-color: #2b2b2b;
                    color: #e6e6e6;
                    font-family: Segoe UI, Arial;
                    font-size: 12px;
                }
                QLineEdit, QTextEdit, QListWidget, QTreeWidget {
                    background-color: #3a3a3a;
                    color: #e6e6e6;
                    border: 1px solid #555;
                }
                QPushButton {
                    background-color: #444;
                    color: #e6e6e6;
                    padding: 6px;
                    border: 1px solid #666;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #555;
                }
                QTabWidget::pane {
                    border: 1px solid #555;
                }
                QTabBar::tab {
                    background: #444;
                    padding: 6px 12px;
                    margin-right: 2px;
                }
                QTabBar::tab:selected {
                    background: #555;
                    border: 1px solid #777;
                }
            """)

        # ============================
        #  TEMA CLARO
        # ============================
        elif theme == "light":
            self.setStyleSheet("""
                QWidget {
                    background-color: #f5f5f5;
                    color: #202020;
                    font-family: Segoe UI, Arial;
                    font-size: 12px;
                }
                QLineEdit, QTextEdit, QListWidget, QTreeWidget {
                    background-color: #ffffff;
                    color: #202020;
                    border: 1px solid #c0c0c0;
                }
                QPushButton {
                    background-color: #e6e6e6;
                    color: #202020;
                    padding: 6px;
                    border: 1px solid #b0b0b0;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #dcdcdc;
                }
                QTabWidget::pane {
                    border: 1px solid #c0c0c0;
                }
                QTabBar::tab {
                    background: #e6e6e6;
                    padding: 6px 12px;
                    margin-right: 2px;
                }
                QTabBar::tab:selected {
                    background: #ffffff;
                    border: 1px solid #c0c0c0;
                }
            """)

        # ============================
        #  TEMA CK3
        # ============================
        elif theme == "ck3":
            self.setStyleSheet("""
                QWidget {
                    background-color: #1c1a17;
                    color: #e0d6b9;
                    font-family: "Trajan Pro", Georgia, serif;
                    font-size: 13px;
                }
                QLineEdit, QTextEdit, QListWidget, QTreeWidget {
                    background-color: #2a2723;
                    color: #e0d6b9;
                    border: 1px solid #6b5b3b;
                }
                QPushButton {
                    background-color: #3a332b;
                    color: #e0d6b9;
                    padding: 6px;
                    border: 1px solid #6b5b3b;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #4a4238;
                }
                QTabWidget::pane {
                    border: 1px solid #6b5b3b;
                }
                QTabBar::tab {
                    background: #3a332b;
                    padding: 6px 12px;
                    margin-right: 2px;
                }
                QTabBar::tab:selected {
                    background: #4a4238;
                    border: 1px solid #6b5b3b;
                }
            """)

        # ============================
        #  TEMA SEPIA
        # ============================
        elif theme == "sepia":
            self.setStyleSheet("""
                QWidget {
                    background-color: #f4ecd8;
                    color: #4b3e2a;
                    font-family: Georgia, serif;
                    font-size: 13px;
                }
                QLineEdit, QTextEdit, QListWidget, QTreeWidget {
                    background-color: #fff8e7;
                    color: #4b3e2a;
                    border: 1px solid #c8b89a;
                }
                QPushButton {
                    background-color: #e8dcc2;
                    color: #4b3e2a;
                    padding: 6px;
                    border: 1px solid #b8a98a;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #e0d2b8;
                }
                QTabWidget::pane {
                    border: 1px solid #c8b89a;
                }
                QTabBar::tab {
                    background: #e8dcc2;
                    padding: 6px 12px;
                    margin-right: 2px;
                }
                QTabBar::tab:selected {
                    background: #fff8e7;
                    border: 1px solid #c8b89a;
                }
            """)

        # ============================
        #  TEMA ALTO CONTRASTE
        # ============================
        elif theme == "contrast":
            self.setStyleSheet("""
                QWidget {
                    background-color: #000000;
                    color: #ffffff;
                    font-family: Segoe UI, Arial;
                    font-size: 13px;
                }
                QLineEdit, QTextEdit, QListWidget, QTreeWidget {
                    background-color: #000000;
                    color: #ffffff;
                    border: 2px solid #ffffff;
                }
                QPushButton {
                    background-color: #000000;
                    color: #ffffff;
                    padding: 6px;
                    border: 2px solid #ffffff;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #222222;
                }
                QTabWidget::pane {
                    border: 2px solid #ffffff;
                }
                QTabBar::tab {
                    background: #000000;
                    padding: 6px 12px;
                    margin-right: 2px;
                    border: 2px solid #ffffff;
                }
                QTabBar::tab:selected {
                    background: #222222;
                }
            """)

        # ============================
        #  TEMA VS CODE OSCURO
        # ============================
        elif theme == "vscode-dark":
            self.setStyleSheet("""
                QWidget {
                    background-color: #1e1e1e;
                    color: #d4d4d4;
                    font-family: Segoe UI, Arial;
                    font-size: 12px;
                }
                QLineEdit, QTextEdit, QListWidget, QTreeWidget {
                    background-color: #252526;
                    color: #d4d4d4;
                    border: 1px solid #3c3c3c;
                }
                QPushButton {
                    background-color: #3c3c3c;
                    color: #d4d4d4;
                    padding: 6px;
                    border: 1px solid #555;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #454545;
                }
                QTabWidget::pane {
                    border: 1px solid #3c3c3c;
                }
                QTabBar::tab {
                    background: #2d2d2d;
                    padding: 6px 12px;
                    margin-right: 2px;
                }
                QTabBar::tab:selected {
                    background: #1e1e1e;
                    border: 1px solid #007acc;
                }
            """)

        # ============================
        #  TEMA VS CODE CLARO
        # ============================
        elif theme == "vscode-light":
            self.setStyleSheet("""
                QWidget {
                    background-color: #ffffff;
                    color: #333333;
                    font-family: Segoe UI, Arial;
                    font-size: 12px;
                }
                QLineEdit, QTextEdit, QListWidget, QTreeWidget {
                    background-color: #ffffff;
                    color: #333333;
                    border: 1px solid #cccccc;
                }
                QPushButton {
                    background-color: #e6e6e6;
                    color: #333333;
                    padding: 6px;
                    border: 1px solid #bfbfbf;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #dcdcdc;
                }
                QTabWidget::pane {
                    border: 1px solid #cccccc;
                }
                QTabBar::tab {
                    background: #f3f3f3;
                    padding: 6px 12px;
                    margin-right: 2px;
                }
                QTabBar::tab:selected {
                    background: #ffffff;
                    border: 1px solid #007acc;
                }
            """)
