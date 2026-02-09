import os
import json

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QTreeWidget, QTreeWidgetItem, QTextEdit, QTabWidget, QMessageBox
)
from PyQt6.QtGui import QColor, QTextCharFormat, QTextCursor
from PyQt6.QtCore import Qt

from core.validation import (
    collect_module_files,
    compare_file_contents
)


def list_files_recursive(base_path):
    result = []
    if not os.path.isdir(base_path):
        return result

    for root, dirs, files in os.walk(base_path):
        for f in files:
            full = os.path.join(root, f)
            rel = os.path.relpath(full, base_path)
            result.append(rel.replace("\\", "/"))

    return result


class ValidationTabQt(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app

        # Para detalles de validación total
        self.module_full_results = []   # (module_name, estado_mod, estado_game, detalles_mod, detalles_game)
        self.file_full_results = []     # (file_key, estado_mod, diff_mod, estado_game, diff_game)

        # Para diff puntual
        self.current_diff_lines = None

        self.build_ui()

    # ---------------------------------------------------------
    # UI general
    # ---------------------------------------------------------
    def build_ui(self):
        layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # ---------------- MÓDULOS ----------------
        self.modules_tab = QWidget()
        self.tabs.addTab(self.modules_tab, "Módulos")
        self.build_modules_tab()

        # ---------------- ARCHIVOS ----------------
        self.files_tab = QWidget()
        self.tabs.addTab(self.files_tab, "Archivos")
        self.build_files_tab()

    # =========================================================
    # MÓDULOS
    # =========================================================
    def build_modules_tab(self):
        layout = QVBoxLayout(self.modules_tab)

        self.modules_subtabs = QTabWidget()
        layout.addWidget(self.modules_subtabs)

        # ---- Por módulo ----
        self.mod_single_tab = QWidget()
        self.modules_subtabs.addTab(self.mod_single_tab, "Por módulo")
        self.build_modules_single_tab()

        # ---- Todos los módulos ----
        self.mod_full_tab = QWidget()
        self.modules_subtabs.addTab(self.mod_full_tab, "Todos los módulos")
        self.build_modules_full_tab()

    # ---------------- Por módulo ----------------
    def build_modules_single_tab(self):
        layout = QVBoxLayout(self.mod_single_tab)

        layout.addWidget(QLabel("Módulo a validar:"))
        self.combo_modules = QComboBox()
        layout.addWidget(self.combo_modules)

        layout.addWidget(QLabel("Comparación:"))
        self.combo_compare = QComboBox()
        self.combo_compare.addItems([
            "Juego ↔ Mod",
            "Mod ↔ Backup",
            "Juego ↔ Backup"
        ])
        layout.addWidget(self.combo_compare)

        btn_run = QPushButton("Comparar ficheros")
        btn_run.clicked.connect(self.run_validation_module_single)
        layout.addWidget(btn_run)

        self.tree_mod_single = QTreeWidget()
        self.tree_mod_single.setColumnCount(3)
        self.tree_mod_single.setHeaderLabels(["Estado", "Archivo", "diff"])
        self.tree_mod_single.setColumnWidth(0, 120)
        self.tree_mod_single.setColumnWidth(1, 500)
        self.tree_mod_single.setColumnHidden(2, True)
        layout.addWidget(self.tree_mod_single)

        self.tree_mod_single.itemDoubleClicked.connect(self.open_diff_from_item)

    # ---------------- Todos los módulos ----------------
    def build_modules_full_tab(self):
        layout = QVBoxLayout(self.mod_full_tab)

        layout.addWidget(QLabel("Validación total de módulos"))

        btn_run = QPushButton("Validar todos los módulos")
        btn_run.clicked.connect(self.run_validation_module_full)
        layout.addWidget(btn_run)

        self.tree_mod_full = QTreeWidget()
        self.tree_mod_full.setColumnCount(3)
        self.tree_mod_full.setHeaderLabels(["Módulo", "MOD ↔ Backup", "Juego ↔ Backup"])
        self.tree_mod_full.setColumnWidth(0, 200)
        layout.addWidget(self.tree_mod_full)

        btn_details = QPushButton("Ver detalles del módulo seleccionado")
        btn_details.clicked.connect(self.show_module_full_details)
        layout.addWidget(btn_details)

    # =========================================================
    # ARCHIVOS
    # =========================================================
    def build_files_tab(self):
        layout = QVBoxLayout(self.files_tab)

        self.files_subtabs = QTabWidget()
        layout.addWidget(self.files_subtabs)

        # ---- Por archivo ----
        self.file_single_tab = QWidget()
        self.files_subtabs.addTab(self.file_single_tab, "Por archivo")
        self.build_files_single_tab()

        # ---- Todos los archivos ----
        self.file_full_tab = QWidget()
        self.files_subtabs.addTab(self.file_full_tab, "Todos los archivos")
        self.build_files_full_tab()

    # ---------------- Por archivo ----------------
    def build_files_single_tab(self):
        layout = QVBoxLayout(self.file_single_tab)

        layout.addWidget(QLabel("Archivo a validar:"))
        self.combo_files = QComboBox()
        self.combo_files.setEditable(False)
        layout.addWidget(self.combo_files)

        # -------------------------
        # BOTONES DE GESTIÓN
        # -------------------------
        btn_row = QHBoxLayout()
        layout.addLayout(btn_row)

        btn_add = QPushButton("Añadir archivo…")
        btn_add.clicked.connect(self.add_new_file)
        btn_row.addWidget(btn_add)

        btn_activate = QPushButton("Activar archivo")
        btn_activate.clicked.connect(self.activate_file)
        btn_row.addWidget(btn_activate)

        btn_deactivate = QPushButton("Desactivar archivo")
        btn_deactivate.clicked.connect(self.deactivate_file)
        btn_row.addWidget(btn_deactivate)

        btn_exception = QPushButton("Excepción de ruta…")
        btn_exception.clicked.connect(self.set_path_exception)
        btn_row.addWidget(btn_exception)

        # -------------------------
        # MODO DE VALIDACIÓN
        # -------------------------
        mode_row = QHBoxLayout()
        layout.addLayout(mode_row)
        mode_row.addWidget(QLabel("Validar contra:"))

        self.validation_mode = "game"  # "game" o "mod"

        btn_game = QPushButton("Juego")
        btn_mod = QPushButton("Mod")

        btn_game.clicked.connect(lambda: setattr(self, "validation_mode", "game"))
        btn_mod.clicked.connect(lambda: setattr(self, "validation_mode", "mod"))

        mode_row.addWidget(btn_game)
        mode_row.addWidget(btn_mod)

        # -------------------------
        # VALIDAR
        # -------------------------
        btn_validate = QPushButton("Validar archivo")
        btn_validate.clicked.connect(self.validate_file_single)
        layout.addWidget(btn_validate)

        self.label_result = QLabel("")
        layout.addWidget(self.label_result)

        btn_diff = QPushButton("Ver diff")
        btn_diff.clicked.connect(self.show_current_diff)
        layout.addWidget(btn_diff)


    # ---------------- Todos los archivos ----------------
    def build_files_full_tab(self):
        layout = QVBoxLayout(self.file_full_tab)

        layout.addWidget(QLabel("Validación total de archivos"))

        btn_run = QPushButton("Validar todos los archivos")
        btn_run.clicked.connect(self.run_validation_file_full)
        layout.addWidget(btn_run)

        self.tree_file_full = QTreeWidget()
        self.tree_file_full.setColumnCount(3)
        self.tree_file_full.setHeaderLabels(["Archivo", "MOD ↔ Backup", "Juego ↔ Backup"])
        self.tree_file_full.setColumnWidth(0, 260)
        layout.addWidget(self.tree_file_full)

        btn_diff = QPushButton("Ver diff del archivo seleccionado")
        btn_diff.clicked.connect(self.show_file_full_diff)
        layout.addWidget(btn_diff)

    # =========================================================
    # REFRESH (llamado desde ui_main_qt)
    # =========================================================
    def refresh(self):
        profile = self.app.current_profile
        if not profile:
            self.combo_modules.clear()
            self.combo_files.clear()
            return

        # Módulos
        game_key = profile["game"]
        game_modules = self.app.modules.get(game_key, {})
        self.combo_modules.clear()
        self.combo_modules.addItems(sorted(game_modules.keys()))

        # Archivos
        game_files = self.app.files.get(game_key, {})
        self.combo_files.clear()
        self.combo_files.addItems(sorted(game_files.keys()))

        self.label_result.setText("")
        self.current_diff_lines = None

        self.tree_mod_single.clear()
        self.tree_mod_full.clear()
        self.tree_file_full.clear()
        self.module_full_results.clear()
        self.file_full_results.clear()

    # =========================================================
    # LÓGICA: MÓDULOS (por módulo)
    # =========================================================
    def run_validation_module_single(self):
        self.tree_mod_single.clear()
        self.current_diff_lines = None

        profile = self.app.current_profile
        if not profile:
            QMessageBox.critical(self, "Error", "Selecciona un perfil")
            return

        module_name = self.combo_modules.currentText()
        if not module_name:
            QMessageBox.critical(self, "Error", "Selecciona un módulo")
            return

        comparison = self.combo_compare.currentText()

        game_key = profile["game"]
        game_modules = self.app.modules.get(game_key, {})

        if module_name not in game_modules:
            QMessageBox.critical(self, "Error", "Módulo no encontrado")
            return

        cfg = game_modules[module_name]
        rel_path = cfg["path"]
        ignore_ext = cfg.get("ignore_ext", [])

        game_root = profile["game_root"]
        mod_root = profile["mod_root"]
        backup_root = profile["backup_root"]

        if not game_root or not mod_root or not backup_root:
            QMessageBox.critical(self, "Error", "Configura rutas de juego, mod y backup en el perfil")
            return

        game_files, backup_files = collect_module_files(game_root, backup_root, rel_path)
        mod_files, _ = collect_module_files(mod_root, mod_root, rel_path)

        if comparison == "Juego ↔ Mod":
            left = game_files
            right = mod_files
        elif comparison == "Mod ↔ Backup":
            left = mod_files
            right = backup_files
        else:
            left = game_files
            right = backup_files

        all_keys = sorted(set(left.keys()) | set(right.keys()))

        for rel in all_keys:
            ext = os.path.splitext(rel)[1].lower()
            if ext in ignore_ext:
                continue

            l = left.get(rel)
            r = right.get(rel)

            if l and r:
                same, diff_lines = compare_file_contents(l, r)
                if same:
                    continue
                estado = "Modificado"
            elif l and not r:
                estado = "Eliminado"
                diff_lines = None
            else:
                estado = "Añadido"
                diff_lines = None

            item = QTreeWidgetItem([estado, rel, json.dumps(diff_lines)])
            if estado == "Modificado":
                item.setForeground(0, QColor("#d17b00"))
            elif estado == "Añadido":
                item.setForeground(0, QColor("green"))
            elif estado == "Eliminado":
                item.setForeground(0, QColor("red"))

            self.tree_mod_single.addTopLevelItem(item)

    # =========================================================
    # LÓGICA: MÓDULOS (todos)
    # =========================================================
    def run_validation_module_full(self):
        profile = self.app.current_profile
        if not profile:
            return

        game_key = profile["game"]
        game_modules = self.app.modules.get(game_key, {})

        active_modules = profile["modules"]

        self.module_full_results = []
        self.tree_mod_full.clear()

        for module_name in active_modules:
            if module_name not in game_modules:
                continue

            cfg = game_modules[module_name]
            rel = cfg["path"]
            ignore_ext = cfg.get("ignore_ext", [])

            game_dir = os.path.join(profile["game_root"], rel)
            mod_dir = os.path.join(profile["mod_root"], rel)
            backup_dir = os.path.join(profile["backup_root"], rel)

            files_mod = list_files_recursive(mod_dir)
            files_game = list_files_recursive(game_dir)
            files_backup = list_files_recursive(backup_dir)

            all_files = sorted(set(files_mod + files_game + files_backup))

            detalles_mod = []
            detalles_game = []

            mod_equal = mod_changed = mod_only = backup_only_mod = 0
            game_equal = game_changed = game_only = backup_only_game = 0

            for f in all_files:
                ext = os.path.splitext(f)[1].lower()
                if ext in ignore_ext:
                    continue

                mod_path = os.path.join(mod_dir, f)
                game_path = os.path.join(game_dir, f)
                backup_path = os.path.join(backup_dir, f)

                # MOD ↔ BACKUP
                if not os.path.isfile(mod_path):
                    if os.path.isfile(backup_path):
                        detalles_mod.append((f, "Eliminado", None))
                        backup_only_mod += 1
                elif not os.path.isfile(backup_path):
                    detalles_mod.append((f, "Añadido", None))
                    mod_only += 1
                else:
                    same, diff = compare_file_contents(mod_path, backup_path)
                    if same:
                        mod_equal += 1
                    else:
                        detalles_mod.append((f, "Modificado", diff))
                        mod_changed += 1

                # JUEGO ↔ BACKUP
                if not os.path.isfile(game_path):
                    if os.path.isfile(backup_path):
                        detalles_game.append((f, "Eliminado", None))
                        backup_only_game += 1
                elif not os.path.isfile(backup_path):
                    detalles_game.append((f, "Añadido", None))
                    game_only += 1
                else:
                    same, diff = compare_file_contents(game_path, backup_path)
                    if same:
                        game_equal += 1
                    else:
                        detalles_game.append((f, "Modificado", diff))
                        game_changed += 1

            total_mod = mod_equal + mod_changed + mod_only + backup_only_mod
            total_game = game_equal + game_changed + game_only + backup_only_game

            estado_mod = (
                f"{total_mod} archivos — "
                f"{mod_changed} modificados, "
                f"{mod_equal} iguales, "
                f"{mod_only} añadidos, "
                f"{backup_only_mod} eliminados"
            )

            estado_game = (
                f"{total_game} archivos — "
                f"{game_changed} modificados, "
                f"{game_equal} iguales, "
                f"{game_only} añadidos, "
                f"{backup_only_game} eliminados"
            )

            self.module_full_results.append(
                (module_name, estado_mod, estado_game, detalles_mod, detalles_game)
            )

            item = QTreeWidgetItem([module_name, estado_mod, estado_game])
            self.tree_mod_full.addTopLevelItem(item)

    def show_module_full_details(self):
        sel = self.tree_mod_full.selectedItems()
        if not sel:
            QMessageBox.information(self, "Info", "Selecciona un módulo")
            return

        module_name = sel[0].text(0)

        for name, estado_mod, estado_game, detalles_mod, detalles_game in self.module_full_results:
            if name == module_name:
                self.show_module_details_dialog(module_name, detalles_mod, detalles_game)
                return

    def show_module_details_dialog(self, module_name, detalles_mod, detalles_game):
        from PyQt6.QtWidgets import QDialog, QSplitter

        dlg = QDialog(self)
        dlg.setWindowTitle(f"Detalles — {module_name}")
        dlg.resize(1000, 600)

        layout = QVBoxLayout(dlg)
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # MOD ↔ Backup
        w_mod = QWidget()
        tabs.addTab(w_mod, "MOD ↔ Backup")
        l_mod = QVBoxLayout(w_mod)

        tree_mod = QTreeWidget()
        tree_mod.setColumnCount(3)
        tree_mod.setHeaderLabels(["Estado", "Archivo", "diff"])
        tree_mod.setColumnWidth(0, 120)
        tree_mod.setColumnWidth(1, 500)
        tree_mod.setColumnHidden(2, True)
        l_mod.addWidget(tree_mod)

        for f, estado, diff in detalles_mod:
            if estado in ("Modificado", "Añadido", "Eliminado"):
                item = QTreeWidgetItem([estado, f, json.dumps(diff)])
                if estado == "Modificado":
                    item.setForeground(0, QColor("#d17b00"))
                elif estado == "Añadido":
                    item.setForeground(0, QColor("green"))
                elif estado == "Eliminado":
                    item.setForeground(0, QColor("red"))
                tree_mod.addTopLevelItem(item)

        tree_mod.itemDoubleClicked.connect(self.open_diff_from_item)

        # Juego ↔ Backup
        w_game = QWidget()
        tabs.addTab(w_game, "Juego ↔ Backup")
        l_game = QVBoxLayout(w_game)

        tree_game = QTreeWidget()
        tree_game.setColumnCount(3)
        tree_game.setHeaderLabels(["Estado", "Archivo", "diff"])
        tree_game.setColumnWidth(0, 120)
        tree_game.setColumnWidth(1, 500)
        tree_game.setColumnHidden(2, True)
        l_game.addWidget(tree_game)

        for f, estado, diff in detalles_game:
            if estado in ("Modificado", "Añadido", "Eliminado"):
                item = QTreeWidgetItem([estado, f, json.dumps(diff)])
                if estado == "Modificado":
                    item.setForeground(0, QColor("#d17b00"))
                elif estado == "Añadido":
                    item.setForeground(0, QColor("green"))
                elif estado == "Eliminado":
                    item.setForeground(0, QColor("red"))
                tree_game.addTopLevelItem(item)

        tree_game.itemDoubleClicked.connect(self.open_diff_from_item)

        dlg.exec()

    # =========================================================
    # LÓGICA: ARCHIVOS (por archivo)
    # =========================================================
    def validate_file_single(self):
        profile = self.app.current_profile
        if not profile:
            return

        sel = self.combo_files.currentText()
        if not sel:
            return

        game_key = profile["game"]
        game_files = self.app.files.get(game_key, {})

        if sel not in game_files:
            return

        data = game_files[sel]
        rel_game = data["path"]
        rel_mod = data.get("map_to", rel_game)

        game_path = os.path.join(profile["game_root"], rel_game)
        backup_path = os.path.join(profile["backup_root"], rel_game)
        mod_path = os.path.join(profile["mod_root"], rel_mod)

        mode = self.validation_mode

        if mode == "game":
            left_path = game_path
            left_label = "JUEGO"
            rel_display = rel_game
        else:
            left_path = mod_path
            left_label = "MOD"
            rel_display = rel_mod

        if not os.path.isfile(left_path):
            self.label_result.setText(f"[+] SOLO EN {left_label} — {rel_display}")
            self.label_result.setStyleSheet("color: blue;")
            self.current_diff_lines = None
            return

        if not os.path.isfile(backup_path):
            self.label_result.setText(f"[-] SOLO EN BACKUP — {rel_game}")
            self.label_result.setStyleSheet("color: purple;")
            self.current_diff_lines = None
            return

        same, diff = compare_file_contents(left_path, backup_path)

        if same:
            self.label_result.setText(f"[=] IGUAL — {rel_display}")
            self.label_result.setStyleSheet("color: green;")
            self.current_diff_lines = None
        else:
            self.label_result.setText(f"[!] CAMBIADO — {rel_display}")
            self.label_result.setStyleSheet("color: red;")
            self.current_diff_lines = diff

    def show_current_diff(self):
        if not self.current_diff_lines:
            QMessageBox.information(self, "Info", "No hay diff disponible")
            return

        self.show_diff_dialog(self.current_diff_lines, "Diff del archivo")

    # ---------------------------------------------------------
    # Añadir archivo
    # ---------------------------------------------------------
    def add_new_file(self):
        profile = self.app.current_profile
        if not profile:
            QMessageBox.critical(self, "Error", "Selecciona un perfil")
            return

        from PyQt6.QtWidgets import QFileDialog
        game_root = profile["game_root"]

        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar archivo", game_root)
        if not path:
            return

        rel = os.path.relpath(path, game_root).replace("\\", "/")

        # Cargar files.json
        with open("data/files.json", "r", encoding="utf-8") as f:
            files_data = json.load(f)

        game_key = profile["game"]
        if game_key not in files_data:
            files_data[game_key] = {}

        name = os.path.splitext(os.path.basename(rel))[0]
        base_name = name
        i = 1
        while name in files_data[game_key]:
            name = f"{base_name}_{i}"
            i += 1

        files_data[game_key][name] = {"path": rel}

        # Guardar
        with open("data/files.json", "w", encoding="utf-8") as f:
            json.dump(files_data, f, indent=4)

        self.app.files = files_data

        # Activar en el perfil
        profile["files"].append(name)
        from utils.profile_ops import update_profile, get_profile
        update_profile(profile)
        self.app.current_profile = get_profile(profile["name"])

        self.refresh()


    # ---------------------------------------------------------
    # Activar archivo
    # ---------------------------------------------------------
    def activate_file(self):
        profile = self.app.current_profile
        if not profile:
            return

        sel = self.combo_files.currentText()
        if not sel:
            return

        if sel not in profile["files"]:
            profile["files"].append(sel)
            from utils.profile_ops import update_profile, get_profile
            update_profile(profile)
            self.app.current_profile = get_profile(profile["name"])

        self.refresh()


    # ---------------------------------------------------------
    # Desactivar archivo
    # ---------------------------------------------------------
    def deactivate_file(self):
        profile = self.app.current_profile
        if not profile:
            return

        sel = self.combo_files.currentText()
        if not sel:
            return

        if sel in profile["files"]:
            profile["files"].remove(sel)
            from utils.profile_ops import update_profile, get_profile
            update_profile(profile)
            self.app.current_profile = get_profile(profile["name"])

        self.refresh()


    # ---------------------------------------------------------
    # Excepción de ruta (map_to)
    # ---------------------------------------------------------
    def set_path_exception(self):
        profile = self.app.current_profile
        if not profile:
            return

        sel = self.combo_files.currentText()
        if not sel:
            return

        game_key = profile["game"]
        game_files = self.app.files.get(game_key, {})

        current = game_files[sel].get("map_to", "")

        from PyQt6.QtWidgets import QDialog, QLineEdit

        dlg = QDialog(self)
        dlg.setWindowTitle("Excepción de ruta (MOD)")

        v = QVBoxLayout(dlg)
        v.addWidget(QLabel("Ruta alternativa en el MOD:"))

        entry = QLineEdit()
        entry.setText(current)
        v.addWidget(entry)

        def save():
            new_path = entry.text().strip()

            with open("data/files.json", "r", encoding="utf-8") as f:
                files_data = json.load(f)

            if new_path:
                files_data[game_key][sel]["map_to"] = new_path
            else:
                files_data[game_key][sel].pop("map_to", None)

            with open("data/files.json", "w", encoding="utf-8") as f:
                json.dump(files_data, f, indent=4)

            self.app.files = files_data
            dlg.accept()

        btn = QPushButton("Guardar")
        btn.clicked.connect(save)
        v.addWidget(btn)

        dlg.exec()


    # =========================================================
    # LÓGICA: ARCHIVOS (todos)
    # =========================================================
    def run_validation_file_full(self):
        profile = self.app.current_profile
        if not profile:
            return

        game_key = profile["game"]
        game_files = self.app.files.get(game_key, {})

        active_files = profile["files"]

        self.file_full_results = []
        self.tree_file_full.clear()

        for file_key in active_files:
            if file_key not in game_files:
                continue

            data = game_files[file_key]

            rel_game = data["path"]
            rel_mod = data.get("map_to", rel_game)

            game_path = os.path.join(profile["game_root"], rel_game)
            mod_path = os.path.join(profile["mod_root"], rel_mod)
            backup_path = os.path.join(profile["backup_root"], rel_game)


            # MOD ↔ BACKUP
            if not os.path.isfile(mod_path):
                estado_mod = "[+] Solo en JUEGO"
                diff_mod = None
            elif not os.path.isfile(backup_path):
                estado_mod = "[-] Solo en BACKUP"
                diff_mod = None
            else:
                same, diff_mod = compare_file_contents(mod_path, backup_path)
                estado_mod = "[=] Igual" if same else "[!] Cambiado"

            # JUEGO ↔ BACKUP
            if not os.path.isfile(game_path):
                estado_game = "[+] Solo en MOD"
                diff_game = None
            elif not os.path.isfile(backup_path):
                estado_game = "[-] Solo en BACKUP"
                diff_game = None
            else:
                same, diff_game = compare_file_contents(game_path, backup_path)
                estado_game = "[=] Igual" if same else "[!] Cambiado"

            self.file_full_results.append((file_key, estado_mod, diff_mod, estado_game, diff_game))

            item = QTreeWidgetItem([file_key, estado_mod, estado_game])
            self.tree_file_full.addTopLevelItem(item)

    def show_file_full_diff(self):
        sel = self.tree_file_full.selectedItems()
        if not sel:
            QMessageBox.information(self, "Info", "Selecciona un archivo")
            return

        file_key = sel[0].text(0)

        for name, estado_mod, diff_mod, estado_game, diff_game in self.file_full_results:
            if name == file_key:
                self.show_file_diff_choice_dialog(file_key, diff_mod, diff_game)
                return

    # =========================================================
    # DIFFS
    # =========================================================
    def open_diff_from_item(self, item, column):
        diff_raw = item.text(2)
        file_name = item.text(1)

        if not diff_raw or diff_raw == "None":
            QMessageBox.information(self, "Info", "Este archivo no tiene diferencias")
            return

        try:
            diff = json.loads(diff_raw)
        except Exception:
            diff = diff_raw.split("\n")

        self.show_diff_dialog(diff, f"Diferencias — {file_name}")

    def show_diff_dialog(self, diff_lines, title):
        from PyQt6.QtWidgets import QDialog

        dlg = QDialog(self)
        dlg.setWindowTitle(title)
        dlg.resize(1000, 600)

        layout = QVBoxLayout(dlg)
        text = QTextEdit()
        text.setReadOnly(True)
        layout.addWidget(text)

        cursor = text.textCursor()

        # Formatos de texto
        fmt_added = QTextCharFormat()
        fmt_removed = QTextCharFormat()
        fmt_normal = QTextCharFormat()

        theme = self.app.theme

        # ============================
        #  TEMA OSCURO
        # ============================
        if theme == "dark":
            text.setStyleSheet("""
                background-color: #1e1e1e;
                color: #e6e6e6;
                font-family: Consolas, monospace;
                font-size: 12px;
            """)
            fmt_normal.setForeground(QColor("#e6e6e6"))
            fmt_added.setForeground(QColor("#00cc44"))
            fmt_removed.setForeground(QColor("#ff4444"))

        # ============================
        #  TEMA CLARO
        # ============================
        elif theme == "light":
            text.setStyleSheet("""
                background-color: #ffffff;
                color: #202020;
                font-family: Consolas, monospace;
                font-size: 12px;
            """)
            fmt_normal.setForeground(QColor("#202020"))
            fmt_added.setForeground(QColor("#008800"))
            fmt_removed.setForeground(QColor("#cc0000"))

        # ============================
        #  TEMA CK3
        # ============================
        elif theme == "ck3":
            text.setStyleSheet("""
                background-color: #2a2723;
                color: #e0d6b9;
                font-family: 'Trajan Pro', Georgia, serif;
                font-size: 13px;
            """)
            fmt_normal.setForeground(QColor("#e0d6b9"))
            fmt_added.setForeground(QColor("#7ecf7e"))   # Verde medieval suave
            fmt_removed.setForeground(QColor("#d97a7a")) # Rojo pergamino

        # ============================
        #  TEMA SEPIA
        # ============================
        elif theme == "sepia":
            text.setStyleSheet("""
                background-color: #fff8e7;
                color: #4b3e2a;
                font-family: Georgia, serif;
                font-size: 13px;
            """)
            fmt_normal.setForeground(QColor("#4b3e2a"))
            fmt_added.setForeground(QColor("#2f7d32"))   # Verde natural
            fmt_removed.setForeground(QColor("#b23b3b")) # Rojo cálido

        # ============================
        #  TEMA ALTO CONTRASTE
        # ============================
        elif theme == "contrast":
            text.setStyleSheet("""
                background-color: #000000;
                color: #ffffff;
                font-family: Consolas, monospace;
                font-size: 14px;
            """)
            fmt_normal.setForeground(QColor("#ffffff"))
            fmt_added.setForeground(QColor("#00ff00"))   # Verde fosforito
            fmt_removed.setForeground(QColor("#ff0000")) # Rojo puro

        # ============================
        #  Insertar líneas del diff
        # ============================
        for line in diff_lines:
            if line.startswith("+") and not line.startswith("+++"):
                cursor.insertText(line + "\n", fmt_added)
            elif line.startswith("-") and not line.startswith("---"):
                cursor.insertText(line + "\n", fmt_removed)
            else:
                cursor.insertText(line + "\n", fmt_normal)

        dlg.exec()



    def show_file_diff_choice_dialog(self, file_key, diff_mod, diff_game):
        from PyQt6.QtWidgets import QDialog

        dlg = QDialog(self)
        dlg.setWindowTitle(f"Diff — {file_key}")

        layout = QVBoxLayout(dlg)
        layout.addWidget(QLabel("Selecciona comparación:"))

        btn_mod = QPushButton("MOD ↔ Backup")
        btn_game = QPushButton("Juego ↔ Backup")

        def open_mod():
            if not diff_mod:
                QMessageBox.information(dlg, "Info", "No hay diff disponible")
                return
            self.show_diff_dialog(diff_mod, f"MOD ↔ Backup — {file_key}")

        def open_game():
            if not diff_game:
                QMessageBox.information(dlg, "Info", "No hay diff disponible")
                return
            self.show_diff_dialog(diff_game, f"Juego ↔ Backup — {file_key}")

        btn_mod.clicked.connect(open_mod)
        btn_game.clicked.connect(open_game)

        layout.addWidget(btn_mod)
        layout.addWidget(btn_game)

        dlg.exec()
