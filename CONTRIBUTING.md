# Contribuir a WordPress Debug Viewer

¡Gracias por tu interés en contribuir a WordPress Debug Viewer! Este documento proporciona pautas para contribuir al proyecto.

Proyecto desarrollado originalmente por [Luis Eduardo G. González](https://devactivo.com), especialista en WordPress y desarrollo web.

## Cómo Contribuir

1. **Fork** el repositorio en GitHub
2. **Clona** tu fork a tu máquina local
3. **Crea una rama** para tu contribución
4. **Realiza tus cambios** y asegúrate de seguir las convenciones de código
5. **Prueba** tus cambios
6. **Envía un Pull Request** con una descripción clara de tus cambios

## Configuración del Entorno de Desarrollo

1. Clona el repositorio:
   ```bash
   git clone https://github.com/tu-usuario/wpdebugger.git
   cd wpdebugger
   ```

2. Crea un entorno virtual:
   ```bash
   python -m venv .venv
   ```

3. Activa el entorno virtual:
   - Windows: `.venv\Scripts\activate`
   - Linux/Mac: `source .venv/bin/activate`

4. Instala las dependencias:
   ```bash
   pip install customtkinter watchdog pyperclip
   ```

## Estructura del Proyecto

- `wpdebugger.py` - Punto de entrada principal (interfaz moderna)
- `wpdebugger_simple.py` - Versión legacy (interfaz tradicional)
- `src/main_modern.py` - Lógica principal para la versión moderna
- `src/main_simple.py` - Lógica principal para la versión legacy
- `src/gui_modern.py` - Interfaz de usuario moderna con CustomTkinter
- `src/gui_simple.py` - Interfaz de usuario tradicional con Tkinter
- `src/config.py` - Gestión de configuración

## Convenciones de Código

- Sigue PEP 8 para el estilo de código Python
- Usa nombres descriptivos para variables y funciones
- Añade comentarios para explicar el código complejo
- Mantén las funciones pequeñas y con un solo propósito

## Pruebas

Antes de enviar un Pull Request, asegúrate de probar tus cambios:

1. Verifica que la aplicación se inicia correctamente
2. Prueba las funcionalidades que has modificado
3. Asegúrate de que no has introducido nuevos errores

## Proceso de Pull Request

1. Asegúrate de que tu código sigue las convenciones del proyecto
2. Actualiza la documentación si es necesario
3. Describe claramente los cambios que has realizado
4. Menciona cualquier problema que resuelva tu PR

## Licencia

Al contribuir a este proyecto, aceptas que tus contribuciones estarán bajo la misma licencia que el proyecto.

¡Gracias por contribuir!
