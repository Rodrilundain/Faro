"""
Buscador de resultados.txt.

Permite filtrar el log del pipeline por palabra clave, paso, tipo (INFO/ERROR) o
rango de fechas. Se puede usar desde el panel web o por línea de comandos.
"""

import sys
import argparse
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

BASE_DIR = Path(__file__).resolve().parent
RUTA_RESULTADOS = BASE_DIR / "resultados.txt"


def _parsear_linea(linea):
    partes = linea.rstrip("\n").split(" | ", 3)
    if len(partes) != 4:
        return None

    marca_texto, paso_texto, tipo_texto, mensaje = partes
    try:
        marca_tiempo = datetime.strptime(marca_texto, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None

    return {
        "marca_tiempo": marca_tiempo,
        "paso": paso_texto.replace("PASO=", "", 1),
        "tipo": tipo_texto.replace("TIPO=", "", 1),
        "mensaje": mensaje,
        "linea_original": linea.rstrip("\n"),
    }


def buscar(palabra=None, paso=None, tipo=None, desde=None, hasta=None):
    if not RUTA_RESULTADOS.exists():
        print("Todavía no existe resultados.txt. Corré ejecutar_pipeline.py primero.")
        return []

    resultados = []
    with open(RUTA_RESULTADOS, "r", encoding="utf-8") as archivo:
        for linea in archivo:
            registro = _parsear_linea(linea)
            if registro is None:
                continue
            if palabra and palabra.lower() not in registro["mensaje"].lower():
                continue
            if paso and paso.lower() not in registro["paso"].lower():
                continue
            if tipo and tipo.upper() != registro["tipo"]:
                continue
            if desde and registro["marca_tiempo"] < desde:
                continue
            if hasta and registro["marca_tiempo"] > hasta:
                continue
            resultados.append(registro)

    return resultados


def main():
    parser = argparse.ArgumentParser(
        description="Filtra resultados.txt por palabra clave, paso, tipo o rango de fechas."
    )
    parser.add_argument("--palabra")
    parser.add_argument("--paso")
    parser.add_argument("--tipo", choices=["INFO", "ERROR"])
    parser.add_argument("--desde", help="Fecha mínima YYYY-MM-DD")
    parser.add_argument("--hasta", help="Fecha máxima YYYY-MM-DD")
    args = parser.parse_args()

    desde = datetime.strptime(args.desde, "%Y-%m-%d") if args.desde else None
    hasta = datetime.strptime(args.hasta, "%Y-%m-%d") if args.hasta else None

    resultados = buscar(args.palabra, args.paso, args.tipo, desde, hasta)
    if not resultados:
        print("No se encontraron resultados con esos filtros.")
        return

    for registro in resultados:
        print(registro["linea_original"])
    print(f"\nTotal de coincidencias: {len(resultados)}")


if __name__ == "__main__":
    main()
