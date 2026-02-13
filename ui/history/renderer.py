from PyQt6.QtGui import QImage
from PyQt6.QtCore import Qt


# ============================================================
# GENERAR MAPA RECOLOREADO HALF (reducción ×2)
# ============================================================
def generate_colored_map_half(original_img, lut):
    w = original_img.width()
    h = original_img.height()

    ptr = original_img.bits()
    ptr.setsize(original_img.sizeInBytes())
    data = bytes(ptr)

    out = bytearray(w * h * 3)

    for idx in range(w * h):
        j4 = idx * 4
        b = data[j4]
        g = data[j4 + 1]
        r = data[j4 + 2]

        color = (r << 16) | (g << 8) | b
        t = lut[color]
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
        else:
            out[j3] = 0; out[j3+1] = 0; out[j3+2] = 0

    # Convertir a BGR888
    bgr = bytearray(len(out))
    for i in range(0, len(out), 3):
        bgr[i] = out[i+2]
        bgr[i+1] = out[i+1]
        bgr[i+2] = out[i]

    qimg_hd = QImage(bgr, w, h, w * 3, QImage.Format.Format_BGR888)

    # Reducir ×2 (HALF)
    qimg_half = qimg_hd.scaled(
        w // 2,
        h // 2,
        Qt.AspectRatioMode.IgnoreAspectRatio,
        Qt.TransformationMode.SmoothTransformation
    )

    return qimg_half


# ============================================================
# GENERAR province_id_map (color → ID real)
# ============================================================
def generate_province_id_map(original_img, map_loader):
    w = original_img.width()
    h = original_img.height()

    ptr = original_img.bits()
    ptr.setsize(original_img.sizeInBytes())
    data = bytes(ptr)

    province_id_map = [0] * (w * h)
    color_to_id = map_loader.color_to_province_id

    for idx in range(w * h):
        j4 = idx * 4
        b = data[j4]
        g = data[j4 + 1]
        r = data[j4 + 2]

        color = (r << 16) | (g << 8) | b
        province_id_map[idx] = color_to_id.get(color, 0)

    return province_id_map


# ============================================================
# Bordes
# ============================================================
def generate_base_map_half(original_img, lut, province_id_map=None):
    w = original_img.width()
    h = original_img.height()

    # Leer RGBA del QImage
    ptr = original_img.bits()
    ptr.setsize(original_img.sizeInBytes())
    data = bytes(ptr)

    # Salida RGB
    out = bytearray(w * h * 3)

    # Si no se pasa province_id_map, lo generamos
    if province_id_map is None:
        # Import local para evitar dependencias circulares
        from .renderer import generate_province_id_map
        province_id_map = generate_province_id_map(original_img, lut)

    # 1. Pintar mapa base usando LUT
    for idx in range(w * h):
        j4 = idx * 4
        b = data[j4]
        g = data[j4 + 1]
        r = data[j4 + 2]

        color = (r << 16) | (g << 8) | b
        t = lut[color]
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
        else:
            out[j3] = 0; out[j3+1] = 0; out[j3+2] = 0

    # 2. Dibujar bordes de provincia
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            idx = y * w + x
            pid = province_id_map[idx]

            # Comparar con vecinos
            if (
                pid != province_id_map[idx - 1] or
                pid != province_id_map[idx + 1] or
                pid != province_id_map[idx - w] or
                pid != province_id_map[idx + w]
            ):
                j3 = idx * 3
                out[j3] = 0
                out[j3+1] = 0
                out[j3+2] = 0

    # Convertir a BGR888
    bgr = bytearray(len(out))
    for i in range(0, len(out), 3):
        bgr[i] = out[i+2]
        bgr[i+1] = out[i+1]
        bgr[i+2] = out[i]

    qimg_hd = QImage(bgr, w, h, w * 3, QImage.Format.Format_BGR888)

    # Reducir ×2 (HALF)
    qimg_half = qimg_hd.scaled(
        w // 2,
        h // 2,
        Qt.AspectRatioMode.IgnoreAspectRatio,
        Qt.TransformationMode.SmoothTransformation
    )

    return qimg_half

