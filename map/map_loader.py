import csv
import re
from map.map_types import SEA, LAKE, RIVER, IMPASSABLE, LAND

class MapLoader:
    def __init__(self, find_file_func):
        self.find_file = find_file_func

        self.province_by_color = {}
        self.sea = set()
        self.lakes = set()
        self.rivers = set()
        self.impassable = set()

        self.load_definition()
        self.load_default_map()

    # ------------------------------
    # Cargar definition.csv
    # ------------------------------
    def load_definition(self):
        path = self.find_file("map_data/definition.csv")
        if not path:
            print("ERROR: No se encontró definition.csv")
            return

        with open(path, encoding="utf-8") as f:
            reader = csv.reader(f, delimiter=";")
            for row in reader:
                if len(row) < 5:
                    continue

                try:
                    pid = int(row[0])
                    r = int(row[1])
                    g = int(row[2])
                    b = int(row[3])
                    name = row[4]
                except:
                    continue

                self.province_by_color[(r, g, b)] = {
                    "id": pid,
                    "name": name,
                    "type": LAND  # por defecto
                }

    # ------------------------------
    # Cargar default.map
    # ------------------------------
    def load_default_map(self):
        path = self.find_file("map_data/default.map")
        if not path:
            print("ERROR: No se encontró default.map")
            return

        text = open(path, encoding="utf-8").read()

        def extract(name):
            m = re.search(rf"{name}\s*=\s*\{{([^}}]+)\}}", text)
            if not m:
                return set()
            nums = re.findall(r"\d+", m.group(1))
            return set(map(int, nums))

        self.sea = extract("sea_zones")
        self.lakes = extract("lakes")
        self.rivers = extract("rivers")
        self.impassable = extract("impassable")

        # Asignar tipo a cada provincia
        for color, info in self.province_by_color.items():
            pid = info["id"]

            if pid in self.sea:
                info["type"] = SEA
            elif pid in self.lakes:
                info["type"] = LAKE
            elif pid in self.rivers:
                info["type"] = RIVER
            elif pid in self.impassable:
                info["type"] = IMPASSABLE
            else:
                info["type"] = LAND

    # ------------------------------
    # Obtener provincia por color
    # ------------------------------
    def get_province_from_color(self, r, g, b):
        return self.province_by_color.get((r, g, b), None)
