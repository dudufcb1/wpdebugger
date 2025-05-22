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
        self.is_paused = False  # Estado de pausa para congelar la actualización de logs
        self.pause_button = None  # Referencia al botón de pausa
        # Expresión regular para detectar bloques (líneas que comienzan con corchetes)
        self.block_pattern = re.compile(r'^\[.*?\]', re.MULTILINE)

        # Variables para la búsqueda
        self.search_frame = None
        self.search_entry = None
        self.search_results_label = None
        self.search_matches = []
        self.current_match_index = -1
        self.is_search_visible = False

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

            # Usamos un widget de texto estándar de Tkinter para poder usar el resaltado nativo
            # Creamos un frame para contener el widget de texto y la barra de desplazamiento
            text_frame = ctk.CTkFrame(normal_tab)
            text_frame.pack(fill=tk.BOTH, expand=True)

            # Área de texto con colores personalizados para vista normal (usando Tkinter estándar)
            self.text_widget = tk.Text(text_frame, wrap="word", font=("Consolas", 10),
                                      bg="#2b2b2b", fg="#ffffff", insertbackground="#ffffff")
            self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            # Barra de desplazamiento para el área de texto
            text_scrollbar = ctk.CTkScrollbar(text_frame, command=self.text_widget.yview)
            text_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            self.text_widget['yscrollcommand'] = text_scrollbar.set

            # Configurar atajos de teclado para búsqueda
            self.root.bind("<Control-f>", self.toggle_search)
            self.text_widget.bind("<Control-f>", self.toggle_search)

            # F3 para buscar siguiente
            self.root.bind("<F3>", self.search_next)
            self.text_widget.bind("<F3>", self.search_next)

            # Shift+F3 para buscar anterior
            self.root.bind("<Shift-F3>", self.search_previous)
            self.text_widget.bind("<Shift-F3>", self.search_previous)

            # Escape para cerrar la búsqueda
            self.root.bind("<Escape>", lambda e: self.hide_search())
            self.text_widget.bind("<Escape>", lambda e: self.hide_search())

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

            # Botón de pausa/reanudar
            self.pause_button = ctk.CTkButton(button_frame, text="Pausar",
                                            command=self.toggle_pause)
            self.pause_button.pack(side=tk.LEFT, padx=5)

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

        # Si está en pausa, no actualizar la interfaz pero guardar el contenido
        if self.is_paused:
            print("Actualización pausada. El contenido se mostrará al reanudar.")
            self.current_content = content
            return

        # Guardar el contenido actual
        self.current_content = content

        # Actualizar el área de texto en modo normal
        if self.text_widget:
            try:
                # Guardar las posiciones de búsqueda actuales si la búsqueda está activa
                search_active = self.is_search_visible and self.search_matches
                current_matches = self.search_matches.copy() if search_active else []
                current_match_index = self.current_match_index

                # Actualizar el contenido
                self.text_widget.delete("0.0", tk.END)
                self.text_widget.insert(tk.END, content)

                # Imprimir información de diagnóstico
                print(f"Contenido insertado en el widget. Tamaño del widget: {len(self.text_widget.get('0.0', tk.END))} bytes")

                # Restaurar los resaltados si la búsqueda estaba activa
                if search_active and self.search_entry:
                    # Volver a buscar con el mismo término
                    search_term = self.search_entry.get()
                    if search_term:
                        # Buscar nuevamente
                        self.search_matches = self.find_all_matches(search_term)

                        # Restaurar el índice de coincidencia actual si es posible
                        if self.search_matches:
                            if current_match_index >= 0 and current_match_index < len(self.search_matches):
                                self.current_match_index = current_match_index
                            else:
                                self.current_match_index = 0

                            # Resaltar todas las coincidencias
                            self.highlight_matches(self.search_matches)

                            # Resaltar la coincidencia actual
                            self.highlight_current_match()

                # Desplazarse hasta la última línea si hay contenido
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

                        # Desplazarse hasta la última línea
                        self.text_widget.see(last_line_end)

                        # Imprimir información de diagnóstico
                        print(f"Desplazamiento a la última línea: '{lines[last_line_index]}'")
            except Exception as e:
                print(f"Error al actualizar el contenido: {e}")

        # Si estamos en modo selección, actualizar también los bloques
        if self.selection_mode:
            self.update_blocks(self.split_into_blocks(content))

    def update_blocks(self, blocks):
        """Actualizar los bloques de log en la interfaz (modo selección)"""
        if not self.is_window_open:
            self.create_window()

        # Si está en pausa, no actualizar la interfaz
        if self.is_paused:
            print("Actualización de bloques pausada. Los bloques se mostrarán al reanudar.")
            return

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

    def toggle_pause(self):
        """Alternar entre pausa y reanudar la actualización de logs"""
        self.is_paused = not self.is_paused

        # Actualizar el texto del botón
        if self.pause_button:
            self.pause_button.configure(text="Reanudar" if self.is_paused else "Pausar")

            # Cambiar el color del botón según el estado
            if self.is_paused:
                self.pause_button.configure(fg_color="#E5B80B")  # Amarillo para pausa
            else:
                self.pause_button.configure(fg_color=None)  # Color por defecto

        # Actualizar el título de la ventana
        if self.root:
            if self.is_paused:
                self.root.title(f"{self.original_title} [PAUSADO]")
            else:
                self.root.title(self.original_title)
                # Al reanudar, recargar el contenido para mostrar los cambios acumulados
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
                    # Si está pausado, incluir [PAUSADO] en el título
                    if self.is_paused:
                        self.root.title("¡NUEVO LOG! - " + self.original_title + " [PAUSADO]")
                    else:
                        self.root.title("¡NUEVO LOG! - " + self.original_title)
                else:
                    # Restaurar el título adecuado según el estado de pausa
                    if self.is_paused:
                        self.root.title(self.original_title + " [PAUSADO]")
                    else:
                        self.root.title(self.original_title)
                flash_count += 1
                time.sleep(0.5)

            # Restaurar el título original con el estado de pausa si corresponde
            if self.root:
                if self.is_paused:
                    self.root.title(self.original_title + " [PAUSADO]")
                else:
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

    def toggle_search(self, event=None):
        """Mostrar u ocultar el panel de búsqueda"""
        if self.is_search_visible:
            self.hide_search()
        else:
            self.show_search()
        return "break"  # Evitar que el evento se propague

    def show_search(self):
        """Mostrar el panel de búsqueda"""
        if not self.is_window_open or not self.text_widget:
            return

        if not self.search_frame:
            # Crear el frame de búsqueda como una ventana flotante
            self.search_frame = ctk.CTkToplevel(self.root)
            self.search_frame.title("Buscar")
            self.search_frame.geometry("400x40")
            self.search_frame.resizable(True, False)
            self.search_frame.transient(self.root)  # Hacer que sea una ventana hija

            # Configurar el frame principal
            main_frame = ctk.CTkFrame(self.search_frame)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

            # Campo de entrada para la búsqueda
            self.search_entry = ctk.CTkEntry(main_frame, placeholder_text="Buscar...")
            self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 5))
            self.search_entry.bind("<Return>", self.search_next)
            self.search_entry.bind("<KP_Enter>", self.search_next)

            # Buscar mientras se escribe
            self.search_entry.bind("<KeyRelease>", self.search_text)

            # Botones de navegación
            nav_frame = ctk.CTkFrame(main_frame)
            nav_frame.pack(side=tk.LEFT, padx=5)

            # Botón para buscar hacia arriba
            up_button = ctk.CTkButton(nav_frame, text="▲", width=30, command=self.search_previous)
            up_button.pack(side=tk.LEFT, padx=2)

            # Botón para buscar hacia abajo
            down_button = ctk.CTkButton(nav_frame, text="▼", width=30, command=self.search_next)
            down_button.pack(side=tk.LEFT, padx=2)

            # Botón para cerrar la búsqueda
            close_button = ctk.CTkButton(main_frame, text="✕", width=30, command=self.hide_search)
            close_button.pack(side=tk.LEFT, padx=5)

            # Etiqueta para mostrar resultados
            self.search_results_label = ctk.CTkLabel(main_frame, text="")
            self.search_results_label.pack(side=tk.LEFT, padx=5)

            # Configurar para que se cierre correctamente
            self.search_frame.protocol("WM_DELETE_WINDOW", self.hide_search)

            # Centrar la ventana de búsqueda en relación con la ventana principal
            self.center_search_window()
        else:
            # Si ya existe, mostrarla y traerla al frente
            self.search_frame.deiconify()
            self.search_frame.lift()
            self.center_search_window()

        self.is_search_visible = True

        # Asegurar que el campo de búsqueda reciba el foco
        self.search_frame.after(100, self.search_entry.focus_set)

        # También seleccionar todo el texto si hay alguno
        if self.search_entry.get():
            self.search_entry.after(150, lambda: self.search_entry.select_range(0, tk.END))

        # Si hay texto seleccionado, usarlo como término de búsqueda
        try:
            selected_text = self.text_widget.get(tk.SEL_FIRST, tk.SEL_LAST)
            if selected_text:
                self.search_entry.delete(0, tk.END)
                self.search_entry.insert(0, selected_text)
                self.search_entry.select_range(0, tk.END)
        except tk.TclError:
            pass  # No hay texto seleccionado

    def center_search_window(self):
        """Centrar la ventana de búsqueda en relación con la ventana principal"""
        if not self.search_frame or not self.root:
            return

        # Obtener las dimensiones y posición de la ventana principal
        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        root_width = self.root.winfo_width()

        # Obtener las dimensiones de la ventana de búsqueda
        search_width = self.search_frame.winfo_width()
        search_height = self.search_frame.winfo_height()

        # Calcular la posición centrada
        x = root_x + (root_width - search_width) // 2
        y = root_y + 50  # Colocar cerca de la parte superior

        # Establecer la posición
        self.search_frame.geometry(f"+{x}+{y}")

    def hide_search(self):
        """Ocultar el panel de búsqueda"""
        if self.search_frame:
            self.search_frame.withdraw()  # Ocultar en lugar de destruir

        # Eliminar los resaltados
        if self.text_widget:
            try:
                # Eliminar las etiquetas de resaltado
                self.text_widget.tag_remove("search", "1.0", tk.END)
                self.text_widget.tag_remove("current_match", "1.0", tk.END)
            except Exception as e:
                print(f"Error al eliminar resaltados: {e}")

        self.is_search_visible = False
        self.search_matches = []
        self.current_match_index = -1

    def find_all_matches(self, search_term):
        """Encontrar todas las coincidencias del término de búsqueda en el texto"""
        if not search_term or not self.text_widget:
            return []

        matches = []
        start_pos = "0.0"

        while True:
            # Buscar la siguiente coincidencia
            pos = self.text_widget.search(search_term, start_pos, tk.END, nocase=True)
            if not pos:
                break

            # Calcular la posición final de la coincidencia
            end_pos = f"{pos}+{len(search_term)}c"

            # Añadir a la lista de coincidencias
            matches.append((pos, end_pos))

            # Actualizar la posición de inicio para la siguiente búsqueda
            start_pos = end_pos

        return matches

    def highlight_matches(self, matches):
        """Resaltar todas las coincidencias encontradas"""
        if not self.text_widget or not matches:
            return

        # Eliminar resaltados anteriores
        self.text_widget.tag_remove("search", "1.0", tk.END)
        self.text_widget.tag_remove("current_match", "1.0", tk.END)

        # Configurar etiquetas para resaltado
        self.text_widget.tag_configure("search", background="#FFFF00", foreground="#000000")
        self.text_widget.tag_configure("current_match", background="#FF9900", foreground="#000000")

        # Resaltar todas las coincidencias
        for start_pos, end_pos in matches:
            self.text_widget.tag_add("search", start_pos, end_pos)

        # Actualizar la etiqueta de resultados
        self.update_results_label()

        # Mostrar un mensaje informativo en la ventana de búsqueda
        if len(matches) > 0:
            # Actualizar el título de la ventana de búsqueda con el número de coincidencias
            if self.search_frame:
                self.search_frame.title(f"Buscar - {len(matches)} coincidencias encontradas")

    def highlight_current_match(self):
        """Resaltar la coincidencia actual"""
        if not self.search_matches or self.current_match_index < 0:
            return

        # Obtener la posición de la coincidencia actual
        start_pos, end_pos = self.search_matches[self.current_match_index]

        # Eliminar resaltado anterior de la coincidencia actual
        self.text_widget.tag_remove("current_match", "1.0", tk.END)

        # Resaltar la coincidencia actual
        self.text_widget.tag_add("current_match", start_pos, end_pos)

        # Desplazarse hasta la coincidencia
        self.text_widget.see(start_pos)

        # Actualizar la etiqueta de resultados
        self.update_results_label()

        # Actualizar el título de la ventana de búsqueda con la posición actual
        if self.search_frame:
            self.search_frame.title(f"Buscar - Coincidencia {self.current_match_index + 1} de {len(self.search_matches)}")

    def update_results_label(self):
        """Actualizar la etiqueta que muestra el número de resultados"""
        if not self.search_results_label:
            return

        if not self.search_matches:
            self.search_results_label.configure(text="No hay coincidencias")
        else:
            self.search_results_label.configure(
                text=f"{self.current_match_index + 1} de {len(self.search_matches)}"
            )

    def search_text(self, event=None):
        """Buscar el texto en el contenido"""
        if not self.search_entry or not self.text_widget:
            return

        search_term = self.search_entry.get()
        if not search_term:
            self.search_matches = []
            self.current_match_index = -1
            self.update_results_label()
            return

        # Encontrar todas las coincidencias
        self.search_matches = self.find_all_matches(search_term)

        # Resaltar todas las coincidencias
        self.highlight_matches(self.search_matches)

        # Establecer la coincidencia actual
        if self.search_matches:
            self.current_match_index = 0
            self.highlight_current_match()
        else:
            self.current_match_index = -1
            self.update_results_label()

    def search_next(self, event=None):
        """Buscar la siguiente coincidencia"""
        if not self.search_entry or not self.text_widget:
            return

        # Si es la primera búsqueda o se cambió el término, buscar desde el principio
        current_search_term = self.search_entry.get()
        if not self.search_matches or current_search_term != self.search_entry.get():
            self.search_text()
            return

        # Si no hay coincidencias, no hacer nada
        if not self.search_matches:
            return

        # Avanzar al siguiente resultado
        self.current_match_index = (self.current_match_index + 1) % len(self.search_matches)
        self.highlight_current_match()

    def search_previous(self, event=None):
        """Buscar la coincidencia anterior"""
        if not self.search_entry or not self.text_widget:
            return

        # Si es la primera búsqueda o se cambió el término, buscar desde el principio
        current_search_term = self.search_entry.get()
        if not self.search_matches or current_search_term != self.search_entry.get():
            self.search_text()
            return

        # Si no hay coincidencias, no hacer nada
        if not self.search_matches:
            return

        # Retroceder al resultado anterior
        self.current_match_index = (self.current_match_index - 1) % len(self.search_matches)
        self.highlight_current_match()

    def start_mainloop(self):
        """Iniciar el bucle principal de Tkinter"""
        if self.root:
            self.root.mainloop()
