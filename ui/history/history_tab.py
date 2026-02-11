import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
)
from PyQt6.QtCore import QTimer

from map.map_loader import MapLoader
from .viewer import MapViewerQt


class HistoryTabQt(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app

        self.viewer = None
        self.map_loader = MapLoader(self.find_file)

        self.build_ui()

    def build_ui(self):
        self.layout = QVBoxLayout(self)

        self.info_label = QLabel("Mapa del juego")
        self.layout.addWidget(self.info_label)

        self.info_panel = QWidget()
        self.info_layout = QVBoxLayout(self.info_panel)

        self.label_id = QLabel("ID: -")
        self.label_name = QLabel("Nombre: -")
        self.label_color = QLabel("Color: -")
        self.label_type = QLabel("Tipo: -")

        self.info_layout.addWidget(self.label_id)
        self.info_layout.addWidget(self.label_name)
        self.info_layout.addWidget(self.label_color)
        self.info_layout.addWidget(self.label_type)
        self.info_layout.addStretch(1)

        btn_row = QHBoxLayout()
        btn_zoom_in = QPushButton("Zoom +")
        btn_zoom_out = QPushButton("Zoom -")
        btn_fit = QPushButton("Ajustar a ventana")
        btn_reset = QPushButton("Zoom 100%")

        btn_row.addWidget(btn_zoom_in)
        btn_row.addWidget(btn_zoom_out)
        btn_row.addWidget(btn_fit)
        btn_row.addWidget(btn_reset)

        self.map_container = QWidget()
        self.map_layout = QVBoxLayout(self.map_container)
        self.map_layout.addLayout(btn_row)

        main_row = QHBoxLayout()
        main_row.addWidget(self.info_panel)
        main_row.addWidget(self.map_container, 1)

        self.layout.addLayout(main_row)

        btn_zoom_in.clicked.connect(lambda: self.viewer.zoom_in() if self.viewer else None)
        btn_zoom_out.clicked.connect(lambda: self.viewer.zoom_out() if self.viewer else None)
        btn_fit.clicked.connect(lambda: self.viewer.fit_to_window() if self.viewer else None)
        btn_reset.clicked.connect(lambda: self.viewer.fit_to_window() if self.viewer else None)

    def find_file(self, relative_path):
        profile = self.app.current_profile
        if not profile:
            return None

        mod_root = profile.get("mod_root", "")
        game_root = profile.get("game_root", "")

        mod_path = os.path.join(mod_root, relative_path)
        if os.path.isfile(mod_path):
            return mod_path

        game_path = os.path.join(game_root, relative_path)
        if os.path.isfile(game_path):
            return game_path

        return None

    def refresh(self):
        if self.viewer:
            self.viewer.setParent(None)
            self.viewer = None

        path = self.find_file("map_data/provinces.png")

        if not path:
            self.info_label.setText("No se encontró provinces.png")
            return

        self.info_label.setText(f"Mapa cargado: {path}")

        self.map_loader = MapLoader(self.find_file)

        self.viewer = MapViewerQt(path, self.map_loader)
        self.viewer.province_clicked.connect(self.update_province_info)
        self.map_layout.addWidget(self.viewer)

        # ❌ ESTA LÍNEA ERA EL PROBLEMA
        # QTimer.singleShot(0, self.viewer.fit_to_window)

        # ✔ NO HACEMOS NADA AQUÍ
        # El viewer ya gestiona su propio fit en resizeEvent

    def update_province_info(self, province: dict):
        pid = province["id"]
        name = province["name"]
        r, g, b = province["color"]
        t = province["type"]

        self.label_id.setText(f"ID: {pid}")
        self.label_name.setText(f"Nombre: {name}")
        self.label_color.setText(f"Color: {r}, {g}, {b}")
        self.label_type.setText(f"Tipo: {t}")
