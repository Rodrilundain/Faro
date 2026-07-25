"""
PASO 5 - Visualizaciones.

Genera todos los gráficos PNG en la carpeta 'graficos/' a partir de las
evaluaciones emocionales y del tablero de riesgo.
"""

from pathlib import Path

import pandas as pd

import visualizaciones

BASE_DIR = Path(__file__).resolve().parent
SALIDA_DIR = BASE_DIR / "salida"


def main():
    ruta_procesado = SALIDA_DIR / "evaluaciones_emocionales.csv"
    ruta_tablero = SALIDA_DIR / "tablero_riesgo.csv"

    df_procesado = pd.read_csv(ruta_procesado, encoding="utf-8") if ruta_procesado.exists() else pd.DataFrame()
    df_riesgo = pd.read_csv(ruta_tablero, encoding="utf-8") if ruta_tablero.exists() else pd.DataFrame()

    if df_procesado.empty and df_riesgo.empty:
        print("No hay datos para graficar.")
        raise SystemExit(1)

    visualizaciones.generar_todos(df_procesado, df_riesgo)
    print("Visualizaciones generadas en 'graficos/'.")


main()
