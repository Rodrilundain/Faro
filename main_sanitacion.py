"""
PASO 1 - Sanitación.

Lee el CSV de registros emocionales indicado en config.txt, verifica que tenga
las columnas necesarias y separa los registros válidos de los inválidos.
Guarda ambos en la carpeta 'salida/'.
"""

from pathlib import Path

import carga_csv
import sanitacion

BASE_DIR = Path(__file__).resolve().parent
SALIDA_DIR = BASE_DIR / "salida"


def main():
    SALIDA_DIR.mkdir(parents=True, exist_ok=True)

    print("Leyendo CSV de origen definido en config.txt...")
    df = carga_csv.leer_csv_desde_config(ruta_config=str(BASE_DIR / "config.txt"))

    if df.empty:
        print("No se pudieron leer registros. Se detiene el paso de sanitación.")
        raise SystemExit(1)

    if not carga_csv.verificar_columnas_csv(df):
        print("El CSV no tiene las columnas obligatorias.")
        raise SystemExit(1)

    df_validos, df_invalidos = sanitacion.sanitizar(df)

    df_validos.to_csv(SALIDA_DIR / "registros_validos.csv", index=False, encoding="utf-8")
    df_invalidos.to_csv(SALIDA_DIR / "registros_invalidos.csv", index=False, encoding="utf-8")

    print(f"Guardados {len(df_validos)} válidos y {len(df_invalidos)} inválidos en 'salida/'.")


main()
