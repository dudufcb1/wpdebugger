import os
import shutil
import subprocess
import sys

def build_executable():
    print("Iniciando compilación del ejecutable...")

    # Verificar que estamos en el directorio correcto
    if not os.path.exists('wpdebugger_simple.py'):
        print("Error: No se encontró el archivo wpdebugger_simple.py")
        print("Asegúrate de ejecutar este script desde el directorio raíz del proyecto")
        return False

    # Crear directorio de build si no existe
    if not os.path.exists('build'):
        os.makedirs('build')

    # Limpiar directorio dist si existe
    if os.path.exists('dist'):
        try:
            shutil.rmtree('dist')
        except PermissionError:
            print("No se pudo eliminar el directorio dist. Puede que algunos archivos estén en uso.")
            print("Intentando continuar de todos modos...")

    # Opciones de PyInstaller
    # Usar un nombre diferente para evitar conflictos
    exe_name = 'WPDebugViewer_new'

    # Preparar las rutas para los datos adicionales
    data_files = []
    if os.path.exists('config.json'):
        data_files.append('config.json;.')

    # Añadir los módulos de src
    src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
    for file in os.listdir(src_path):
        if file.endswith('.py'):
            data_files.append(f'src/{file};src')

    # Construir las opciones de PyInstaller
    pyinstaller_options = [
        'pyinstaller',
        f'--name={exe_name}',
        '--onefile',
        '--windowed',
        '--icon=monitor.ico' if os.path.exists('monitor.ico') else '',
        '--clean',
    ]

    # Añadir los datos adicionales
    for data in data_files:
        pyinstaller_options.append(f'--add-data={data}')

    # Añadir el script principal
    pyinstaller_options.append('wpdebugger_simple.py')

    # Eliminar opciones vacías
    pyinstaller_options = [opt for opt in pyinstaller_options if opt]

    # Ejecutar PyInstaller
    print("Ejecutando PyInstaller con las siguientes opciones:")
    print(" ".join(pyinstaller_options))

    try:
        subprocess.run(pyinstaller_options, check=True)

        # Verificar que se creó el ejecutable
        executable_path = os.path.join('dist', f'{exe_name}.exe')
        if os.path.exists(executable_path):
            print(f"\nCompilación exitosa. Ejecutable creado en: {os.path.abspath(executable_path)}")

            # Copiar el ejecutable a la raíz del proyecto con el nombre final
            final_name = 'WPDebugViewer.exe'
            try:
                # Intentar eliminar el archivo existente si es posible
                if os.path.exists(final_name):
                    try:
                        os.remove(final_name)
                    except PermissionError:
                        # Si no se puede eliminar, usar un nombre alternativo
                        final_name = 'WPDebugViewer_latest.exe'
                        print(f"No se pudo sobrescribir el ejecutable existente. Usando nombre alternativo: {final_name}")

                # Copiar el nuevo ejecutable
                shutil.copy(executable_path, final_name)
                print(f"Ejecutable copiado a: {os.path.abspath(final_name)}")
            except Exception as e:
                print(f"Advertencia: No se pudo copiar el ejecutable a la raíz: {e}")
                print(f"Puedes encontrar el ejecutable en: {os.path.abspath(executable_path)}")

            return True
        else:
            print(f"Error: No se encontró el ejecutable en {executable_path}")
            return False

    except subprocess.CalledProcessError as e:
        print(f"Error al ejecutar PyInstaller: {e}")
        return False
    except Exception as e:
        print(f"Error inesperado: {e}")
        return False

if __name__ == "__main__":
    success = build_executable()
    sys.exit(0 if success else 1)
