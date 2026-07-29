"""Pruebas de regresion para el motor de riesgo en Python.

Usan el dataset de ejemplo real (datos/*.csv) para asegurar que el pipeline
(sanitacion -> procesamiento emocional -> calculo de riesgo) siga dando los
mismos resultados que el panel publicado. Si estas pruebas fallan despues de
un cambio, es una senal de que el modelo de riesgo cambio de comportamiento
sin querer.
"""

import pandas as pd

from calculo_riesgo import (
    _CONFIG_PATH,
    _cargar_config,
    _clamp,
    _racha_negativa_maxima,
    calcular_riesgo,
)
from procesamiento_emocional import procesar_emociones
from sanitacion import sanitizar

DATOS_DIR = _CONFIG_PATH.parent.parent / "datos"


def _cargar_riesgo_de_ejemplo():
      registros = pd.read_csv(DATOS_DIR / "registros_emocionales.csv", encoding="utf-8")
      etiquetas = pd.read_csv(DATOS_DIR / "etiquetas_emocionales.csv", encoding="utf-8")
      validos, _invalidos = sanitizar(registros)
      procesados = procesar_emociones(validos, etiquetas)
      return calcular_riesgo(procesados)


def test_clamp_limita_al_rango():
      assert _clamp(-5, 0, 1) == 0
      assert _clamp(5, 0, 1) == 1
      assert _clamp(0.5, 0, 1) == 0.5


def test_racha_negativa_maxima_cuenta_consecutivos():
      assert _racha_negativa_maxima([0.1, -0.1, -0.2, -0.3, 0.4, -0.1]) == 3
      assert _racha_negativa_maxima([0.1, 0.2]) == 0


def test_config_usa_defecto_si_no_existe_el_archivo():
      cfg = _cargar_config(_CONFIG_PATH.parent / "no_existe_esto.json")
      assert cfg["umbrales"]["rojo"] == 70
      assert round(sum(cfg["pesos"].values()), 6) == 1.0


def test_config_riesgo_json_tiene_pesos_que_suman_uno():
      cfg = _cargar_config(_CONFIG_PATH)
      assert round(sum(cfg["pesos"].values()), 6) == 1.0
      assert cfg["umbrales"]["rojo"] > cfg["umbrales"]["naranja"] > cfg["umbrales"]["amarillo"]


def test_pipeline_dataset_de_ejemplo_no_cambia_de_comportamiento():
      df_riesgo = _cargar_riesgo_de_ejemplo()
      assert len(df_riesgo) == 30

      conteo = df_riesgo["nivel_riesgo"].value_counts().to_dict()
      assert conteo.get("Rojo", 0) == 3
      assert conteo.get("Naranja", 0) == 1
      assert conteo.get("Amarillo", 0) == 1
      assert conteo.get("Verde", 0) == 25

      assert df_riesgo["puntaje_riesgo"].max() == 86.7
