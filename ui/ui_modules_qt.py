from PyQt6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QListWidget,
    QVBoxLayout, QHBoxLayout, QMessageBox
)
import json


class ModulesTabQt(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app

        self.build_ui()

    # ---------------------------------------------------------
    # UI
    # ---------------------------------------------------------
    def build_ui(self):
        layout = QVBoxLayout(self)

        # Juego del perfil
        layout.addWidget(QLabel("Juego del perfil actual:"))
        self.label_game = QLabel("")
        layout.addWidget(self.label_game)

        # Lista de módulos
        self.listbox = QListWidget()
        self.listbox.itemSelectionChanged.connect(self.on_module_selected)
        layout.addWidget(self.listbox)

        # Campos de edición
        layout.addWidget(QLabel("Nombre del módulo:"))
        self.entry_name = QLineEdit()
        layout.addWidget(self.entry_name)

        layout.addWidget(QLabel("Ruta relativa:"))
        self.entry_path = QLineEdit()
        layout.addWidget(self.entry_path)

        layout.addWidget(QLabel("Extensiones ignoradas (coma):"))
        self.entry_ignore = QLineEdit()
        layout.addWidget(self.entry_ignore)

        # Botones
        btn_add = QPushButton("Añadir módulo")
        btn_add.clicked.connect(self.add_module)
        layout.addWidget(btn_add)

        btn_save = QPushButton("Guardar cambios")
        btn_save.clicked.connect(self.save_module)
        layout.addWidget(btn_save)

        btn_delete = QPushButton("Eliminar módulo")
        btn_delete.clicked.connect(self.delete_module)
        layout.addWidget(btn_delete)

    # ---------------------------------------------------------
    # REFRESH
    # ---------------------------------------------------------
    def refresh(self):
        profile = self.app.current_profile
        if not profile:
            return

        game_key = profile["game"]
        self.label_game.setText(game_key)

        self.load_modules()

    # ---------------------------------------------------------
    # Cargar módulos en la lista
    # ---------------------------------------------------------
    def load_modules(self):
        self.listbox.clear()

        profile = self.app.current_profile
        if not profile:
            return

        game_key = profile["game"]
        game_modules = self.app.modules.get(game_key, {})

        for name in sorted(game_modules.keys()):
            self.listbox.addItem(name)

    # ---------------------------------------------------------
    # Selección de módulo
    # ---------------------------------------------------------
    def on_module_selected(self):
        items = self.listbox.selectedItems()
        if not items:
            return

        name = items[0].text()
        profile = self.app.current_profile
        game_key = profile["game"]

        cfg = self.app.modules.get(game_key, {}).get(name)
        if not cfg:
            return

        self.entry_name.setText(name)
        self.entry_path.setText(cfg.get("path", ""))

        ignore = ", ".join(cfg.get("ignore_ext", []))
        self.entry_ignore.setText(ignore)

    # ---------------------------------------------------------
    # Añadir módulo
    # ---------------------------------------------------------
    def add_module(self):
        profile = self.app.current_profile
        if not profile:
            QMessageBox.critical(self, "Error", "No hay perfil seleccionado")
            return

        name = self.entry_name.text().strip()
        path = self.entry_path.text().strip()
        ignore = [ext.strip() for ext in self.entry_ignore.text().split(",") if ext.strip()]

        if not name or not path:
            QMessageBox.critical(self, "Error", "Nombre y ruta son obligatorios")
            return

        game_key = profile["game"]

        if game_key not in self.app.modules:
            self.app.modules[game_key] = {}

        self.app.modules[game_key][name] = {
            "path": path,
            "ignore_ext": ignore
        }

        self.save_modules_file()
        self.load_modules()

    # ---------------------------------------------------------
    # Guardar módulo
    # ---------------------------------------------------------
    def save_module(self):
        profile = self.app.current_profile
        if not profile:
            QMessageBox.critical(self, "Error", "No hay perfil seleccionado")
            return

        name = self.entry_name.text().strip()
        path = self.entry_path.text().strip()
        ignore = [ext.strip() for ext in self.entry_ignore.text().split(",") if ext.strip()]

        game_key = profile["game"]

        if name not in self.app.modules.get(game_key, {}):
            QMessageBox.critical(self, "Error", "El módulo no existe")
            return

        self.app.modules[game_key][name]["path"] = path
        self.app.modules[game_key][name]["ignore_ext"] = ignore

        self.save_modules_file()
        self.load_modules()

    # ---------------------------------------------------------
    # Eliminar módulo
    # ---------------------------------------------------------
    def delete_module(self):
        profile = self.app.current_profile
        if not profile:
            QMessageBox.critical(self, "Error", "No hay perfil seleccionado")
            return

        items = self.listbox.selectedItems()
        if not items:
            return

        name = items[0].text()
        game_key = profile["game"]

        if name in self.app.modules.get(game_key, {}):
            del self.app.modules[game_key][name]

        self.save_modules_file()
        self.load_modules()

    # ---------------------------------------------------------
    # Guardar modules.json
    # ---------------------------------------------------------
    def save_modules_file(self):
        with open("data/modules.json", "w", encoding="utf-8") as f:
            json.dump(self.app.modules, f, indent=4)
