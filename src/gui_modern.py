"""
WordPress Debug Viewer - Interfaz gráfica moderna con CustomTkinter
Desarrollado por Luis Eduardo G. González (DevActivo.com | EspecialistaEnWP.com)
"""

import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox, filedialog
import pyperclip
import threading
import time
import re
import os
import subprocess
import sys

class DebuggerGUI:
    def resource_path(self, relative_path):
        """Obtener la ruta absoluta a un recurso, funciona para dev y para PyInstaller"""
        try:
            # PyInstaller crea un directorio temporal y almacena la ruta en _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def __init__(self, on_path_selected, on_clear_content, config=None):
        self.root = None
        self.on_path_selected = on_path_selected
        self.on_clear_content = on_clear_content
        self.on_reload_content = None  # Se asignará más tarde
        self.is_window_open = False
        self.config = config
        self.exceptions_window = None
        self.console_logs_window = None
        self.text_widget = None
        self.blocks_frame = None
        self.canvas = None
        self.blocks = []
        self.block_widgets = []
        self.original_title = "WordPress Debug Viewer"
        self.is_flashing = False
        self.flash_thread = None
        self.selection_mode = False
        self.current_content = ""
        # Expresión regular para detectar bloques (líneas que comienzan con corchetes)
        self.block_pattern = re.compile(r'^\[.*?\]', re.MULTILINE)

        # Configurar apariencia de CustomTkinter
        ctk.set_appearance_mode("System")  # "System", "Dark" o "Light"
        ctk.set_default_color_theme("blue")  # "blue", "green" o "dark-blue"

    def request_wp_content_path(self):
        """Solicitar la ruta al directorio wp-content"""
        root = ctk.CTk()
        root.withdraw()
        folder_path = filedialog.askdirectory(title="Selecciona el directorio wp-content")
        root.destroy()
        if folder_path:
            self.on_path_selected(folder_path)
            return True
        return False

    def request_console_logs_path(self):
        """Solicitar la ruta a la carpeta de logs de consola"""
        if not self.root:
            root = ctk.CTk()
            root.withdraw()
            folder_path = filedialog.askdirectory(title="Selecciona la carpeta de logs de consola")
            root.destroy()
        else:
            folder_path = filedialog.askdirectory(title="Selecciona la carpeta de logs de consola", parent=self.root)

        if folder_path and self.config:
            self.config.set_console_logs_path(folder_path)

            # Actualizar la interfaz si la ventana de configuración está abierta
            if self.console_logs_window:
                for widget in self.console_logs_window.winfo_children():
                    if isinstance(widget, ctk.CTkFrame):
                        for child in widget.winfo_children():
                            if isinstance(child, ctk.CTkFrame) and "Carpeta de Logs de Consola" in child._text:
                                for grandchild in child.winfo_children():
                                    if isinstance(grandchild, ctk.CTkEntry):
                                        # Actualizar el Entry con la nueva ruta
                                        grandchild.delete(0, tk.END)
                                        grandchild.insert(0, folder_path)
                                        break

            # Mostrar mensaje de confirmación
            messagebox.showinfo("Configuración guardada", f"Carpeta de logs de consola configurada:\n{folder_path}")
            return True
        return False

    def create_window(self):
        """Crear la ventana principal"""
        if self.root is None:
            self.root = ctk.CTk()
            self.root.title(self.original_title)
            self.root.geometry("900x700")

            # Establecer el icono de la ventana
            try:
                icon_path = self.resource_path("monitor.ico")
                if os.path.exists(icon_path):
                    self.root.iconbitmap(icon_path)
                    print(f"Icono establecido desde: {icon_path}")
                else:
                    print(f"Archivo de icono no encontrado en: {icon_path}")
            except Exception as e:
                print(f"Error al establecer el icono: {e}")

            # Configurar el comportamiento del icono X (cerrar)
            self.root.protocol("WM_DELETE_WINDOW", self.close_window)

            # Contenedor principal
            main_frame = ctk.CTkFrame(self.root)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # Crear un tabview para tener pestañas
            tabview = ctk.CTkTabview(main_frame)
            tabview.pack(fill=tk.BOTH, expand=True)

            # Pestaña para vista normal
            normal_tab = tabview.add("Vista Normal")

            # Pestaña para vista de selección
            selection_tab = tabview.add("Vista de Selección")

            # Área de texto con colores personalizados para vista normal
            self.text_widget = ctk.CTkTextbox(normal_tab, wrap="word", font=("Consolas", 10))
            self.text_widget.pack(fill=tk.BOTH, expand=True)

            # Frame para los bloques con scroll en la pestaña de selección
            blocks_container = ctk.CTkFrame(selection_tab)
            blocks_container.pack(fill=tk.BOTH, expand=True)

            # Scrollable frame para los bloques
            self.blocks_frame = ctk.CTkScrollableFrame(blocks_container)
            self.blocks_frame.pack(fill=tk.BOTH, expand=True)

            # Función para cambiar entre modos
            def on_tab_changed(event):
                tab_name = tabview.get()
                if tab_name == "Vista Normal":
                    self.selection_mode = False
                    self.selection_buttons_frame.pack_forget()
                else:
                    self.selection_mode = True
                    self.selection_buttons_frame.pack(side=tk.LEFT)
                    # Actualizar la vista de selección si hay contenido
                    if self.current_content:
                        self.update_blocks(self.split_into_blocks(self.current_content))

            # Vincular evento de cambio de pestaña
            tabview.configure(command=on_tab_changed)

            # Frame para botones
            button_frame = ctk.CTkFrame(main_frame)
            button_frame.pack(fill=tk.X, pady=(10, 0))

            # Botones comunes
            ctk.CTkButton(button_frame, text="Copiar Todo",
                         command=self.copy_all_content).pack(side=tk.LEFT, padx=5)
            ctk.CTkButton(button_frame, text="Borrar Contenido",
                         command=self.clear_content).pack(side=tk.LEFT, padx=5)
            ctk.CTkButton(button_frame, text="Recargar",
                         command=self.reload_content).pack(side=tk.LEFT, padx=5)
            ctk.CTkButton(button_frame, text="Excepciones",
                         command=self.show_exceptions_manager).pack(side=tk.LEFT, padx=5)
            ctk.CTkButton(button_frame, text="Config. Logs Consola",
                         command=self.show_console_logs_config).pack(side=tk.LEFT, padx=5)
            ctk.CTkButton(button_frame, text="Combinar Logs",
                         command=self.combine_logs).pack(side=tk.LEFT, padx=5)
            ctk.CTkButton(button_frame, text="Abrir Carpeta",
                         command=self.open_folder).pack(side=tk.LEFT, padx=5)

            # Botones para modo selección
            self.selection_buttons_frame = ctk.CTkFrame(button_frame)
            self.selection_buttons_frame.pack(side=tk.LEFT)

            ctk.CTkButton(self.selection_buttons_frame, text="Copiar Seleccionados",
                         command=self.copy_selected_blocks).pack(side=tk.LEFT, padx=5)
            ctk.CTkButton(self.selection_buttons_frame, text="Seleccionar Todo",
                         command=self.select_all_blocks).pack(side=tk.LEFT, padx=5)
            ctk.CTkButton(self.selection_buttons_frame, text="Deseleccionar Todo",
                         command=self.deselect_all_blocks).pack(side=tk.LEFT, padx=5)

            # Inicialmente ocultar botones de selección
            if not self.selection_mode:
                self.selection_buttons_frame.pack_forget()

            self.is_window_open = True

            # Mostrar la ventana en primer plano
            self.root.lift()
            self.root.attributes('-topmost', True)
            self.root.after_idle(self.root.attributes, '-topmost', False)

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

    def update_content(self, content):
        """Actualizar el contenido en la interfaz (modo normal)"""
        if not self.is_window_open:
            self.create_window()

        # Imprimir información de diagnóstico
        print(f"Actualizando contenido. Tamaño: {len(content)} bytes")

        # Guardar el contenido actual
        self.current_content = content

        # Actualizar el área de texto en modo normal
        if self.text_widget:
            try:
                # Actualizar el contenido
                self.text_widget.delete("0.0", tk.END)
                self.text_widget.insert(tk.END, content)

                # Imprimir información de diagnóstico
                print(f"Contenido insertado en el widget. Tamaño del widget: {len(self.text_widget.get('0.0', tk.END))} bytes")

                # Resaltar el último mensaje si hay contenido
                if content.strip():
                    lines = content.split('\n')
                    last_line_index = len(lines) - 1

                    # Encontrar la última línea no vacía
                    while last_line_index >= 0 and not lines[last_line_index].strip():
                        last_line_index -= 1

                    if last_line_index >= 0:
                        # Calcular la posición de la última línea
                        last_line_start = "1.0"
                        for i in range(last_line_index):
                            last_line_start = self.text_widget.index(f"{last_line_start}+1 line")

                        last_line_end = f"{last_line_start}+{len(lines[last_line_index])}c"

                        # Configurar etiqueta para el fondo de color
                        self.text_widget.tag_configure("highlight", background="#d4edda")
                        self.text_widget.tag_add("highlight", last_line_start, last_line_end)

                        # Desplazarse hasta la última línea
                        self.text_widget.see(last_line_end)

                        # Imprimir información de diagnóstico
                        print(f"Última línea resaltada: '{lines[last_line_index]}'")
            except Exception as e:
                print(f"Error al actualizar el contenido: {e}")

        # Si estamos en modo selección, actualizar también los bloques
        if self.selection_mode:
            self.update_blocks(self.split_into_blocks(content))

    def update_blocks(self, blocks):
        """Actualizar los bloques de log en la interfaz (modo selección)"""
        if not self.is_window_open:
            self.create_window()

        # Guardar los bloques
        self.blocks = blocks

        # Limpiar los widgets existentes
        for widget in self.block_widgets:
            for w in widget:
                w.destroy()
        self.block_widgets = []

        # Crear nuevos widgets para cada bloque
        for block in blocks:
            # Frame para el bloque
            block_frame = ctk.CTkFrame(self.blocks_frame)
            block_frame.pack(fill=tk.X, pady=5, padx=5)

            # Variable para el checkbox
            var = tk.BooleanVar(value=False)

            # Checkbox
            checkbox = ctk.CTkCheckBox(block_frame, text="", variable=var)
            checkbox.pack(side=tk.LEFT, padx=(0, 5))

            # Botón de copiar
            copy_button = ctk.CTkButton(
                block_frame,
                text="Copiar",
                command=lambda b=block: self.copy_block(b)
            )
            copy_button.pack(side=tk.RIGHT, padx=5)

            # Área de texto para el contenido del bloque
            text = ctk.CTkTextbox(block_frame, height=100)
            text.insert(tk.END, block)
            text.configure(state="disabled")  # Hacer el texto de solo lectura
            text.pack(fill=tk.X, expand=True, padx=5)

            # Guardar referencia a los widgets
            self.block_widgets.append((block_frame, checkbox, var, text, copy_button))

    def copy_all_content(self):
        """Copiar todo el contenido al portapapeles"""
        if self.current_content:
            pyperclip.copy(self.current_content)
            messagebox.showinfo("Copiado", "Todo el contenido copiado al portapapeles")
        else:
            messagebox.showinfo("Información", "No hay contenido para copiar")

    def copy_block(self, block):
        """Copiar un bloque específico al portapapeles"""
        pyperclip.copy(block)
        messagebox.showinfo("Copiado", "Bloque copiado al portapapeles")

    def copy_selected_blocks(self):
        """Copiar todos los bloques seleccionados al portapapeles"""
        selected_blocks = []
        for _, _, var, text, _ in self.block_widgets:
            if var.get():
                selected_blocks.append(text.get("0.0", tk.END).strip())

        if not selected_blocks:
            messagebox.showinfo("Información", "No hay bloques seleccionados")
            return

        # Copiar al portapapeles
        content = "\n\n".join(selected_blocks)
        pyperclip.copy(content)
        messagebox.showinfo("Copiado", f"{len(selected_blocks)} bloques copiados al portapapeles")

    def select_all_blocks(self):
        """Seleccionar todos los bloques"""
        for _, _, var, _, _ in self.block_widgets:
            var.set(True)

    def deselect_all_blocks(self):
        """Deseleccionar todos los bloques"""
        for _, _, var, _, _ in self.block_widgets:
            var.set(False)

    def clear_content(self):
        """Borrar el contenido del archivo de log"""
        if messagebox.askyesno("Confirmar", "¿Estás seguro de que quieres borrar todo el contenido del archivo de log?"):
            self.on_clear_content()

    def reload_content(self):
        """Recargar completamente el contenido del archivo debug.log"""
        if self.on_reload_content:
            self.on_reload_content()

    def flash_title(self):
        """Hacer que el título de la ventana parpadee para indicar nuevos logs"""
        if not self.root or self.is_flashing:
            return

        self.is_flashing = True

        def flash_task():
            flash_count = 0
            while flash_count < 6 and self.is_flashing:  # Parpadear 3 veces (6 cambios)
                if flash_count % 2 == 0:
                    self.root.title("¡NUEVO LOG! - " + self.original_title)
                else:
                    self.root.title(self.original_title)
                flash_count += 1
                time.sleep(0.5)

            # Restaurar el título original
            if self.root:
                self.root.title(self.original_title)
            self.is_flashing = False

        # Iniciar el parpadeo en un hilo separado
        if self.flash_thread is None or not self.flash_thread.is_alive():
            self.flash_thread = threading.Thread(target=flash_task)
            self.flash_thread.daemon = True
            self.flash_thread.start()

    def show_exceptions_manager(self):
        """Mostrar la ventana de gestión de excepciones"""
        if self.exceptions_window:
            self.exceptions_window.lift()
            return

        # Crear una nueva ventana
        self.exceptions_window = ctk.CTkToplevel(self.root)
        self.exceptions_window.title("Gestión de Excepciones")
        self.exceptions_window.geometry("600x400")
        self.exceptions_window.transient(self.root)

        # Establecer el icono de la ventana
        try:
            icon_path = self.resource_path("monitor.ico")
            if os.path.exists(icon_path):
                self.exceptions_window.iconbitmap(icon_path)
        except Exception as e:
            print(f"Error al establecer el icono en ventana de excepciones: {e}")

        # Configurar para que se cierre correctamente
        self.exceptions_window.protocol("WM_DELETE_WINDOW", self.close_exceptions_window)

        # Frame principal
        main_frame = ctk.CTkFrame(self.exceptions_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Frame para añadir nuevas excepciones
        add_frame = ctk.CTkFrame(main_frame)
        add_frame.pack(fill=tk.X, pady=(0, 10))

        # Etiqueta para el frame
        ctk.CTkLabel(add_frame, text="Añadir Nueva Excepción").pack(anchor="w", padx=10, pady=(10, 0))

        # Contenido del frame
        input_frame = ctk.CTkFrame(add_frame)
        input_frame.pack(fill=tk.X, padx=10, pady=10)

        # Entrada para la nueva expresión regular
        ctk.CTkLabel(input_frame, text="Expresión Regular:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        regex_entry = ctk.CTkEntry(input_frame, width=300)
        regex_entry.grid(row=0, column=1, sticky=tk.W+tk.E, padx=5, pady=5)

        # Botón para añadir
        ctk.CTkButton(input_frame, text="Añadir",
                     command=lambda: self.add_exception(regex_entry.get())).grid(
                         row=0, column=2, padx=5, pady=5)

        # Frame para la lista de excepciones
        list_frame = ctk.CTkFrame(main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)

        # Etiqueta para el frame
        ctk.CTkLabel(list_frame, text="Excepciones Actuales").pack(anchor="w", padx=10, pady=(10, 0))

        # Lista de excepciones (usando Listbox de tkinter ya que CTk no tiene equivalente)
        exceptions_listbox = tk.Listbox(list_frame, height=10, bg="#2b2b2b", fg="#ffffff",
                                       selectbackground="#1f538d", font=("Segoe UI", 10))
        exceptions_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Barra de desplazamiento
        scrollbar = ctk.CTkScrollbar(list_frame, command=exceptions_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        exceptions_listbox['yscrollcommand'] = scrollbar.set

        # Cargar las excepciones existentes
        self.update_exceptions_list(exceptions_listbox)

        # Frame para botones
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        # Botones
        ctk.CTkButton(button_frame, text="Eliminar Seleccionada",
                     command=lambda: self.remove_exception(exceptions_listbox)).pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(button_frame, text="Eliminar Todas",
                     command=lambda: self.clear_exceptions(exceptions_listbox)).pack(side=tk.LEFT, padx=5)
        ctk.CTkButton(button_frame, text="Cerrar",
                     command=self.close_exceptions_window).pack(side=tk.RIGHT, padx=5)

    def update_exceptions_list(self, listbox):
        """Actualizar la lista de excepciones en la interfaz"""
        if not self.config:
            return

        # Limpiar la lista
        listbox.delete(0, tk.END)

        # Añadir cada excepción
        for regex in self.config.regex_exceptions:
            listbox.insert(tk.END, regex)

    def add_exception(self, regex_pattern):
        """Añadir una nueva excepción"""
        if not self.config or not regex_pattern.strip():
            return

        # Intentar añadir la excepción
        if self.config.add_regex_exception(regex_pattern.strip()):
            # Actualizar la lista en la interfaz
            if self.exceptions_window:
                for widget in self.exceptions_window.winfo_children():
                    if isinstance(widget, ctk.CTkFrame):
                        for child in widget.winfo_children():
                            if isinstance(child, ctk.CTkFrame):
                                for grandchild in child.winfo_children():
                                    if isinstance(grandchild, tk.Listbox):
                                        self.update_exceptions_list(grandchild)
                                        break

            # Mostrar mensaje de éxito
            messagebox.showinfo("Éxito", f"Excepción '{regex_pattern}' añadida correctamente")
        else:
            # Mostrar mensaje de error
            messagebox.showerror("Error", f"No se pudo añadir la excepción. Verifica que sea una expresión regular válida.")

    def remove_exception(self, listbox):
        """Eliminar la excepción seleccionada"""
        if not self.config:
            return

        # Obtener la selección
        selection = listbox.curselection()
        if not selection:
            messagebox.showinfo("Información", "No hay ninguna excepción seleccionada")
            return

        # Obtener el patrón seleccionado
        regex_pattern = listbox.get(selection[0])

        # Eliminar la excepción
        if self.config.remove_regex_exception(regex_pattern):
            # Actualizar la lista
            self.update_exceptions_list(listbox)

            # Mostrar mensaje de éxito
            messagebox.showinfo("Éxito", f"Excepción '{regex_pattern}' eliminada correctamente")

    def clear_exceptions(self, listbox):
        """Eliminar todas las excepciones"""
        if not self.config:
            return

        # Confirmar la acción
        if messagebox.askokcancel("Confirmar", "¿Estás seguro de que quieres eliminar todas las excepciones?"):
            # Eliminar todas las excepciones
            self.config.clear_regex_exceptions()

            # Actualizar la lista
            self.update_exceptions_list(listbox)

            # Mostrar mensaje de éxito
            messagebox.showinfo("Éxito", "Todas las excepciones han sido eliminadas")

    def close_exceptions_window(self):
        """Cerrar la ventana de excepciones"""
        if self.exceptions_window:
            self.exceptions_window.destroy()
            self.exceptions_window = None

    def close_window(self):
        """Cerrar completamente la aplicación"""
        if self.root:
            # Mostrar un mensaje de confirmación
            if messagebox.askokcancel("Cerrar", "¿Estás seguro de que quieres cerrar la aplicación?"):
                print("Cerrando la aplicación...")

                # Cerrar la ventana de excepciones si está abierta
                if self.exceptions_window:
                    self.exceptions_window.destroy()
                    self.exceptions_window = None

                # Cerrar la ventana de logs de consola si está abierta
                if self.console_logs_window:
                    self.console_logs_window.destroy()
                    self.console_logs_window = None

                self.root.quit()
                self.root.destroy()
                self.root = None
                self.is_window_open = False

    def show_console_logs_config(self):
        """Mostrar la ventana de configuración de logs de consola"""
        if self.console_logs_window:
            self.console_logs_window.lift()
            return

        # Crear una nueva ventana
        self.console_logs_window = ctk.CTkToplevel(self.root)
        self.console_logs_window.title("Configuración de Logs de Consola")
        self.console_logs_window.geometry("600x300")
        self.console_logs_window.transient(self.root)

        # Establecer el icono de la ventana
        try:
            icon_path = self.resource_path("monitor.ico")
            if os.path.exists(icon_path):
                self.console_logs_window.iconbitmap(icon_path)
        except Exception as e:
            print(f"Error al establecer el icono en ventana de logs de consola: {e}")

        # Configurar para que se cierre correctamente
        self.console_logs_window.protocol("WM_DELETE_WINDOW", self.close_console_logs_window)

        # Frame principal
        main_frame = ctk.CTkFrame(self.console_logs_window)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Frame para la configuración de la carpeta
        folder_frame = ctk.CTkFrame(main_frame)
        folder_frame.pack(fill=tk.X, pady=(0, 10))

        # Etiqueta para el frame
        ctk.CTkLabel(folder_frame, text="Carpeta de Logs de Consola").pack(anchor="w", padx=10, pady=(10, 0))

        # Contenido del frame
        input_frame = ctk.CTkFrame(folder_frame)
        input_frame.pack(fill=tk.X, padx=10, pady=10)

        # Mostrar la ruta actual
        current_path = "No configurada"
        if self.config and self.config.console_logs_path:
            current_path = self.config.console_logs_path

        ctk.CTkLabel(input_frame, text="Ruta actual:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)

        # Crear un Entry
        path_entry = ctk.CTkEntry(input_frame, width=300)
        path_entry.insert(0, current_path)
        path_entry.configure(state="readonly")
        path_entry.grid(row=0, column=1, sticky=tk.W+tk.E, padx=5, pady=5)

        # Botón para seleccionar carpeta
        ctk.CTkButton(input_frame, text="Seleccionar Carpeta",
                     command=self.request_console_logs_path).grid(row=0, column=2, padx=5, pady=5)

        # Frame para información
        info_frame = ctk.CTkFrame(main_frame)
        info_frame.pack(fill=tk.BOTH, expand=True)

        # Etiqueta para el frame
        ctk.CTkLabel(info_frame, text="Información").pack(anchor="w", padx=10, pady=(10, 0))

        # Texto informativo
        info_text = ctk.CTkTextbox(info_frame, height=120)
        info_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        info_text.insert(tk.END, "Esta carpeta debe contener los archivos de logs de consola exportados desde el navegador.\n\n"
                        "Los archivos deben tener extensión .log y contener los logs de consola.\n\n"
                        "Al hacer clic en 'Combinar Logs', se tomará el archivo más reciente de esta carpeta y se combinará con el contenido actual del debug.log.")
        info_text.configure(state="disabled")

        # Frame para botones
        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        # Botón para cerrar
        ctk.CTkButton(button_frame, text="Cerrar",
                     command=self.close_console_logs_window).pack(side=tk.RIGHT, padx=5)

    def close_console_logs_window(self):
        """Cerrar la ventana de configuración de logs de consola"""
        if self.console_logs_window:
            self.console_logs_window.destroy()
            self.console_logs_window = None

    def combine_logs(self):
        """Combinar los logs de debug.log con los logs de consola"""
        if not self.config:
            messagebox.showerror("Error", "No se pudo acceder a la configuración")
            return

        if not self.config.console_logs_path:
            messagebox.showinfo("Información", "Primero debes configurar la carpeta de logs de consola")
            self.show_console_logs_config()
            return

        # Verificar si la carpeta existe
        if not os.path.exists(self.config.console_logs_path):
            messagebox.showerror("Error", f"La carpeta configurada no existe:\n{self.config.console_logs_path}\n\nPor favor, configura una carpeta válida.")
            self.show_console_logs_config()
            return

        # Obtener el archivo de log de consola más reciente
        latest_log_file = self.config.get_latest_console_log()
        if not latest_log_file:
            # Buscar manualmente archivos .log en la carpeta
            log_files = []
            try:
                for file in os.listdir(self.config.console_logs_path):
                    if file.endswith('.log'):
                        log_files.append(file)
            except Exception as e:
                messagebox.showerror("Error", f"Error al leer la carpeta: {str(e)}")
                return

            if not log_files:
                messagebox.showinfo("Información", f"No se encontraron archivos .log en la carpeta:\n{self.config.console_logs_path}")
            else:
                messagebox.showinfo("Información", f"Se encontraron {len(log_files)} archivos .log, pero no se pudo determinar el más reciente.\nArchivos: {', '.join(log_files)}")
            return

        try:
            # Leer el contenido del archivo de log de consola
            with open(latest_log_file, 'r', encoding='utf-8', errors='ignore') as f:
                console_log_content = f.read()

            # Verificar si hay contenido
            if not console_log_content.strip():
                messagebox.showinfo("Información", f"El archivo de log de consola está vacío:\n{os.path.basename(latest_log_file)}")
                return

            # Combinar con el contenido actual
            combined_content = f"=== DEBUG.LOG ===\n\n{self.current_content}\n\n=== CONSOLE.LOG ===\n\n{console_log_content}"

            # Copiar al portapapeles
            pyperclip.copy(combined_content)

            # Mostrar mensaje de éxito
            messagebox.showinfo("Éxito", f"Logs combinados y copiados al portapapeles.\n\nArchivo de consola: {os.path.basename(latest_log_file)}\nTamaño: {len(console_log_content)} bytes\nFecha: {time.ctime(os.path.getmtime(latest_log_file))}")

        except Exception as e:
            messagebox.showerror("Error", f"Error al combinar logs: {str(e)}\n\nArchivo: {latest_log_file}")

    def open_folder(self):
        """Abrir la carpeta donde se encuentra el archivo debug.log"""
        if not self.config or not self.config.wp_content_path:
            messagebox.showinfo("Información", "No hay una carpeta configurada")
            return

        # Obtener la ruta completa al directorio wp-content
        folder_path = self.config.wp_content_path

        # Verificar si la carpeta existe
        if not os.path.exists(folder_path):
            messagebox.showerror("Error", f"La carpeta no existe:\n{folder_path}")
            return

        # Mostrar la ruta que se va a abrir
        print(f"Abriendo carpeta: {folder_path}")

        try:
            # Abrir la carpeta en el explorador de Windows
            # Usar comillas dobles para manejar rutas con espacios
            os.system(f'explorer "{folder_path}"')
        except Exception as e:
            messagebox.showerror("Error", f"Error al abrir la carpeta: {str(e)}")

    def start_mainloop(self):
        """Iniciar el bucle principal de Tkinter"""
        if self.root:
            self.root.mainloop()
