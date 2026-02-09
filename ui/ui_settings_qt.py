import json
import os
from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout,
    QRadioButton, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt

SETTINGS_FILE = "data/settings.json"


def load_settings():
    if not os.path.isfile(SETTINGS_FILE):
        return {"theme": "light"}

    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"theme": "light"}


def save_settings(settings):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4)


class SettingsTabQt(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app

        self.settings = load_settings()

        self.build_ui()

    def build_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Personalización de la interfaz")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        layout.addSpacing(10)

        layout.addWidget(QLabel("Tema visual:"))

        # Radios
        self.radio_light = QRadioButton("Claro")
        self.radio_dark = QRadioButton("Oscuro")
        self.radio_ck3 = QRadioButton("CK3 (colores del juego)")
        self.radio_sepia = QRadioButton("Sepia (lectura prolongada)")
        self.radio_contrast = QRadioButton("Alto contraste")
        self.radio_vscode_dark = QRadioButton("VS Code (oscuro)")
        self.radio_vscode_light = QRadioButton("VS Code (claro)")

        # Añadirlos al layout
        layout.addWidget(self.radio_light)
        layout.addWidget(self.radio_dark)
        layout.addWidget(self.radio_ck3)
        layout.addWidget(self.radio_sepia)
        layout.addWidget(self.radio_contrast)
        layout.addWidget(self.radio_vscode_dark)
        layout.addWidget(self.radio_vscode_light)

        # Seleccionar el tema actual
        theme = self.settings.get("theme", "light")

        if theme == "dark":
            self.radio_dark.setChecked(True)
        elif theme == "ck3":
            self.radio_ck3.setChecked(True)
        elif theme == "sepia":
            self.radio_sepia.setChecked(True)
        elif theme == "contrast":
            self.radio_contrast.setChecked(True)
        elif theme == "vscode-dark":
            self.radio_vscode_dark.setChecked(True)
        elif theme == "vscode-light":
            self.radio_vscode_light.setChecked(True)
        else:
            self.radio_light.setChecked(True)

        # Botón aplicar
        btn_apply = QPushButton("Aplicar tema")
        btn_apply.clicked.connect(self.apply_theme)
        layout.addSpacing(10)
        layout.addWidget(btn_apply)

        layout.addStretch()

    def apply_theme(self):
        # Detectar tema seleccionado
        if self.radio_dark.isChecked():
            theme = "dark"
        elif self.radio_light.isChecked():
            theme = "light"
        elif self.radio_ck3.isChecked():
            theme = "ck3"
        elif self.radio_sepia.isChecked():
            theme = "sepia"
        elif self.radio_contrast.isChecked():
            theme = "contrast"
        elif self.radio_vscode_dark.isChecked():
            theme = "vscode-dark"
        elif self.radio_vscode_light.isChecked():
            theme = "vscode-light"
        else:
            theme = "light"

        # Guardar
        self.settings["theme"] = theme
        save_settings(self.settings)

        # Aplicar inmediatamente
        self.app.apply_theme(theme)

        QMessageBox.information(self, "OK", "Tema aplicado")
