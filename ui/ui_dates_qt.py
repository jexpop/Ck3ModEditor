from PyQt6.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout,
    QTabWidget, QScrollArea, QGridLayout, QCheckBox, QMessageBox
)
from PyQt6.QtCore import Qt

from core.processor import process_module
from core.defines import read_end_date, read_mod_end_date, write_end_date


class DatesTabQt(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app

        self.module_vars = {}

        self.build_ui()

    # ---------------------------------------------------------
    # UI
    # ---------------------------------------------------------
    def build_ui(self):
        layout = QVBoxLayout(self)

        # Notebook interno
        self.sub_tabs = QTabWidget()
        layout.addWidget(self.sub_tabs)

        # Subpestañas
        self.tab_process = QWidget()
        self.tab_logs = QWidget()

        self.sub_tabs.addTab(self.tab_process, "Procesado")
        self.sub_tabs.addTab(self.tab_logs, "Logs")

        self.build_process_tab()
        self.build_logs_tab()

    # ---------------------------------------------------------
    # SUBPESTAÑA: PROCESADO
    # ---------------------------------------------------------
    def build_process_tab(self):
        layout = QVBoxLayout(self.tab_process)

        # Offset
        layout.addWidget(QLabel("Offset de año:"))
        self.entry_offset = QLineEdit()
        layout.addWidget(self.entry_offset)

        # END_DATE
        layout.addWidget(QLabel("Fecha final del juego (END_DATE):"))
        self.entry_end_date = QLineEdit()
        layout.addWidget(self.entry_end_date)

        self.label_end_date_source = QLabel("")
        self.label_end_date_source.setStyleSheet("color: gray;")
        layout.addWidget(self.label_end_date_source)

        btn_save_end = QPushButton("Guardar END_DATE en el mod")
        btn_save_end.clicked.connect(self.save_end_date)
        layout.addWidget(btn_save_end)

        # ---------------------------------------------------------
        # MÓDULOS A PROCESAR (SCROLL + GRID)
        # ---------------------------------------------------------
        layout.addWidget(QLabel("Módulos a procesar:"))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)

        self.modules_container = QWidget()
        self.modules_layout = QGridLayout(self.modules_container)
        scroll.setWidget(self.modules_container)

        # Botón procesar
        btn_process = QPushButton("Procesar")
        btn_process.clicked.connect(self.run_processing)
        layout.addWidget(btn_process)

    # ---------------------------------------------------------
    # SUBPESTAÑA: LOGS
    # ---------------------------------------------------------
    def build_logs_tab(self):
        layout = QVBoxLayout(self.tab_logs)
        layout.addWidget(QLabel("Los logs se guardan en logs/<perfil>/<modulo>.log"))

    # ---------------------------------------------------------
    # REFRESH
    # ---------------------------------------------------------
    def refresh(self):
        profile = self.app.current_profile
        if not profile:
            return

        # Offset
        self.entry_offset.setText(str(profile["year_offset"]))

        # END_DATE
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

        self.entry_end_date.setText(final_date)
        self.label_end_date_source.setText(f"Origen: {source}")

        # Módulos
        self.load_modules_for_process()

    # ---------------------------------------------------------
    # MÓDULOS PARA PROCESADO
    # ---------------------------------------------------------
    def load_modules_for_process(self):
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

        self.module_vars = {}

        row = 0
        col = 0
        cols = 8

        for module_name in sorted(game_modules.keys()):
            default_active = module_name in profile["modules"]

            chk = QCheckBox(module_name)
            chk.setChecked(default_active)

            self.modules_layout.addWidget(chk, row, col)
            self.module_vars[module_name] = chk

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
            QMessageBox.critical(self, "Error", "Selecciona un perfil")
            return

        try:
            offset = int(self.entry_offset.text())
        except ValueError:
            QMessageBox.critical(self, "Error", "Offset inválido")
            return

        # Guardar offset
        profile["year_offset"] = offset
        from utils.profile_ops import update_profile
        update_profile(profile)

        game_root = profile["game_root"]
        mod_root = profile["mod_root"]
        backup_root = profile["backup_root"]
        game_key = profile["game"]
        profile_name = profile["name"]

        for module_name, chk in self.module_vars.items():
            if chk.isChecked():
                process_module(
                    game_key,
                    module_name,
                    game_root,
                    mod_root,
                    backup_root,
                    offset,
                    profile_name
                )

        QMessageBox.information(self, "OK", "Procesado completado")

    # ---------------------------------------------------------
    # END_DATE
    # ---------------------------------------------------------
    def save_end_date(self):
        profile = self.app.current_profile
        if not profile:
            QMessageBox.critical(self, "Error", "Selecciona un perfil")
            return

        new_date = self.entry_end_date.text().strip()
        if not new_date:
            QMessageBox.critical(self, "Error", "Fecha inválida")
            return

        ok = write_end_date(
            game_root=profile["game_root"],
            mod_root=profile["mod_root"],
            backup_root=profile["backup_root"],
            new_date=new_date
        )

        if ok:
            QMessageBox.information(self, "OK", "END_DATE guardado en el mod")
        else:
            QMessageBox.critical(self, "Error", "No se pudo guardar END_DATE")
