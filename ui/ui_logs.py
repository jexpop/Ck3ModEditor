import tkinter as tk
from tkinter import ttk


class LogsTab:
    def __init__(self, parent, app):
        self.app = app
        self.frame = ttk.Frame(parent)

        self.build_ui()

    # ---------------------------------------------------------
    # UI
    # ---------------------------------------------------------
    def build_ui(self):
        frame = self.frame

        tk.Label(
            frame,
            text="Los logs generados por el procesado se guardan en:\nlogs/<perfil>/<modulo>.log",
            justify="left"
        ).pack(pady=20)

        tk.Label(
            frame,
            text="Cada módulo genera su propio log con trazabilidad completa.",
            justify="left"
        ).pack(pady=5)

        tk.Label(
            frame,
            text="Esta pestaña puede ampliarse en el futuro para visualizar logs directamente.",
            justify="left",
            fg="#666"
        ).pack(pady=10)

    # ---------------------------------------------------------
    # REFRESH
    # ---------------------------------------------------------
    def refresh(self):
        # Actualmente no necesita refrescar nada,
        # pero dejamos el método preparado para futuras ampliaciones.
        pass
