import sys
import json
from PyQt6.QtWidgets import QApplication
from ui.ui_main_qt import ModToolAppQt


class AppQt:
    def __init__(self):
        # Cargar módulos
        with open("data/modules.json", "r", encoding="utf-8") as f:
            self.modules = json.load(f)

        # Cargar archivos concretos
        with open("data/files.json", "r", encoding="utf-8") as f:
            self.files = json.load(f)

        self.current_profile = None

        # Crear aplicación Qt
        self.qt_app = QApplication(sys.argv)

        # Crear ventana principal Qt
        self.ui = ModToolAppQt(self)

        # Mostrar directamente maximizada (sin warnings)
        self.ui.showMaximized()

        # Ejecutar loop Qt
        sys.exit(self.qt_app.exec())


def main():
    AppQt()


if __name__ == "__main__":
    main()
