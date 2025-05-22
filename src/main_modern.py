"""
WordPress Debug Viewer - Módulo principal (versión moderna)
Desarrollado por Luis Eduardo G. González (DevActivo.com | EspecialistaEnWP.com)
"""

import os
import time
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import re

# Añadir el directorio actual al path para encontrar los módulos
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Importar módulos locales
from config import Config
from gui_modern import DebuggerGUI

class DebugLogHandler(FileSystemEventHandler):
    def __init__(self, debug_log_path, gui, config):
        self.debug_log_path = debug_log_path
        self.gui = gui
        self.config = config
        self.last_modified = 0
        self.last_content = ""

        # Expresión regular para detectar bloques (líneas que comienzan con corchetes)
        self.block_pattern = re.compile(r'^\[.*?\]', re.MULTILINE)

        # Mostrar contenido inicial si existe
        if os.path.exists(debug_log_path):
            self.show_current_content()

    def on_modified(self, event):
        if event.src_path == self.debug_log_path:
            # Evitar múltiples actualizaciones en un corto período
            current_time = time.time()
            if current_time - self.last_modified > 0.5:  # 500ms debounce
                self.last_modified = current_time
                self.show_current_content()

    def show_current_content(self):
        """Mostrar el contenido actual del archivo debug.log"""
        try:
            # Verificar si el archivo existe
            if not os.path.exists(self.debug_log_path):
                print(f"El archivo {self.debug_log_path} no existe")
                return

            # Verificar si el archivo está vacío
            if os.path.getsize(self.debug_log_path) == 0:
                print(f"El archivo {self.debug_log_path} está vacío")
                self.gui.update_content("")
                return

            with open(self.debug_log_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

                # Verificar si hay cambios en el contenido
                if content != self.last_content:
                    print(f"Cambios detectados. Tamaño anterior: {len(self.last_content)}, Tamaño actual: {len(content)}")
                    self.last_content = content

                    # Aplicar filtrado de expresiones regulares
                    filtered_content = self.filter_content(content)

                    # Enviar el contenido a la GUI
                    self.gui.update_content(filtered_content)

                    # Hacer que el título parpadee
                    self.gui.flash_title()
                else:
                    print("No se detectaron cambios en el contenido")
        except Exception as e:
            print(f"Error al leer el archivo: {e}")

    def filter_content(self, content):
        """Filtrar el contenido usando las expresiones regulares configuradas"""
        if not self.config or not self.config.regex_exceptions:
            return content

        filtered_content = content
        for regex_pattern in self.config.regex_exceptions:
            try:
                # Crear un patrón de regex
                pattern = re.compile(regex_pattern, re.MULTILINE)

                # Reemplazar las coincidencias con un mensaje de filtrado
                filtered_content = pattern.sub("[FILTRADO: Coincide con patrón configurado]", filtered_content)
            except Exception as e:
                print(f"Error al aplicar filtro regex '{regex_pattern}': {e}")

        return filtered_content

    def clear_content(self):
        """Borrar el contenido del archivo debug.log"""
        try:
            # Verificar si el archivo existe
            if not os.path.exists(self.debug_log_path):
                print(f"El archivo {self.debug_log_path} no existe")
                return

            # Abrir el archivo en modo escritura para borrarlo
            with open(self.debug_log_path, 'w', encoding='utf-8') as f:
                f.write("")

            # Actualizar el contenido en la GUI
            self.last_content = ""
            self.gui.update_content("")
            print(f"Contenido de {self.debug_log_path} borrado")
        except Exception as e:
            print(f"Error al borrar el contenido: {e}")

    def reload_content(self):
        """Recargar el contenido del archivo debug.log"""
        # Forzar la recarga del contenido
        self.last_content = ""
        self.show_current_content()

def main():
    # Cargar configuración
    config = Config()

    # Variables globales para el manejador y el observador
    debug_handler = None
    observer = None

    # Callbacks para la GUI
    def on_path_selected(path):
        config.wp_content_path = path
        config.save_config()
        start_monitoring(path)

    def on_clear_content():
        if debug_handler:
            debug_handler.clear_content()

    def on_reload_content():
        if debug_handler:
            print("Recargando contenido del archivo debug.log...")
            debug_handler.reload_content()

    # Inicializar GUI con las funciones de callback
    gui = DebuggerGUI(on_path_selected, on_clear_content, config)

    # Añadir la función de recarga
    gui.on_reload_content = on_reload_content

    def start_monitoring(wp_content_path):
        nonlocal debug_handler, observer

        # Verificar si la ruta existe
        if not os.path.exists(wp_content_path):
            print(f"La ruta {wp_content_path} no existe")
            return False

        # Construir la ruta al archivo debug.log
        debug_dir = wp_content_path
        debug_log_path = os.path.join(debug_dir, "debug.log")

        # Verificar si el archivo debug.log existe
        if not os.path.exists(debug_log_path):
            print(f"El archivo debug.log no existe en {debug_dir}")
            # Intentar crear el archivo
            try:
                with open(debug_log_path, 'w', encoding='utf-8') as f:
                    f.write("")
                print(f"Archivo debug.log creado en {debug_dir}")
            except Exception as e:
                print(f"Error al crear el archivo debug.log: {e}")
                return False

        # Inicializar el manejador de eventos
        debug_handler = DebugLogHandler(debug_log_path, gui, config)

        # Configurar y iniciar el observador
        if observer:
            observer.stop()
            if observer.is_alive():
                observer.join()

        observer = Observer()
        observer.schedule(debug_handler, debug_dir, recursive=False)
        observer.start()

        print(f"Monitoreando cambios en {debug_log_path}")
        return True

    # Siempre solicitar la ruta del directorio wp-content al iniciar
    if not gui.request_wp_content_path():
        print("No se seleccionó un directorio wp-content. Saliendo...")
        return

    # Mostrar la ventana
    if not gui.is_window_open:
        gui.create_window()
        print("Ventana creada")

    # Iniciar el monitoreo si hay una ruta configurada
    if config.wp_content_path:
        start_monitoring(config.wp_content_path)

    # Iniciar el bucle principal
    try:
        gui.start_mainloop()
    except KeyboardInterrupt:
        print("Programa interrumpido por el usuario")
    finally:
        # Detener el observador al salir
        if observer:
            observer.stop()
            if observer.is_alive():
                observer.join()
        print("Programa finalizado")

if __name__ == "__main__":
    main()
