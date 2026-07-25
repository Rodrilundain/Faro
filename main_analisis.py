"""
PASO 4 - Análisis agregado.

A partir del tablero de riesgo genera resúmenes por nivel y por grupo, y los
guarda como CSV en 'salida/'. Sirve para tener una mirada de conjunto del centro
educativo, no solo estudiante por estudiante.
"""

from pathlib import Path

import pandas as pd

import analisis

BASE_DIR = Path(__file__).resolve().parent
SALIDA_DIR = BASE_DIR / "salida"


def main():
    ruta_tablero = SALIDA_DIR / "tablero_riesgo.csv"
    if not ruta_tablero.exists():
        print("No existe tablero_riesgo.csv. Corré primero el cálculo de riesgo.")
        raise SystemExit(1)

    df_riesgo = pd.read_csv(ruta_tablero, encoding="utf-8")

    resumen_nivel = analisis.resumen_por_nivel(df_riesgo)
    resumen_grupo = analisis.resumen_por_grupo(df_riesgo)

    resumen_nivel.to_csv(SALIDA_DIR / "resumen_por_nivel.csv", index=False, encoding="utf-8")
    resumen_grupo.to_csv(SALIDA_DIR / "resumen_por_grupo.csv", index=False, encoding="utf-8")

    print("Resumen por nivel:")
    print(resumen_nivel.to_string(index=False))
    print("\nResumen por grupo:")
    print(resumen_grupo.to_string(index=False))


main()
