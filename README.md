# WordPress Debug Viewer

Una aplicación para monitorear y visualizar los logs de depuración de WordPress en tiempo real.

## Características

- Monitoreo en tiempo real del archivo `debug.log` de WordPress
- Interfaz moderna con CustomTkinter
- Soporte para modo claro/oscuro (sigue la configuración del sistema)
- Vista normal y vista de selección por bloques
- Filtrado de mensajes mediante expresiones regulares
- Combinación de logs de consola del navegador con logs de WordPress
- Resaltado del último mensaje recibido
- Notificaciones visuales mediante parpadeo del título
- Búsqueda de texto en los logs con atajos de teclado:
  - Ctrl+F: Abrir/cerrar búsqueda
  - F3: Buscar siguiente coincidencia
  - Shift+F3: Buscar coincidencia anterior
  - Esc: Cerrar búsqueda

## Requisitos

- Python 3.6 o superior
- Bibliotecas requeridas:
  - customtkinter
  - watchdog
  - pyperclip

## Instalación

1. Clona o descarga este repositorio
2. Instala las dependencias:

```bash
pip install customtkinter watchdog pyperclip
```

O si prefieres usar UV:

```bash
uv pip install customtkinter watchdog pyperclip
```

## Uso

### Versión Principal

Ejecuta la aplicación con la interfaz moderna (recomendada):

```bash
python wpdebugger.py
```

### Versión Legacy

Si necesitas usar la interfaz original por alguna razón:

```bash
python wpdebugger_simple.py
```

**Nota**: La versión legacy se mantiene por compatibilidad, pero se recomienda usar la versión principal con la interfaz moderna.

## Configuración

Al iniciar la aplicación, se te pedirá seleccionar el directorio `wp-content` de tu instalación de WordPress. La aplicación buscará o creará el archivo `debug.log` en este directorio y comenzará a monitorearlo.

### Filtrado de Mensajes

Puedes configurar expresiones regulares para filtrar mensajes específicos:

1. Haz clic en el botón "Excepciones"
2. Añade las expresiones regulares que deseas filtrar
3. Los mensajes que coincidan con estas expresiones serán reemplazados por un texto de filtrado

### Logs de Consola

Para combinar logs de consola del navegador con los logs de WordPress:

1. Haz clic en "Config. Logs Consola"
2. Selecciona la carpeta donde se guardan los logs de consola exportados
3. Usa el botón "Combinar Logs" para unir el contenido del archivo de log más reciente con el contenido actual

## Interfaz

La aplicación tiene dos vistas principales:

- **Vista Normal**: Muestra todos los logs en un área de texto continua
- **Vista de Selección**: Divide los logs en bloques individuales que pueden ser seleccionados y copiados independientemente

## Compilación

Para crear un ejecutable independiente:

```bash
pyinstaller --onefile --windowed --icon=monitor.ico --add-data "src;src" --add-data "monitor.ico;." wpdebugger.py
```

El ejecutable resultante se encontrará en la carpeta `dist`.

## Licencia

Este proyecto está disponible bajo la licencia MIT. Ver el archivo [LICENSE](LICENSE) para más detalles.

## Contribuir

¿Quieres contribuir al proyecto? ¡Genial! Consulta nuestras [pautas de contribución](CONTRIBUTING.md) para comenzar.

## Autor

Desarrollado por [Luis Eduardo G. González](https://devactivo.com), especialista en WordPress y desarrollo web.

- 🌐 [DevActivo.com](https://devactivo.com)
- 🔧 [EspecialistaEnWP.com](https://especialistaenwp.com)

Especializado en desarrollo de plugins, temas (clásicos y Gutenberg), Laravel, React y más.
