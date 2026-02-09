import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
)
from PyQt6.QtGui import QPixmap, QWheelEvent, QPainter
from PyQt6.QtCore import Qt, QTimer


# ============================================================
#   VISOR PRINCIPAL DEL MAPA (zoom estable)
# ============================================================
class MapViewerQt(QGraphicsView):
    def __init__(self, image_path):
        super().__init__()

        # --- ESCENA PRINCIPAL ---
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        self.pixmap = QPixmap(image_path)
        self.map_item = QGraphicsPixmapItem(self.pixmap)
        self.scene.addItem(self.map_item)

        # Renderizado suave
        self.setRenderHints(
            QPainter.RenderHint.Antialiasing
            | QPainter.RenderHint.SmoothPixmapTransform
        )

        # Arrastre tipo Google Maps
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

        # Zoom centrado en el cursor
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        # Parámetros de zoom
        self.zoom_factor = 1.15
        self.current_scale = 1.0
        self.min_scale = 1.0
        self.max_scale = 8.0

    # ---------------------------------------------------------
    # ZOOM CON RUEDA
    # ---------------------------------------------------------
    def wheelEvent(self, event: QWheelEvent):
        if event.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    # ---------------------------------------------------------
    # AJUSTE A VENTANA
    # ---------------------------------------------------------
    def fit_to_window(self):
        if self.scene and not self.scene.itemsBoundingRect().isNull():
            self.resetTransform()
            self.fitInView(self.scene.itemsBoundingRect(), Qt.AspectRatioMode.KeepAspectRatio)

            s = self.transform().m11()
            self.current_scale = s
            self.min_scale = s

    # ---------------------------------------------------------
    # ZOOM 100%
    # ---------------------------------------------------------
    def zoom_reset(self):
        self.fit_to_window()

    # ---------------------------------------------------------
    # ZOOM +
    # ---------------------------------------------------------
    def zoom_in(self):
        if self.current_scale >= self.max_scale:
            return

        factor = self.zoom_factor
        if self.current_scale * factor > self.max_scale:
            factor = self.max_scale / self.current_scale

        self.scale(factor, factor)
        self.current_scale *= factor

    # ---------------------------------------------------------
    # ZOOM -
    # ---------------------------------------------------------
    def zoom_out(self):
        if self.current_scale <= self.min_scale:
            return

        factor = 1 / self.zoom_factor
        if self.current_scale * factor < self.min_scale:
            factor = self.min_scale / self.current_scale

        self.scale(factor, factor)
        self.current_scale *= factor


# ============================================================
#   PESTAÑA DE HISTORIA
# ============================================================
class HistoryTabQt(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app

        self.viewer = None

        self.build_ui()

    def build_ui(self):
        self.layout = QVBoxLayout(self)

        self.info_label = QLabel("Mapa del juego")
        self.layout.addWidget(self.info_label)

        # --- BOTONES DE ZOOM ---
        btn_row = QHBoxLayout()
        self.layout.addLayout(btn_row)

        btn_zoom_in = QPushButton("Zoom +")
        btn_zoom_out = QPushButton("Zoom -")
        btn_fit = QPushButton("Ajustar a ventana")
        btn_reset = QPushButton("Zoom 100%")

        btn_row.addWidget(btn_zoom_in)
        btn_row.addWidget(btn_zoom_out)
        btn_row.addWidget(btn_fit)
        btn_row.addWidget(btn_reset)

        btn_zoom_in.clicked.connect(lambda: self.viewer.zoom_in() if self.viewer else None)
        btn_zoom_out.clicked.connect(lambda: self.viewer.zoom_out() if self.viewer else None)
        btn_fit.clicked.connect(lambda: self.viewer.fit_to_window() if self.viewer else None)
        btn_reset.clicked.connect(lambda: self.viewer.zoom_reset() if self.viewer else None)

        # Contenedor del mapa
        self.map_container = QWidget()
        self.map_layout = QVBoxLayout(self.map_container)
        self.layout.addWidget(self.map_container)

    # ---------------------------------------------------------
    # Buscar archivo igual que en Tkinter
    # ---------------------------------------------------------
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

    # ---------------------------------------------------------
    # Refrescar cuando cambia el perfil
    # ---------------------------------------------------------
    def refresh(self):
        if self.viewer:
            self.viewer.setParent(None)
            self.viewer = None

        path = self.find_file("map_data/provinces.png")

        if not path:
            self.info_label.setText("No se encontró provinces.png")
            return

        self.info_label.setText(f"Mapa cargado: {path}")

        self.viewer = MapViewerQt(path)
        self.map_layout.addWidget(self.viewer)

        QTimer.singleShot(0, self.viewer.fit_to_window)
