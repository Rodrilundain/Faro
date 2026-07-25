"""
Orquestador del pipeline FARO.

Ejecuta los pasos en orden y guarda TODO lo que imprime cada paso en
'resultados.txt', clasificando cada línea como INFO o ERROR y con marca de
tiempo y nombre de paso. Si un paso falla, se detiene el pipeline y queda el
traceback registrado.

Mantiene el mismo mecanismo del proyecto de clase (redirección de stdout con un
'Tee' + importlib para correr cada paso como módulo).
"""

import re
import sys
import contextlib
import importlib
import traceback
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except (AttributeError, OSError):
    pass

BASE_DIR = Path(__file__).resolve().parent
RUTA_RESULTADOS = BASE_DIR / "resultados.txt"

PASOS = [
    ("Sanitacion", "main_sanitacion"),
    ("Procesamiento", "main_procesamiento"),
    ("Riesgo", "main_riesgo"),
    ("Analisis", "main_analisis"),
    ("Visualizaciones", "main_visualizaciones"),
]

PATRON_EXCEPCION = re.compile(r"[A-Za-z]+Error\b")
PATRON_ERROR_TEXTO = re.compile(r"\berror\b|no se pudo|no se pudieron|excepción|traceback")


class _Tee:
    """Escribe en la consola real y guarda una copia del texto emitido."""

    def __init__(self, consola):
        self.consola = consola
        self.buffer = []

    def write(self, texto):
        self.consola.write(texto)
        self.buffer.append(texto)
        return len(texto)

    def flush(self):
        self.consola.flush()

    def reconfigure(self, *args, **kwargs):
        pass

    @property
    def encoding(self):
        return getattr(self.consola, "encoding", "utf-8")


def _clasificar_linea(linea):
    if PATRON_EXCEPCION.search(linea):
        return "ERROR"
    if PATRON_ERROR_TEXTO.search(linea.lower()):
        return "ERROR"
    return "INFO"


def _guardar_en_resultados(marca_tiempo, nombre_paso, texto):
    with open(RUTA_RESULTADOS, "a", encoding="utf-8") as archivo:
        for linea in texto.splitlines():
            if not linea.strip():
                continue
            tipo = _clasificar_linea(linea)
            archivo.write(f"{marca_tiempo} | PASO={nombre_paso} | TIPO={tipo} | {linea}\n")


def _ejecutar_paso(nombre_paso, nombre_modulo):
    marca_tiempo = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n=== {nombre_paso} ===")

    tee = _Tee(sys.stdout)
    try:
        with contextlib.redirect_stdout(tee):
            importlib.import_module(nombre_modulo)
    except Exception:
        tee.buffer.append(traceback.format_exc())
        _guardar_en_resultados(marca_tiempo, nombre_paso, "".join(tee.buffer))
        print(f"\nEl paso '{nombre_paso}' falló. Se detiene el pipeline. Ver resultados.txt")
        raise

    _guardar_en_resultados(marca_tiempo, nombre_paso, "".join(tee.buffer))


def main():
    marca_inicio = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(RUTA_RESULTADOS, "a", encoding="utf-8") as archivo:
        archivo.write(f"\n{'=' * 80}\nEJECUCIÓN INICIADA: {marca_inicio}\n{'=' * 80}\n")

    for nombre_paso, nombre_modulo in PASOS:
        _ejecutar_paso(nombre_paso, nombre_modulo)

    print("\nPipeline completo finalizado. Resultados guardados en resultados.txt")


main()
