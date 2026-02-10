import os
import json
import hashlib
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
)
from PyQt6.QtGui import QPixmap, QWheelEvent, QPainter, QImage, QColor
from PyQt6.QtCore import Qt, QTimer, pyqtSignal

from map.map_loader import MapLoader
from map.map_types import SEA, LAKE, RIVER, IMPASSABLE, LAND


# ============================================================
#   VISOR PRINCIPAL DEL MAPA (zoom + clic + LUT + caché)
# ============================================================
class MapViewerQt(QGraphicsView):
    province_clicked = pyqtSignal(dict)

    def __init__(self, image_path, map_loader: MapLoader):
        super().__init__()

        self.map_loader = map_loader
        self.image_path = image_path

        # Estado para arrastre con botón derecho
        self.right_button_dragging = False
        self.last_mouse_pos = None

        # --- ESCENA PRINCIPAL ---
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        # Mapa original (oculto)
        self.pixmap = QPixmap(image_path)
        self.map_item = QGraphicsPixmapItem(self.pixmap)
        self.scene.addItem(self.map_item)
        self.map_item.setVisible(False)

        # ======================================================
        # INICIALIZAR ORIGINAL_IMG *ANTES* DE GENERAR CACHÉ
        # ======================================================
        self.original_img = self.pixmap.toImage()
        self.w = self.original_img.width()
        self.h = self.original_img.height()

        ptr = self.original_img.bits()
        ptr.setsize(self.original_img.sizeInBytes())
        self.original_bytes = bytes(ptr)  # BGRA BGRA BGRA...

        # Capa recoloreada
        self.colored_layer = QGraphicsPixmapItem()
        self.colored_layer.setZValue(10)
        self.scene.addItem(self.colored_layer)

        # Capa de resaltado
        self.highlight_layer = QGraphicsPixmapItem()
        self.highlight_layer.setZValue(30)
        self.scene.addItem(self.highlight_layer)

        # Generar o cargar desde caché
        self.generate_or_load_cached_map()

        # Renderizado suave
        self.setRenderHints(
            QPainter.RenderHint.Antialiasing
            | QPainter.RenderHint.SmoothPixmapTransform
        )

        # NO usar drag automático de Qt
        self.setDragMode(QGraphicsView.DragMode.NoDrag)

        # Zoom centrado en el cursor
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        # Parámetros de zoom
        self.zoom_factor = 1.15
        self.current_scale = 1.0
        self.min_scale = 1.0
        self.max_scale = 8.0

    # ---------------------------------------------------------
    # HASH de archivo
    # ---------------------------------------------------------
    def file_hash(self, path):
        h = hashlib.md5()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    # ---------------------------------------------------------
    # Cargar o generar mapa base cacheado
    # ---------------------------------------------------------
    def generate_or_load_cached_map(self):
        base_dir = os.path.dirname(self.image_path)
        cache_dir = os.path.join(base_dir, "ck3_map_cache")
        os.makedirs(cache_dir, exist_ok=True)

        cache_png = os.path.join(cache_dir, "base_map.png")
        cache_meta = os.path.join(cache_dir, "base_map.meta")

        # Hashes actuales
        h_provinces = self.file_hash(self.image_path)
        h_def = self.file_hash(self.map_loader.definition_path)
        h_map = self.file_hash(self.map_loader.default_map_path)

        # Intentar cargar caché
        if os.path.isfile(cache_png) and os.path.isfile(cache_meta):
            try:
                meta = json.load(open(cache_meta, "r", encoding="utf-8"))
                if (
                    meta.get("provinces_hash") == h_provinces
                    and meta.get("definition_hash") == h_def
                    and meta.get("default_map_hash") == h_map
                ):
                    print("Mapa base cargado desde caché")
                    self.colored_layer.setPixmap(QPixmap(cache_png))
                    return
            except Exception:
                pass

        # Si llegamos aquí → regenerar
        print("Generando mapa base (no hay caché válida)...")
        qimg = self.generate_colored_map()

        # Guardar en caché
        qimg.save(cache_png)

        json.dump(
            {
                "provinces_hash": h_provinces,
                "definition_hash": h_def,
                "default_map_hash": h_map,
            },
            open(cache_meta, "w", encoding="utf-8"),
            indent=2,
        )

        print("Mapa base guardado en caché")

    # ---------------------------------------------------------
    # Generar mapa recoloreado (solo si no hay caché)
    # ---------------------------------------------------------
    def generate_colored_map(self):
        img = self.original_img
        w, h = self.w, self.h

        ptr = img.bits()
        ptr.setsize(img.sizeInBytes())
        data = bytes(ptr)

        color_ids = [0] * (w * h)
        lut = self.map_loader.lut
        out = bytearray(w * h * 3)

        # Extraer colores originales + recolorear
        for idx in range(w * h):
            j4 = idx * 4
            b = data[j4]
            g = data[j4 + 1]
            r = data[j4 + 2]

            color_ids[idx] = (r << 16) | (g << 8) | b

            t = lut[color_ids[idx]]
            j3 = idx * 3

            if t == 1:      # mar
                out[j3] = 80; out[j3+1] = 120; out[j3+2] = 255
            elif t == 2:    # lago
                out[j3] = 60; out[j3+1] = 100; out[j3+2] = 230
            elif t == 3:    # río
                out[j3] = 100; out[j3+1] = 150; out[j3+2] = 255
            elif t == 4:    # impassable
                out[j3] = 120; out[j3+1] = 120; out[j3+2] = 120
            elif t == 0:    # tierra
                out[j3] = 235; out[j3+1] = 180; out[j3+2] = 60
            elif t == 5:    # unknown
                out[j3] = 0; out[j3+1] = 0; out[j3+2] = 0
            else:
                out[j3] = 0; out[j3+1] = 0; out[j3+2] = 0

        # ---------------------------------------------------------
        # BORDES usando color original
        # ---------------------------------------------------------
        border_r, border_g, border_b = 0, 0, 0

        for y in range(h):
            base = y * w
            for x in range(w):
                idx = base + x
                j3 = idx * 3

                r2 = out[j3]
                g2 = out[j3+1]
                b2 = out[j3+2]

                if not (r2 == 235 and g2 == 180 and b2 == 60):
                    continue

                cid = color_ids[idx]
                is_border = False

                if x < w - 1:
                    if color_ids[idx + 1] != cid:
                        is_border = True

                if y < h - 1:
                    if color_ids[idx + w] != cid:
                        is_border = True

                if is_border:
                    out[j3] = border_r
                    out[j3+1] = border_g
                    out[j3+2] = border_b

        # Convertir a BGR
        bgr = bytearray(len(out))
        for i in range(0, len(out), 3):
            bgr[i] = out[i+2]
            bgr[i+1] = out[i+1]
            bgr[i+2] = out[i]

        qimg = QImage(bgr, w, h, w * 3, QImage.Format.Format_BGR888)
        self.colored_layer.setPixmap(QPixmap.fromImage(qimg))
        return qimg

    # ---------------------------------------------------------
    # RESALTAR PROVINCIA (rápido, basado en color original)
    # ---------------------------------------------------------
    def highlight_province(self, province):
        if not province or not province["color"]:
            self.highlight_layer.setPixmap(QPixmap())
            return

        target_r, target_g, target_b = province["color"]
        w, h = self.w, self.h
        data = self.original_bytes

        # Imagen ARGB vacía
        highlight = bytearray(w * h * 4)

        # Color A1 amarillo semitransparente
        hr, hg, hb, ha = 255, 255, 0, 120

        for idx in range(w * h):
            j4 = idx * 4
            b = data[j4]
            g = data[j4 + 1]
            r = data[j4 + 2]

            if r == target_r and g == target_g and b == target_b:
                k = idx * 4
                highlight[k] = hb
                highlight[k+1] = hg
                highlight[k+2] = hr
                highlight[k+3] = ha

        qimg = QImage(highlight, w, h, w * 4, QImage.Format.Format_ARGB32)
        self.highlight_layer.setPixmap(QPixmap.fromImage(qimg))

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

    # ---------------------------------------------------------
    # RATÓN: clic izquierdo = seleccionar, derecho = arrastrar
    # ---------------------------------------------------------
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self.right_button_dragging = True
            self.last_mouse_pos = event.position()
            super().mousePressEvent(event)
            return

        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position()
            scene_pos = self.mapToScene(pos.toPoint())
            x = int(scene_pos.x())
            y = int(scene_pos.y())

            if 0 <= x < self.pixmap.width() and 0 <= y < self.pixmap.height():
                img = self.original_img
                c = img.pixelColor(x, y)
                r, g, b = c.red(), c.green(), c.blue()

                province = self.map_loader.get_province_from_color(r, g, b)
                if province:
                    self.province_clicked.emit(province)
                    self.highlight_province(province)

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.right_button_dragging and self.last_mouse_pos is not None:
            delta = event.position() - self.last_mouse_pos
            self.last_mouse_pos = event.position()

            dx = int(delta.x())
            dy = int(delta.y())

            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - dx
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - dy
            )
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self.right_button_dragging = False
            self.last_mouse_pos = None
            super().mouseReleaseEvent(event)
            return

        super().mouseReleaseEvent(event)


# ============================================================
#   PESTAÑA DE HISTORIA
# ============================================================
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

        # --- PANEL IZQUIERDO DE INFORMACIÓN ---
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

        # --- BOTONES DE ZOOM ---
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

        # Layout principal horizontal: panel izq + mapa
        main_row = QHBoxLayout()
        main_row.addWidget(self.info_panel)
        main_row.addWidget(self.map_container, 1)

        self.layout.addLayout(main_row)

        # Conexiones de botones
        btn_zoom_in.clicked.connect(lambda: self.viewer.zoom_in() if self.viewer else None)
        btn_zoom_out.clicked.connect(lambda: self.viewer.zoom_out() if self.viewer else None)
        btn_fit.clicked.connect(lambda: self.viewer.fit_to_window() if self.viewer else None)
        btn_reset.clicked.connect(lambda: self.viewer.zoom_reset() if self.viewer else None)

    # ---------------------------------------------------------
    # Buscar archivo primero en mod, luego en juego
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

        # Recargar datos de mapa por si el perfil ha cambiado
        self.map_loader = MapLoader(self.find_file)

        self.viewer = MapViewerQt(path, self.map_loader)
        self.viewer.province_clicked.connect(self.update_province_info)
        self.map_layout.addWidget(self.viewer)

        QTimer.singleShot(0, self.viewer.fit_to_window)

    # ---------------------------------------------------------
    # Actualizar panel izquierdo con info de provincia
    # ---------------------------------------------------------
    def update_province_info(self, province: dict):
        pid = province["id"]
        name = province["name"]
        r, g, b = province["color"]
        t = province["type"]

        self.label_id.setText(f"ID: {pid}")
        self.label_name.setText(f"Nombre: {name}")
        self.label_color.setText(f"Color: {r}, {g}, {b}")
        self.label_type.setText(f"Tipo: {t}")
