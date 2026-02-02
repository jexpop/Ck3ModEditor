# CK3 Mod Tool

Herramienta modular para procesar, validar y gestionar modificaciones de *Crusader Kings III* (CK3).  
Diseñada con un enfoque en **trazabilidad**, **reversibilidad**, **modularidad** y **control manual**.

Permite:

- Aplicar offsets de fechas a archivos del juego
- Editar y sobrescribir `END_DATE` de forma segura
- Procesar módulos independientes con backups deterministas
- Validar diferencias entre Juego ↔ Backup
- Gestionar perfiles con rutas y módulos personalizados
- Editar módulos visualmente desde la interfaz

---

## 🧩 Arquitectura

El proyecto está organizado en módulos independientes:

