"""
cargar_registros_mysql.py

Carga los registros emocionales del CSV (el mismo origen que usa el pipeline,
definido en config.txt) dentro de la tabla 'registros_emocionales' de la base
MySQL 'faro'.

Sirve para tener en MySQL exactamente los mismos datos que procesa el pipeline.
Es IDEMPOTENTE: vacía la tabla y la vuelve a cargar, así se puede correr las
veces que haga falta sin duplicar filas.

Requiere XAMPP/MySQL corriendo y la base 'faro' creada (ver faro_schema.sql).
Reutiliza la conexión de carga_base_datos.py y la lectura de carga_csv.py.

Uso:
    python cargar_registros_mysql.py
"""

import sys
from pathlib import Path

import pandas as pd
import pymysql

import carga_csv
from carga_base_datos import CONFIG_MYSQL

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

BASE_DIR = Path(__file__).resolve().parent
TABLA = "registros_emocionales"
COLUMNAS = ["id_registro", "id_estudiante", "id_contexto",
            "fecha_hora", "valencia", "activacion", "comentario"]


def _leer_registros():
    """Lee el CSV desde el origen de config.txt; si falla, usa el CSV local."""
    df = carga_csv.leer_csv_desde_config(ruta_config=str(BASE_DIR / "config.txt"))
    if df.empty:
        ruta = BASE_DIR / "datos" / "registros_emocionales.csv"
        print(f"Usando CSV local por defecto: {ruta}")
        df = carga_csv.leer_registros_emocionales(ruta.parent, ruta.name)
    return df


def cargar():
    df = _leer_registros()
    if df.empty:
        print("No hay registros para cargar. Abortando.")
        return

    faltan = [c for c in COLUMNAS if c not in df.columns]
    if faltan:
        print("El CSV no tiene las columnas obligatorias:", faltan)
        return

    print(f"Registros a cargar: {len(df)}")

    try:
        # utf8mb4 para que las tildes de los comentarios queden bien.
        conexion = pymysql.connect(charset="utf8mb4", **CONFIG_MYSQL)
    except pymysql.err.Error as error:
        print(f"No se pudo conectar a MySQL ({error}).")
        print("Verificá que XAMPP/MySQL esté activo y que exista la base "
              "'faro' (importá faro_schema.sql).")
        return

    try:
        marcadores = ",".join(["%s"] * len(COLUMNAS))
        sql = f"INSERT INTO {TABLA} ({','.join(COLUMNAS)}) VALUES ({marcadores})"
        filas = [
            (
                int(r.id_registro), int(r.id_estudiante), int(r.id_contexto),
                str(r.fecha_hora), float(r.valencia), float(r.activacion),
                (r.comentario if pd.notna(r.comentario) else ""),
            )
            for r in df.itertuples(index=False)
        ]

        with conexion.cursor() as cursor:
            cursor.execute(f"DELETE FROM {TABLA}")   # idempotente
            cursor.executemany(sql, filas)
        conexion.commit()

        with conexion.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) FROM {TABLA}")
            total = cursor.fetchone()[0]

        print(f"Tabla '{TABLA}' poblada correctamente: {total} filas en MySQL.")
    except pymysql.err.Error as error:
        conexion.rollback()
        print(f"Error al cargar los registros: {error}")
    finally:
        conexion.close()


if __name__ == "__main__":
    cargar()
