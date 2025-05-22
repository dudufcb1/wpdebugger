import customtkinter as ctk

# Configurar apariencia
ctk.set_appearance_mode("System")  # "System", "Dark" o "Light"
ctk.set_default_color_theme("blue")  # "blue", "green" o "dark-blue"

# Crear ventana principal
app = ctk.CTk()
app.title("CustomTkinter Test")
app.geometry("400x300")

# Crear un frame
frame = ctk.CTkFrame(app)
frame.pack(fill="both", expand=True, padx=10, pady=10)

# Añadir etiqueta
label = ctk.CTkLabel(frame, text="Prueba de CustomTkinter", font=("Helvetica", 16))
label.pack(pady=10)

# Añadir botón
button = ctk.CTkButton(frame, text="Haz clic", command=lambda: print("Botón presionado"))
button.pack(pady=10)

# Añadir entrada de texto
entry = ctk.CTkEntry(frame, placeholder_text="Escribe algo aquí")
entry.pack(pady=10)

# Añadir área de texto
textbox = ctk.CTkTextbox(frame, width=300, height=100)
textbox.pack(pady=10)
textbox.insert("1.0", "Este es un área de texto con CustomTkinter.\nPuedes escribir múltiples líneas.")

# Iniciar el bucle principal
app.mainloop()
