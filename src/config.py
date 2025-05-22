import json
import os
import re

CONFIG_FILE = "config.json"

class Config:
    def __init__(self):
        self.config_path = os.path.join(os.path.dirname(__file__), '..', CONFIG_FILE)
        self.wp_content_path = None
        self.console_logs_path = None  # Ruta a la carpeta de logs de consola
        self.regex_exceptions = []  # Lista de expresiones regulares para filtrar
        self.load_config()

    def load_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                self.wp_content_path = config.get('wp_content_path')
                self.console_logs_path = config.get('console_logs_path')
                self.regex_exceptions = config.get('regex_exceptions', [])

    def save_config(self):
        config = {
            'wp_content_path': self.wp_content_path,
            'console_logs_path': self.console_logs_path,
            'regex_exceptions': self.regex_exceptions
        }
        with open(self.config_path, 'w') as f:
            json.dump(config, f)

    def set_wp_content_path(self, path):
        """Establecer la ruta al directorio wp-content y guardar la configuración"""
        self.wp_content_path = path
        self.save_config()
        return True

    def set_console_logs_path(self, path):
        """Establecer la ruta a la carpeta de logs de consola y guardar la configuración"""
        self.console_logs_path = path
        self.save_config()
        return True

    def add_regex_exception(self, regex_pattern):
        """Añadir una nueva expresión regular a la lista de excepciones"""
        try:
            # Verificar que la expresión regular sea válida
            re.compile(regex_pattern)

            # Añadir a la lista si no existe ya
            if regex_pattern not in self.regex_exceptions:
                self.regex_exceptions.append(regex_pattern)
                self.save_config()
                return True
            return False
        except re.error:
            # La expresión regular no es válida
            return False

    def remove_regex_exception(self, regex_pattern):
        """Eliminar una expresión regular de la lista de excepciones"""
        if regex_pattern in self.regex_exceptions:
            self.regex_exceptions.remove(regex_pattern)
            self.save_config()
            return True
        return False

    def clear_regex_exceptions(self):
        """Eliminar todas las expresiones regulares de la lista de excepciones"""
        self.regex_exceptions = []
        self.save_config()

    def get_latest_console_log(self):
        """Obtener el archivo de log de consola más reciente"""
        if not self.console_logs_path or not os.path.exists(self.console_logs_path):
            return None

        # Buscar todos los archivos .log en la carpeta
        log_files = [os.path.join(self.console_logs_path, f) for f in os.listdir(self.console_logs_path)
                    if f.endswith('.log') and os.path.isfile(os.path.join(self.console_logs_path, f))]

        if not log_files:
            return None

        # Ordenar por fecha de modificación (más reciente primero)
        log_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)

        # Devolver el archivo más reciente
        return log_files[0]

    def filter_content(self, content):
        """Filtrar el contenido usando las expresiones regulares de excepción"""
        if not self.regex_exceptions:
            return content

        # Dividir el contenido en líneas
        lines = content.split('\n')
        filtered_lines = []

        # Procesar cada línea
        i = 0
        while i < len(lines):
            line = lines[i]
            should_exclude = False

            # Verificar si la línea coincide con alguna expresión regular
            for regex_pattern in self.regex_exceptions:
                try:
                    if re.search(regex_pattern, line):
                        should_exclude = True
                        # Encontramos un patrón a excluir, ahora debemos identificar el bloque completo

                        # Buscar el inicio del bloque (línea con timestamp)
                        start_index = i
                        while start_index > 0:
                            # Buscar una línea que comience con un timestamp [DD-MMM-YYYY HH:MM:SS UTC]
                            if re.match(r'^\[\d{1,2}-\w{3}-\d{4}\s\d{2}:\d{2}:\d{2}\s\w+\]', lines[start_index-1]):
                                if start_index > 1 and lines[start_index-2].strip() == '':
                                    # Si hay una línea en blanco antes, considerarla como separador de bloques
                                    start_index -= 1
                                break
                            start_index -= 1

                        # Buscar el final del bloque (próxima línea con timestamp o fin del contenido)
                        end_index = i
                        while end_index < len(lines) - 1:
                            end_index += 1
                            # Si encontramos una línea que comienza con timestamp, es el inicio del siguiente bloque
                            if re.match(r'^\[\d{1,2}-\w{3}-\d{4}\s\d{2}:\d{2}:\d{2}\s\w+\]', lines[end_index]):
                                break

                        # Si el final es el último índice, incluirlo
                        if end_index == len(lines) - 1:
                            end_index = len(lines)

                        # Obtener el timestamp del bloque para el mensaje resumido
                        timestamp_match = re.match(r'^(\[\d{1,2}-\w{3}-\d{4}\s\d{2}:\d{2}:\d{2}\s\w+\])', lines[start_index])
                        timestamp = timestamp_match.group(1) if timestamp_match else "[Timestamp no encontrado]"

                        # Añadir el mensaje resumido
                        if start_index > 0 and filtered_lines and filtered_lines[-1].strip() != '':
                            filtered_lines.append('')  # Línea en blanco para separar
                        filtered_lines.append(f"{timestamp} Contenido omitido... (coincide con '{regex_pattern}')")

                        # Saltar al final del bloque
                        i = end_index - 1
                        break
                except re.error:
                    # Ignorar expresiones regulares inválidas
                    pass

            # Si no debe excluirse, añadir la línea al resultado
            if not should_exclude:
                filtered_lines.append(line)

            i += 1

        # Unir las líneas filtradas
        return '\n'.join(filtered_lines)
