import tkinter as tk
import json
from ui.ui_main import ModToolApp


class App:
    def __init__(self):
        # Cargar módulos
        with open("data/modules.json", "r", encoding="utf-8") as f:
            self.modules = json.load(f)

        # Cargar archivos concretos
        with open("data/files.json", "r", encoding="utf-8") as f:
            self.files = json.load(f)

        self.current_profile = None

        root = tk.Tk()
        self.ui = ModToolApp(root, self)
        root.mainloop()


def main():
    App()


if __name__ == "__main__":
    main()
