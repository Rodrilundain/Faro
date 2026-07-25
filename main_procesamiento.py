"""
PASO 2 - Procesamiento emocional.

Toma los registros válidos, carga las etiquetas emocionales desde la base de
datos (o el CSV de respaldo) y calcula intensidad, cuadrante y etiqueta para
cada registro. Guarda 'salida/evaluaciones_emocionales.csv'.
"""

from pathlib import Path

import pandas as pd

import carga_base_datos
import procesamiento_emocional

BASE_DIR = Path(__file__).resolve().parent
SALIDA_DIR = BASE_DIR / "salida"


def main():
    ruta_validos = SALIDA_DIR / "registros_validos.csv"
    if not ruta_validos.exists():
        print("No existe registros_validos.csv. Corré primero la sanitación.")
        raise SystemExit(1)

    df_validos = pd.read_csv(ruta_validos, encoding="utf-8")
    print(f"Registros válidos leídos: {len(df_validos)}")

    conexion = carga_base_datos.conectar_base_datos()
    df_etiquetas = carga_base_datos.cargar_etiquetas_emocionales(conexion)
    carga_base_datos.cerrar_conexion(conexion)

    if df_etiquetas is None or df_etiquetas.empty:
        print("No se pudieron cargar etiquetas emocionales.")
        raise SystemExit(1)

    df_procesado = procesamiento_emocional.procesar_emociones(df_validos, df_etiquetas)

    ruta_salida = SALIDA_DIR / "evaluaciones_emocionales.csv"
    df_procesado.to_csv(ruta_salida, index=False, encoding="utf-8")

    print(f"Procesados {len(df_procesado)} registros con etiqueta emocional.")
    print("Ejemplo de etiquetas asignadas:")
    print(df_procesado["etiqueta_emocional"].value_counts().to_string())


main()
