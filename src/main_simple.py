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
from gui_simple import DebuggerGUI

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
        try:
            # Verificar si el archivo existe
            if not os.path.exists(self.debug_log_path):
                print(f"Advertencia: El archivo {self.debug_log_path} no existe.")
                return

            # Verificar el tamaño del archivo
            file_size = os.path.getsize(self.debug_log_path)
            print(f"Tamaño del archivo debug.log: {file_size} bytes")

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
        """Aplicar filtros de expresiones regulares al contenido"""
        if not content or not self.config or not hasattr(self.config, 'regex_exceptions'):
            return content

        filtered_content = content
        try:
            for pattern in self.config.regex_exceptions:
                filtered_content = re.sub(pattern, "[FILTRADO]", filtered_content)
            return filtered_content
        except Exception as e:
            print(f"Error al aplicar filtros: {e}")
            return content

    def split_into_blocks(self, content):
        """Dividir el contenido en bloques basados en líneas que comienzan con corchetes"""
        if not content:
            return []

        # Encontrar todas las posiciones donde comienzan los bloques
        block_starts = [m.start() for m in self.block_pattern.finditer(content)]

        # Si no hay coincidencias, devolver todo el contenido como un solo bloque
        if not block_starts:
            return [content]

        # Crear los bloques
        blocks = []
        for i in range(len(block_starts)):
            start = block_starts[i]
            # Si es el último bloque, el final es el final del contenido
            end = block_starts[i+1] if i < len(block_starts) - 1 else len(content)
            block_content = content[start:end].strip()
            if block_content:
                blocks.append(block_content)

        return blocks

    def reload_content(self):
        """Recargar completamente el contenido del archivo debug.log"""
        try:
            # Verificar si el archivo existe
            if not os.path.exists(self.debug_log_path):
                print(f"Advertencia: El archivo {self.debug_log_path} no existe.")
                return

            # Verificar el tamaño del archivo
            file_size = os.path.getsize(self.debug_log_path)
            print(f"Recargando archivo debug.log. Tamaño: {file_size} bytes")

            with open(self.debug_log_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

                # Actualizar el contenido almacenado
                self.last_content = content

                # Aplicar filtrado de expresiones regulares
                filtered_content = self.filter_content(content)

                # Enviar el contenido a la GUI
                self.gui.update_content(filtered_content)

                print(f"Contenido recargado. Tamaño: {len(content)} bytes")
        except Exception as e:
            print(f"Error al recargar el archivo: {e}")

    def clear_content(self):
        """Borrar el contenido del archivo de log"""
        try:
            with open(self.debug_log_path, 'w') as f:
                f.write('')
            self.last_content = ""
            print("Contenido del archivo debug.log borrado")

            # Actualizar la GUI
            self.gui.update_content("")
        except Exception as e:
            print(f"Error al borrar el contenido: {e}")

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

    # Función para iniciar el monitoreo
    def start_monitoring(wp_content_path):
        nonlocal debug_handler, observer

        # Construir la ruta al archivo debug.log
        debug_log_path = os.path.join(wp_content_path, 'debug.log')

        # Verificar si el directorio existe
        debug_dir = os.path.dirname(debug_log_path)
        if not os.path.exists(debug_dir):
            print(f"El directorio {debug_dir} no existe")
            return False

        # Si el archivo no existe, crearlo vacío
        if not os.path.exists(debug_log_path):
            try:
                open(debug_log_path, 'w').close()
                print(f"Archivo debug.log creado en {debug_log_path}")
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

    try:
        # Iniciar el bucle principal de Tkinter
        gui.start_mainloop()
    except KeyboardInterrupt:
        pass
    finally:
        if observer:
            observer.stop()
            if observer.is_alive():
                observer.join()

if __name__ == "__main__":
    main()
