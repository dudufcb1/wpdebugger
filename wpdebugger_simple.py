import sys
import os

# =========================================================================
# VERSIÓN LEGACY: Esta es la versión original con la interfaz tradicional
# Se mantiene por compatibilidad, pero se recomienda usar wpdebugger.py
# que utiliza la interfaz moderna con CustomTkinter
# =========================================================================

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

try:
    # Intentar importar directamente
    from src.main_simple import main
except ImportError:
    try:
        # Intentar importar sin el prefijo src
        from main_simple import main
    except ImportError:
        print("Error: No se pudo importar el módulo main_simple")
        sys.exit(1)

if __name__ == "__main__":
    print("NOTA: Estás usando la versión legacy con interfaz tradicional.")
    print("Para usar la versión moderna con CustomTkinter, ejecuta 'wpdebugger.py'")
    main()
