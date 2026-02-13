import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout
)

from map.map_loader import MapLoader
from .viewer import MapViewerQt

from ui.history.title_history_loader import load_all_title_history, get_holder_at_year


class HistoryTabQt(QWidget):
    def __init__(self, app, mode="base"):
        super().__init__()
        self.app = app
        self.mode = mode   # "base" o "mod"

        self.viewer = None
        self.map_loader = None
        self.title_history = {}

        self.build_ui()

    # ---------------------------------------------------------
    # FIND_FILE según la vista
    # ---------------------------------------------------------
    def find_file_base(self, relative_path):
        game_root = self.app.current_profile["game_root"]
        full = os.path.join(game_root, relative_path)
        return full if os.path.isfile(full) else None

    def find_file_mod(self, relative_path):
        profile = self.app.current_profile
        mod_root = profile["mod_root"]
        game_root = profile["game_root"]

        mod_path = os.path.join(mod_root, relative_path)
        if os.path.isfile(mod_path):
            return mod_path

        game_path = os.path.join(game_root, relative_path)
        if os.path.isfile(game_path):
            return game_path

        return None

    # ---------------------------------------------------------
    # UI
    # ---------------------------------------------------------
    def build_ui(self):
        self.layout = QVBoxLayout(self)

        self.info_label = QLabel("Mapa del juego")
        self.layout.addWidget(self.info_label)

        # Panel izquierdo
        self.info_panel = QWidget()
        self.info_layout = QVBoxLayout(self.info_panel)

        self.label_id = QLabel("ID: -")
        self.label_barony = QLabel("Baronía: -")
        self.label_color = QLabel("Color: -")
        self.label_type = QLabel("Tipo: -")
        self.label_holder = QLabel("Holder: -")

        self.info_layout.addWidget(self.label_id)
        self.info_layout.addWidget(self.label_barony)
        self.info_layout.addWidget(self.label_color)
        self.info_layout.addWidget(self.label_type)
        self.info_layout.addWidget(self.label_holder)
        self.info_layout.addStretch(1)

        # Botones de zoom
        btn_row = QHBoxLayout()
        btn_zoom_in = QPushButton("Zoom +")
        btn_zoom_out = QPushButton("Zoom -")
        btn_fit = QPushButton("Ajustar a ventana")
        btn_reset = QPushButton("Zoom 100%")

        btn_row.addWidget(btn_zoom_in)
        btn_row.addWidget(btn_zoom_out)
        btn_row.addWidget(btn_fit)
        btn_row.addWidget(btn_reset)

        # Contenedor del mapa
        self.map_container = QWidget()
        self.map_layout = QVBoxLayout(self.map_container)
        self.map_layout.addLayout(btn_row)

        # Layout principal
        main_row = QHBoxLayout()
        main_row.addWidget(self.info_panel)
        main_row.addWidget(self.map_container, 1)

        self.layout.addLayout(main_row)

        # Conexiones
        btn_zoom_in.clicked.connect(lambda: self.viewer.zoom_in() if self.viewer else None)
        btn_zoom_out.clicked.connect(lambda: self.viewer.zoom_out() if self.viewer else None)
        btn_fit.clicked.connect(lambda: self.viewer.fit_to_window() if self.viewer else None)
        btn_reset.clicked.connect(lambda: self.viewer.fit_to_window() if self.viewer else None)

    # ---------------------------------------------------------
    # REFRESH según la vista
    # ---------------------------------------------------------
    def refresh(self):
        if self.viewer:
            self.viewer.setParent(None)
            self.viewer = None

        profile = self.app.current_profile
        game_root = profile["game_root"]
        mod_root = profile["mod_root"]

        # Vista BASE
        if self.mode == "base":
            find_file = self.find_file_base
            history_root = game_root
            self.info_label.setText("Vista: Juego Base")

        # Vista MOD
        else:
            find_file = self.find_file_mod
            history_root = mod_root
            self.info_label.setText("Vista: Mod")

        # Cargar mapa
        path = find_file("map_data/provinces.png")
        if not path:
            self.info_label.setText("No se encontró provinces.png")
            return

        self.map_loader = MapLoader(find_file)

        # Cargar historia de títulos
        self.title_history = load_all_title_history(history_root)

        # Crear viewer
        self.viewer = MapViewerQt(path, self.map_loader)
        self.viewer.province_clicked.connect(self.update_province_info)
        self.map_layout.addWidget(self.viewer)

    # ---------------------------------------------------------
    # CLICK EN PROVINCIA
    # ---------------------------------------------------------
    def update_province_info(self, province: dict):
        try:
            pid = province["id"]
            r, g, b = province["color"]
            t = province["type"]

            #print("PID:", pid)

            # Datos básicos
            self.label_id.setText(f"ID: {pid}")
            self.label_color.setText(f"Color: {r}, {g}, {b}")
            self.label_type.setText(f"Tipo: {t}")

            # -----------------------------
            # Resolver baronía (b_*)
            # -----------------------------
            barony = self.map_loader.get_title_from_province_id(pid)
            self.label_barony.setText(f"Baronía: {barony}")
            
            #print("Baronía encontrada:", barony)

            if not barony:
                self.label_holder.setText("Holder: (sin baronía)")
                return

            # -----------------------------
            # Resolver condado (c_*)
            # -----------------------------
            county = self.map_loader.get_county_from_barony(barony)

            if not county:
                self.label_holder.setText("Holder: (sin condado)")
                return

            # Año según modo
            year = 1200 if self.mode == "base" else 11200

            # -----------------------------
            # Buscar holder
            # -----------------------------
            if county in self.title_history:
                holder = get_holder_at_year(self.title_history[county], year)
                self.label_holder.setText(f"Holder en {year}: {holder}")
            else:
                self.label_holder.setText(f"Holder en {year}: (sin datos)")

        except Exception as e:
            print("ERROR EN update_province_info:", e)
