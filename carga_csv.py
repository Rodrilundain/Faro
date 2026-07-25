"""
Lectura de CSV de registros emocionales.

Mantiene el patrón del proyecto de clase: puede leer desde una ruta local o una
URL http/https, y define el origen en config.txt (clave 'origen_csv').
"""

from pathlib import Path
import pandas as pd

COLUMNAS_ESPERADAS = [
    "id_registro",
    "id_estudiante",
    "id_contexto",
    "fecha_hora",
    "valencia",
    "activacion",
    "comentario",
]


def _leer_csv(fuente):
    """Lee un CSV probando UTF-8 y luego latin1 si falla la decodificación."""
    try:
        return pd.read_csv(fuente, encoding="utf-8")
    except UnicodeDecodeError:
        return pd.read_csv(fuente, encoding="latin1")
    except FileNotFoundError:
        print(f"No se encontró el archivo: {fuente}")
        return pd.DataFrame()
    except Exception as error:
        print(f"Error al leer el archivo CSV ({fuente}):", error)
        return pd.DataFrame()


def obtener_valor_config(clave, ruta_config="config.txt"):
    """Lee un archivo 'clave=valor' y devuelve el valor de 'clave', o None."""
    try:
        with open(ruta_config, "r", encoding="utf-8") as archivo:
            for linea in archivo:
                linea = linea.strip()
                if not linea or linea.startswith("#") or "=" not in linea:
                    continue
                clave_linea, valor = linea.split("=", 1)
                if clave_linea.strip() == clave:
                    return valor.strip()
    except FileNotFoundError:
        print(f"No se encontró el archivo de configuración: {ruta_config}")
        return None

    print(f"No se definió '{clave}' en {ruta_config}.")
    return None


def leer_csv_desde_config(clave="origen_csv", ruta_config="config.txt"):
    """Lee el CSV principal según la ruta/URL definida en config.txt."""
    origen = obtener_valor_config(clave, ruta_config)
    if not origen:
        return pd.DataFrame()
    if origen.startswith("http://") or origen.startswith("https://"):
        print(f"Descargando CSV desde: {origen}")
    return _leer_csv(origen)


def leer_registros_emocionales(ruta_carpeta, nombre_archivo):
    """Lee el CSV de registros emocionales desde una carpeta y nombre dados."""
    return _leer_csv(Path(ruta_carpeta) / nombre_archivo)


def verificar_columnas_csv(df):
    """Verifica que el DataFrame tenga todas las columnas obligatorias."""
    columnas_csv = list(df.columns)
    faltantes = [c for c in COLUMNAS_ESPERADAS if c not in columnas_csv]

    if faltantes:
        print("Error: faltan columnas obligatorias:")
        for columna in faltantes:
            print("-", columna)
        return False

    print("El CSV tiene todas las columnas necesarias.")
    return True
