"""
Acceso a la base de datos MySQL (XAMPP) del proyecto.

Igual que en el proyecto de clase usamos pymysql contra una base MySQL/MariaDB
(la que provee XAMPP con phpMyAdmin). La base se llama 'faro' y se crea con el
script faro_schema.sql.

IMPORTANTE (uso real en escuelas): si XAMPP no está corriendo o la base no
existe, cada función cae automáticamente a leer el CSV equivalente de la carpeta
'datos/'. Así la herramienta funciona igual para una demo, y usa la base cuando
está disponible. Cada función informa por consola de dónde salieron los datos.
"""

from pathlib import Path
import warnings

import pandas as pd
import pymysql
from pymysql import Error

BASE_DIR = Path(__file__).resolve().parent
DATOS_DIR = BASE_DIR / "datos"

CONFIG_MYSQL = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "faro",
}


def conectar_base_datos():
    """Intenta conectar a MySQL. Devuelve la conexión o None si falla."""
    try:
        conexion = pymysql.connect(**CONFIG_MYSQL)
        print("Conexión exitosa a la base de datos MySQL 'faro'.")
        return conexion
    except Error as error:
        print(f"Aviso: MySQL no disponible ({error}). Se usan los CSV de 'datos/' como respaldo.")
        return None


def cerrar_conexion(conexion):
    """Cierra la conexión si existe."""
    try:
        if conexion is not None:
            conexion.close()
            print("Conexión cerrada correctamente.")
    except Error as error:
        print(f"Error al cerrar la conexión: {error}")


def _leer_tabla(conexion, nombre_tabla, csv_respaldo):
    """
    Lee una tabla desde MySQL; si no hay conexión o falla, lee el CSV de
    respaldo con el mismo contenido.
    """
    if conexion is not None:
        try:
            with warnings.catch_warnings():
                # pandas avisa que prefiere SQLAlchemy; para el proyecto alcanza pymysql.
                warnings.simplefilter("ignore")
                df = pd.read_sql(f"SELECT * FROM {nombre_tabla}", conexion)
            print(f"Tabla '{nombre_tabla}' cargada desde MySQL ({len(df)} filas).")
            return df
        except Exception as error:
            print(f"Error al leer '{nombre_tabla}' de MySQL ({error}). Uso el CSV de respaldo.")

    ruta_csv = DATOS_DIR / csv_respaldo
    df = pd.read_csv(ruta_csv, encoding="utf-8")
    print(f"Tabla '{nombre_tabla}' cargada desde CSV '{csv_respaldo}' ({len(df)} filas).")
    return df


def cargar_estudiantes(conexion):
    return _leer_tabla(conexion, "estudiantes", "estudiantes.csv")


def cargar_contextos(conexion):
    return _leer_tabla(conexion, "contextos", "contextos.csv")


def cargar_etiquetas_emocionales(conexion):
    return _leer_tabla(conexion, "etiquetas_emocionales", "etiquetas_emocionales.csv")
