import os
import json
from PyQt6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem
)
from PyQt6.QtGui import QPixmap, QWheelEvent, QPainter
from PyQt6.QtCore import Qt, QRectF, pyqtSignal

from .utils import file_hash
from .renderer import generate_colored_map_half, generate_province_id_map
from .highlighter import generate_highlight_half_from_idmap


class MapViewerQt(QGraphicsView):
    province_clicked = pyqtSignal(dict)

    def __init__(self, image_path, map_loader):
        super().__init__()

        self.map_loader = map_loader
        self.image_path = image_path

        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.setCursor(Qt.CursorShape.ArrowCursor)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)

        self.pixmap = QPixmap(image_path)
        self.original_img = self.pixmap.toImage()
        self.w = self.original_img.width()
        self.h = self.original_img.height()

        self.province_id_map = generate_province_id_map(self.original_img, self.map_loader)

        self.highlight_cache = {}

        self.colored_layer = QGraphicsPixmapItem()
        self.colored_layer.setZValue(10)
        self.scene.addItem(self.colored_layer)

        self.highlight_layer = QGraphicsPixmapItem()
        self.highlight_layer.setZValue(30)
        self.scene.addItem(self.highlight_layer)

        self.generate_or_load_cached_map()

        half_w = self.colored_layer.pixmap().width()
        half_h = self.colored_layer.pixmap().height()
        self.scene.setSceneRect(QRectF(0, 0, half_w, half_h))

        self.setRenderHints(
            QPainter.RenderHint.Antialiasing
            | QPainter.RenderHint.SmoothPixmapTransform
        )
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        self.base_scale = None
        self.dragging = False
        self.last_pos = None

    def resizeEvent(self, event):
        super().resizeEvent(event)

        if self.base_scale is None:
            self.fit_to_window()
            self.base_scale = self.transform().m11()

    def generate_or_load_cached_map(self):
        base_dir = os.path.dirname(self.image_path)
        cache_dir = os.path.join(base_dir, "ck3_map_cache")
        os.makedirs(cache_dir, exist_ok=True)

        cache_png = os.path.join(cache_dir, "base_map_half.png")
        cache_meta = os.path.join(cache_dir, "base_map_half.meta")

        h_provinces = file_hash(self.image_path)
        h_def = file_hash(self.map_loader.definition_path)
        h_map = file_hash(self.map_loader.default_map_path)

        if os.path.isfile(cache_png) and os.path.isfile(cache_meta):
            try:
                meta = json.load(open(cache_meta, "r", encoding="utf-8"))
                if (
                    meta.get("provinces_hash") == h_provinces
                    and meta.get("definition_hash") == h_def
                    and meta.get("default_map_hash") == h_map
                ):
                    self.colored_layer.setPixmap(QPixmap(cache_png))
                    return
            except Exception:
                pass

        qimg_half = generate_colored_map_half(self.original_img, self.map_loader.lut)
        qimg_half.save(cache_png)

        json.dump(
            {
                "provinces_hash": h_provinces,
                "definition_hash": h_def,
                "default_map_hash": h_map,
            },
            open(cache_meta, "w", encoding="utf-8"),
            indent=2,
        )

        self.colored_layer.setPixmap(QPixmap.fromImage(qimg_half))

    def fit_to_window(self):
        self.resetTransform()
        self.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def highlight_province(self, province):
        pid = province["id"]

        if pid in self.highlight_cache:
            self.highlight_layer.setPixmap(self.highlight_cache[pid])
            return

        img = generate_highlight_half_from_idmap(
            self.province_id_map,
            self.w,
            self.h,
            pid
        )

        pix = QPixmap.fromImage(img)
        self.highlight_cache[pid] = pix
        self.highlight_layer.setPixmap(pix)

    def wheelEvent(self, event: QWheelEvent):
        if event.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def zoom_in(self):
        if self.base_scale is None:
            return

        scale = self.transform().m11()

        if scale > self.base_scale * 30:
            return

        self.scale(1.15, 1.15)

    def zoom_out(self):
        if self.base_scale is None:
            return

        scale = self.transform().m11()

        # Si el siguiente paso se pasaría del mínimo, ajustamos justo a base_scale
        next_scale = scale / 1.15
        if next_scale <= self.base_scale:
            factor = self.base_scale / scale
            self.scale(factor, factor)
            return

        self.scale(1/1.15, 1/1.15)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position()
            scene_pos = self.mapToScene(pos.toPoint())

            x = int(scene_pos.x()) * 2
            y = int(scene_pos.y()) * 2

            if 0 <= x < self.w and 0 <= y < self.h:
                idx = y * self.w + x
                province_id = self.province_id_map[idx]

                if province_id > 0:
                    province = self.map_loader.get_province_from_id(province_id)
                    if province:
                        self.province_clicked.emit(province)
                        self.highlight_province(province)

            return

        if event.button() == Qt.MouseButton.RightButton:
            self.dragging = True
            self.last_pos = event.position()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.dragging and self.last_pos is not None:
            delta = event.position() - self.last_pos
            self.last_pos = event.position()

            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - int(delta.x())
            )
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - int(delta.y())
            )
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            self.dragging = False
            self.last_pos = None
            self.setCursor(Qt.CursorShape.ArrowCursor)

        super().mouseReleaseEvent(event)
