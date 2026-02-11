import csv
import re
import os
import json
import hashlib
from PIL import Image
from map.map_types import SEA, LAKE, RIVER, IMPASSABLE, LAND, UNKNOWN


class MapLoader:
    def __init__(self, find_file_func):
        self.find_file = find_file_func

        self.province_by_color = {}
        self.sea = set()
        self.lakes = set()
        self.rivers = set()
        self.impassable = set()
        self.impassable_seas = set()
        self.lut = None

        # Rutas
        self.definition_path = self.find_file("map_data/definition.csv")
        self.default_map_path = self.find_file("map_data/default.map")
        self.provinces_png_path = self.find_file("map_data/provinces.png")

        if not self.definition_path:
            raise FileNotFoundError("No se encontró map_data/definition.csv")

        if not self.default_map_path:
            raise FileNotFoundError("No se encontró map_data/default.map")

        if not self.provinces_png_path:
            raise FileNotFoundError("No se encontró map_data/provinces.png")

        # Cargar colores del provinces.png
        self.load_all_colors()

        # Cargar definition.csv
        self.load_definition()

        # Crear mapa color → ID de provincia
        self.color_to_province_id = {}
        for prov in self.provinces.values():
            r, g, b = prov["color"]
            color = (r << 16) | (g << 8) | b
            self.color_to_province_id[color] = prov["id"]

        print("TEST color_to_province_id size:", len(self.color_to_province_id))

        # Marcar colores no definidos como UNKNOWN
        self.mark_unknown_colors()

        # Cargar default.map
        self.load_default_map()

        # Construir LUT
        self.build_or_load_lut()

    # ------------------------------
    # Leer todos los colores del provinces.png
    # ------------------------------
    def load_all_colors(self):
        img = Image.open(self.provinces_png_path).convert("RGB")
        pixels = img.load()

        self.all_colors_in_png = set()

        for y in range(img.height):
            for x in range(img.width):
                self.all_colors_in_png.add(pixels[x, y])

    # ------------------------------
    # Cargar definition.csv
    # ------------------------------
    def load_definition(self):
        self.provinces = {}

        with open(self.definition_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()

                if not line or line.startswith("#"):
                    continue

                parts = line.split(";")

                if len(parts) < 5:
                    continue

                try:
                    pid = int(parts[0])
                    r = int(parts[1])
                    g = int(parts[2])
                    b = int(parts[3])
                    name = parts[4].strip()
                except:
                    continue

                if pid == 0:
                    continue

                self.provinces[pid] = {
                    "id": pid,
                    "color": (r, g, b),
                    "name": name,
                    "type": None,
                }

                self.province_by_color[(r, g, b)] = self.provinces[pid]

        print("TEST provinces loaded:", len(self.provinces))

    # ------------------------------
    # Marcar colores no definidos como UNKNOWN
    # ------------------------------
    def mark_unknown_colors(self):
        for color in self.all_colors_in_png:
            if color not in self.province_by_color:
                self.province_by_color[color] = {
                    "id": None,
                    "color": color,
                    "name": "UNKNOWN",
                    "type": UNKNOWN,
                }

    # ------------------------------
    # Cargar default.map (LIST + RANGE)
    # ------------------------------
    def load_default_map(self):
        path = self.default_map_path
        text = open(path, encoding="utf-8").read()

        def extract(name):
            results = set()

            pattern = rf"{name}\s*=\s*(LIST|RANGE)?\s*\{{([^}}]+)\}}"
            matches = re.findall(pattern, text, flags=re.MULTILINE)

            for block_type, block_content in matches:
                lines = block_content.splitlines()

                for line in lines:
                    line = line.split("#")[0].strip()
                    if not line:
                        continue

                    nums = list(map(int, re.findall(r"\d+", line)))
                    if not nums:
                        continue

                    if block_type == "RANGE" and len(nums) == 2:
                        a, b = nums
                        for x in range(a, b + 1):
                            results.add(x)
                        continue

                    for n in nums:
                        results.add(n)

            return results

        self.sea = extract("sea_zones")
        self.lakes = extract("lakes")
        self.rivers = extract("river_provinces")
        self.impassable = extract("impassable_mountains")
        self.impassable_seas = extract("impassable_seas")

        print("TEST sea:", len(self.sea))
        print("TEST lakes:", len(self.lakes))
        print("TEST rivers:", len(self.rivers))

        in_default = (
            self.sea
            | self.lakes
            | self.rivers
            | self.impassable
            | self.impassable_seas
        )

        for (r, g, b), info in self.province_by_color.items():
            pid = info["id"]

            if pid is None:
                info["type"] = UNKNOWN
                continue

            if pid in self.sea:
                info["type"] = SEA
            elif pid in self.lakes:
                info["type"] = LAKE
            elif pid in self.rivers:
                info["type"] = RIVER
            elif pid in self.impassable or pid in self.impassable_seas:
                info["type"] = IMPASSABLE
            elif pid not in in_default:
                info["type"] = LAND
            else:
                info["type"] = UNKNOWN

    # ------------------------------
    # Hash de archivo
    # ------------------------------
    def _file_hash(self, path):
        if not path or not os.path.isfile(path):
            return None
        h = hashlib.md5()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    # ------------------------------
    # Construir o cargar LUT
    # ------------------------------
    def build_or_load_lut(self):
        base_dir = os.path.dirname(self.definition_path)
        cache_dir = os.path.join(base_dir, "ck3_map_cache")
        os.makedirs(cache_dir, exist_ok=True)

        lut_bin_path = os.path.join(cache_dir, "lut_types.bin")
        lut_meta_path = os.path.join(cache_dir, "lut_types.meta")

        def_hash = self._file_hash(self.definition_path)
        map_hash = self._file_hash(self.default_map_path)

        if os.path.isfile(lut_bin_path) and os.path.isfile(lut_meta_path):
            try:
                meta = json.load(open(lut_meta_path, "r", encoding="utf-8"))
                if meta.get("definition_hash") == def_hash and meta.get("default_map_hash") == map_hash:
                    data = open(lut_bin_path, "rb").read()
                    if len(data) == 16_777_216:
                        self.lut = bytearray(data)
                        print("LUT cargada desde caché")
                        return
            except:
                pass

        print("Construyendo LUT nueva...")
        self.lut = self._build_lut_in_memory()

        with open(lut_bin_path, "wb") as f:
            f.write(self.lut)

        with open(lut_meta_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "definition_hash": def_hash,
                    "default_map_hash": map_hash,
                },
                f,
                indent=2,
            )

        print("LUT guardada en caché")

    # ------------------------------
    # Construir LUT en memoria
    # ------------------------------
    def _build_lut_in_memory(self):
        lut = bytearray(16_777_216)

        for (r, g, b), info in self.province_by_color.items():
            cid = (r << 16) | (g << 8) | b
            t = info["type"]

            if t == SEA:
                lut[cid] = 1
            elif t == LAKE:
                lut[cid] = 2
            elif t == RIVER:
                lut[cid] = 3
            elif t == IMPASSABLE:
                lut[cid] = 4
            elif t == LAND:
                lut[cid] = 0
            elif t == UNKNOWN:
                lut[cid] = 5

        return lut

    # ------------------------------
    # Obtener provincia por color
    # ------------------------------
    def get_province_from_color(self, r, g, b):
        return self.province_by_color.get((r, g, b), None)

    # ------------------------------
    # Obtener provincia por ID
    # ------------------------------
    def get_province_from_id(self, pid):
        return self.provinces.get(pid)
