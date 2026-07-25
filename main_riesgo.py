"""
PASO 3 - Cálculo de riesgo (solo emocional).

Toma las evaluaciones emocionales, calcula el puntaje y nivel de riesgo por
estudiante, y lo une con los datos de los estudiantes (nombre, grupo). Guarda
'salida/tablero_riesgo.csv', que es la tabla principal que consume el panel.
"""

from pathlib import Path

import pandas as pd

import calculo_riesgo
import carga_base_datos
import analisis

BASE_DIR = Path(__file__).resolve().parent
SALIDA_DIR = BASE_DIR / "salida"


def main():
    ruta_procesado = SALIDA_DIR / "evaluaciones_emocionales.csv"
    if not ruta_procesado.exists():
        print("No existe evaluaciones_emocionales.csv. Corré primero el procesamiento.")
        raise SystemExit(1)

    df_procesado = pd.read_csv(ruta_procesado, encoding="utf-8")

    df_riesgo = calculo_riesgo.calcular_riesgo(df_procesado)
    if df_riesgo.empty:
        print("No se pudo calcular el riesgo.")
        raise SystemExit(1)

    conexion = carga_base_datos.conectar_base_datos()
    df_estudiantes = carga_base_datos.cargar_estudiantes(conexion)
    carga_base_datos.cerrar_conexion(conexion)

    df_riesgo = analisis.unir_con_estudiantes(df_riesgo, df_estudiantes)

    ruta_salida = SALIDA_DIR / "tablero_riesgo.csv"
    df_riesgo.to_csv(ruta_salida, index=False, encoding="utf-8")

    print(f"Tablero de riesgo generado con {len(df_riesgo)} estudiantes.")
    analisis.imprimir_resumen(df_riesgo)


main()
