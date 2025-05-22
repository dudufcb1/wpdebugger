"""
WordPress Debug Viewer - Herramienta para monitorear logs de depuración de WordPress
Desarrollado por Luis Eduardo G. González (DevActivo.com | EspecialistaEnWP.com)
"""

import sys
import os

# Añadir el directorio src al path
base_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(base_dir, 'src')
if src_dir not in sys.path:
    sys.path.append(src_dir)
if base_dir not in sys.path:
    sys.path.append(base_dir)

# Configurar para PyInstaller
def resource_path(relative_path):
    """Obtener la ruta absoluta a un recurso, funciona para dev y para PyInstaller"""
    try:
        # PyInstaller crea un directorio temporal y almacena la ruta en _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Asegurarse de que src esté en el path para PyInstaller
if hasattr(sys, '_MEIPASS'):
    sys.path.append(os.path.join(sys._MEIPASS, 'src'))

# Importar el módulo principal (versión moderna)
from src.main_modern import main

if __name__ == "__main__":
    main()
