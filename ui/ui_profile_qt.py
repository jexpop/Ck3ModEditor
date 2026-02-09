from PyQt6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QComboBox,
    QFileDialog, QMessageBox, QVBoxLayout, QHBoxLayout,
    QGridLayout, QCheckBox, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt

from utils.profile_ops import (
    list_profiles,
    get_profile,
    update_profile,
    add_profile,
    delete_profile
)


class ProfileTabQt(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app

        self.profile_module_vars = {}

        self.build_ui()

    # ---------------------------------------------------------
    def build_ui(self):
        layout = QVBoxLayout(self)

        # Selector de perfil
        layout.addWidget(QLabel("Seleccionar perfil:"))
        self.profile_combo = QComboBox()
        self.profile_combo.addItems(list_profiles())
        self.profile_combo.currentIndexChanged.connect(self.on_profile_selected)
        layout.addWidget(self.profile_combo)

        # Entradas de rutas
        self.entry_game_root = self._add_path_selector(layout, "Raíz del juego")
        self.entry_mod_root = self._add_path_selector(layout, "Raíz del mod")
        self.entry_backup_root = self._add_path_selector(layout, "Carpeta de backups")

        # Botones
        layout.addWidget(self._make_button("Guardar perfil", self.save_profile))
        layout.addWidget(self._make_button("Crear perfil nuevo", self.create_profile))
        layout.addWidget(self._make_button("Renombrar perfil", self.rename_profile))
        layout.addWidget(self._make_button("Eliminar perfil", self.delete_profile_action))

        # Módulos por defecto
        layout.addWidget(QLabel("Módulos activados por defecto:"))

        # Scroll para módulos
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)

        self.modules_container = QWidget()
        self.modules_layout = QGridLayout(self.modules_container)
        scroll.setWidget(self.modules_container)

    # ---------------------------------------------------------
    def _make_button(self, text, callback):
        btn = QPushButton(text)
        btn.clicked.connect(callback)
        return btn

    # ---------------------------------------------------------
    def _add_path_selector(self, layout, label_text):
        layout.addWidget(QLabel(label_text))

        h = QHBoxLayout()
        entry = QLineEdit()
        btn = QPushButton("Seleccionar")

        def choose():
            path = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta")
            if path:
                entry.setText(path)

        btn.clicked.connect(choose)

        h.addWidget(entry)
        h.addWidget(btn)
        layout.addLayout(h)

        return entry

    # ---------------------------------------------------------
    def on_profile_selected(self):
        name = self.profile_combo.currentText()
        profile = get_profile(name)

        if not profile:
            return

        self.app.on_profile_selected(profile)

    # ---------------------------------------------------------
    def refresh(self):
        profile = self.app.current_profile
        if not profile:
            return

        # Combo
        self.profile_combo.setCurrentText(profile["name"])

        # Rutas
        self.entry_game_root.setText(profile["game_root"])
        self.entry_mod_root.setText(profile["mod_root"])
        self.entry_backup_root.setText(profile["backup_root"])

        # Módulos
        self.load_profile_modules()

    # ---------------------------------------------------------
    def load_profile_modules(self):
        # Limpiar
        for i in reversed(range(self.modules_layout.count())):
            item = self.modules_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()

        profile = self.app.current_profile
        if not profile:
            return

        game_key = profile["game"]
        game_modules = self.app.modules.get(game_key, {})

        self.profile_module_vars = {}

        cols = 3
        row = 0
        col = 0

        for module_name in sorted(game_modules.keys()):
            chk = QCheckBox(module_name)
            chk.setChecked(module_name in profile["modules"])

            self.modules_layout.addWidget(chk, row, col)
            self.profile_module_vars[module_name] = chk

            col += 1
            if col >= cols:
                col = 0
                row += 1

    # ---------------------------------------------------------
    def save_profile(self):
        profile = self.app.current_profile
        if not profile:
            QMessageBox.critical(self, "Error", "No hay perfil seleccionado")
            return

        profile["game_root"] = self.entry_game_root.text()
        profile["mod_root"] = self.entry_mod_root.text()
        profile["backup_root"] = self.entry_backup_root.text()

        # Módulos
        selected = [
            name for name, chk in self.profile_module_vars.items()
            if chk.isChecked()
        ]
        profile["modules"] = selected

        update_profile(profile)
        QMessageBox.information(self, "OK", "Perfil guardado")

    # ---------------------------------------------------------
    def create_profile(self):
        new_profile = {
            "name": "Nuevo Perfil",
            "game": "CK3",
            "game_root": "",
            "mod_root": "",
            "backup_root": "",
            "year_offset": 10000,
            "modules": []
        }

        add_profile(new_profile)

        self.profile_combo.clear()
        self.profile_combo.addItems(list_profiles())
        self.profile_combo.setCurrentText("Nuevo Perfil")

        self.app.on_profile_selected(new_profile)

    # ---------------------------------------------------------
    def rename_profile(self):
        profile = self.app.current_profile
        if not profile:
            QMessageBox.critical(self, "Error", "No hay perfil seleccionado")
            return

        from PyQt6.QtWidgets import QInputDialog
        new_name, ok = QInputDialog.getText(self, "Renombrar perfil", "Nuevo nombre:", text=profile["name"])

        if ok and new_name.strip():
            profile["name"] = new_name.strip()
            update_profile(profile)

            self.profile_combo.clear()
            self.profile_combo.addItems(list_profiles())
            self.profile_combo.setCurrentText(new_name)

    # ---------------------------------------------------------
    def delete_profile_action(self):
        profile = self.app.current_profile
        if not profile:
            QMessageBox.critical(self, "Error", "No hay perfil seleccionado")
            return

        name = profile["name"]

        if not QMessageBox.question(self, "Confirmar", f"¿Eliminar el perfil '{name}'?") == QMessageBox.StandardButton.Yes:
            return

        delete_profile(name)

        self.app.current_profile = None

        self.profile_combo.clear()
        self.profile_combo.addItems(list_profiles())

        self.entry_game_root.clear()
        self.entry_mod_root.clear()
        self.entry_backup_root.clear()

        for i in reversed(range(self.modules_layout.count())):
            item = self.modules_layout.itemAt(i)
            if item.widget():
                item.widget().deleteLater()
