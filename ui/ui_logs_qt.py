import os
import json
from PyQt6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QTextEdit, QListWidget,
    QVBoxLayout, QHBoxLayout, QMessageBox, QTabWidget
)
from PyQt6.QtGui import QTextCursor, QColor, QTextCharFormat
from PyQt6.QtCore import Qt


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


class LogsTabQt(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app

        self.filters = load_filters()

        self.build_ui()

    # ---------------------------------------------------------
    # UI
    # ---------------------------------------------------------
    def build_ui(self):
        layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # -------------------------
        # SUBPESTAÑA: VISOR DE LOGS
        # -------------------------
        self.viewer_tab = QWidget()
        self.tabs.addTab(self.viewer_tab, "Visor de logs")
        self.build_viewer_ui()

        # -------------------------
        # SUBPESTAÑA: CONFIGURACIÓN
        # -------------------------
        self.config_tab = QWidget()
        self.tabs.addTab(self.config_tab, "Configuración de filtros")
        self.build_config_ui()

    # ---------------------------------------------------------
    # VISOR
    # ---------------------------------------------------------
    def build_viewer_ui(self):
        layout = QVBoxLayout(self.viewer_tab)

        layout.addWidget(QLabel("Visor de error.log del juego"))

        # Toolbar
        toolbar = QHBoxLayout()
        layout.addLayout(toolbar)

        btn_reload = QPushButton("Recargar")
        btn_reload.clicked.connect(self.load_log)
        toolbar.addWidget(btn_reload)

        toolbar.addWidget(QLabel("Filtrar:"))
        self.filter_entry = QLineEdit()
        toolbar.addWidget(self.filter_entry)

        btn_apply = QPushButton("Aplicar")
        btn_apply.clicked.connect(self.apply_filter)
        toolbar.addWidget(btn_apply)

        # Caja de texto
        self.text = QTextEdit()
        self.text.setReadOnly(True)
        layout.addWidget(self.text)

    # ---------------------------------------------------------
    # CONFIGURACIÓN
    # ---------------------------------------------------------
    def build_config_ui(self):
        layout = QVBoxLayout(self.config_tab)

        layout.addWidget(QLabel("Filtros de líneas a omitir en error.log"))

        self.listbox = QListWidget()
        layout.addWidget(self.listbox)

        for f in self.filters:
            self.listbox.addItem(f)

        entry_row = QHBoxLayout()
        layout.addLayout(entry_row)

        entry_row.addWidget(QLabel("Nuevo filtro:"))
        self.new_filter_entry = QLineEdit()
        entry_row.addWidget(self.new_filter_entry)

        btn_add = QPushButton("Añadir")
        btn_add.clicked.connect(self.add_filter)
        entry_row.addWidget(btn_add)

        btn_delete = QPushButton("Eliminar seleccionado")
        btn_delete.clicked.connect(self.remove_filter)
        layout.addWidget(btn_delete)

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

        base_dir = os.path.dirname(mod_root)
        base_dir = os.path.dirname(base_dir)

        return os.path.join(base_dir, "logs", "error.log")

    # ---------------------------------------------------------
    # Cargar error.log
    # ---------------------------------------------------------
    def load_log(self):
        self.text.clear()

        log_path = self.get_error_log_path()

        if not log_path or not os.path.isfile(log_path):
            self.text.setPlainText("No se encontró error.log")
            return

        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:

                # Aplicar filtros configurados
                if any(filt.lower() in line.lower() for filt in self.filters):
                    continue

                self.insert_colored_line(line)

    # ---------------------------------------------------------
    # Insertar línea con color
    # ---------------------------------------------------------
    def insert_colored_line(self, line):
        fmt = QTextCharFormat()

        upper = line.upper()
        if "ERROR" in upper:
            fmt.setForeground(QColor("red"))
        elif "WARN" in upper:
            fmt.setForeground(QColor("orange"))
        elif "INFO" in upper:
            fmt.setForeground(QColor("gray"))

        cursor = self.text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(line, fmt)

    # ---------------------------------------------------------
    # Aplicar filtro manual
    # ---------------------------------------------------------
    def apply_filter(self):
        filtro = self.filter_entry.text().strip().lower()

        self.text.clear()

        log_path = self.get_error_log_path()
        if not log_path or not os.path.isfile(log_path):
            self.text.setPlainText("No se encontró error.log")
            return

        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:

                if any(filt.lower() in line.lower() for filt in self.filters):
                    continue

                if filtro in line.lower():
                    self.insert_colored_line(line)

    # ---------------------------------------------------------
    # Añadir filtro
    # ---------------------------------------------------------
    def add_filter(self):
        new = self.new_filter_entry.text().strip()
        if not new:
            return

        self.filters.append(new)
        save_filters(self.filters)

        self.listbox.addItem(new)
        self.new_filter_entry.clear()

    # ---------------------------------------------------------
    # Eliminar filtro
    # ---------------------------------------------------------
    def remove_filter(self):
        items = self.listbox.selectedItems()
        if not items:
            return

        item = items[0]
        value = item.text()

        self.filters.remove(value)
        save_filters(self.filters)

        self.listbox.takeItem(self.listbox.row(item))
