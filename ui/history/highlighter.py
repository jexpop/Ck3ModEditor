from PyQt6.QtGui import QImage
from PyQt6.QtCore import Qt


def generate_highlight_half_from_idmap(province_id_map, w: int, h: int, target_id: int):
    highlight_hd = bytearray(w * h * 4)

    hr, hg, hb, ha = 255, 255, 0, 120

    for idx in range(w * h):
        if province_id_map[idx] == target_id:
            k = idx * 4
            highlight_hd[k] = hb
            highlight_hd[k+1] = hg
            highlight_hd[k+2] = hr
            highlight_hd[k+3] = ha

    qimg_hd = QImage(highlight_hd, w, h, w * 4, QImage.Format.Format_ARGB32)

    qimg_half = qimg_hd.scaled(
        w // 2,
        h // 2,
        Qt.AspectRatioMode.IgnoreAspectRatio,
        Qt.TransformationMode.SmoothTransformation
    )

    return qimg_half
