"""
Calculo de riesgo emocional por estudiante  (MODELO SOLO EMOCIONAL).

A partir de los registros ya procesados (valencia, activacion, intensidad,
cuadrante, etiqueta), este modulo resume el estado de cada estudiante y produce
un puntaje de riesgo de 0 a 100 y un nivel con forma de semaforo.

El puntaje es TRANSPARENTE: es una suma ponderada de factores emocionales
observables, y para cada estudiante se guardan las "senales" en texto que
explican por que se le asigno ese nivel. No usa texto libre ni datos externos:
solo las variables emocionales, como se acordo.

  ┌───────────────────────────────────────────────────────────────────────┐
    │  ADVERTENCIA DE USO                                                     │
      │  Esto NO es un diagnostico ni una prediccion clinica. Es una ayuda de   │
        │  priorizacion para que un profesional (psicologo / asistente social)    │
          │  decida a quien mirar primero. La decision y la intervencion son        │
            │  siempre humanas y profesionales.                                       │
              └───────────────────────────────────────────────────────────────────────┘
              """

import json
from pathlib import Path

import numpy as np
import pandas as pd

# Los pesos y umbrales del modelo viven en config/riesgo_config.json, que
# tambien lee (embebido por exportar_sitio.py en datos_faro.js) web/faro_core.js.
# Asi Python y JavaScript comparten una unica fuente de verdad y no pueden
# desincronizarse entre si.
_CONFIG_PATH = Path(__file__).resolve().parent / "config" / "riesgo_config.json"


def _cargar_config(ruta=None):
      """Carga pesos y umbrales desde config/riesgo_config.json.

          Si el archivo no existe o el JSON es invalido, se usan los valores por
              defecto (los mismos que tenia este modulo antes de externalizar la
                  configuracion), para que el pipeline nunca se rompa por esto.
                      """
      ruta = ruta or _CONFIG_PATH
      defecto = {
          "dias_ventana": 28,
          "min_registros": 4,
          "pesos": {
              "valencia_negativa": 0.25,
              "prop_negativos": 0.15,
              "prop_apagamiento": 0.25,
              "persistencia": 0.15,
              "tendencia": 0.15,
              "intensidad_negativa": 0.05,
          },
          "umbrales": {"rojo": 70, "naranja": 45, "amarillo": 25},
      }
      try:
                with open(ruta, "r", encoding="utf-8") as f:
                              cfg = json.load(f)
      except (FileNotFoundError, json.JSONDecodeError, OSError):
                return defecto
            for clave in ("dias_ventana", "min_registros", "pesos", "umbrales"):
                      if clave in cfg:
                                    defecto[clave] = cfg[clave]
                            return defecto


_CONFIG = _cargar_config(_CONFIG_PATH)

# Ventana reciente sobre la que se mira el estado actual del estudiante.
DIAS_VENTANA = _CONFIG["dias_ventana"]
# Minimo de registros recientes para poder evaluar con confianza.
MIN_REGISTROS = _CONFIG["min_registros"]
# Pesos de cada factor (suman 1.0). El apagamiento (cuadrante Triste) y la
# valencia negativa pesan mas porque son las senales mas asociadas al retiro
# emocional que interesa detectar temprano.
PESOS = _CONFIG["pesos"]
# Umbrales del semaforo (sobre el puntaje 0-100).
UMBRAL_ROJO = _CONFIG["umbrales"]["rojo"]
UMBRAL_NARANJA = _CONFIG["umbrales"]["naranja"]
UMBRAL_AMARILLO = _CONFIG["umbrales"]["amarillo"]


def _clamp(valor, minimo=0.0, maximo=1.0):
      return max(minimo, min(maximo, valor))


def _racha_negativa_maxima(valencias_ordenadas):
      """Racha maxima de registros consecutivos con valencia negativa."""
    maxima = 0
    actual = 0
    for valencia in valencias_ordenadas:
              if valencia < 0:
                            actual += 1
                            maxima = max(maxima, actual)
else:
            actual = 0
    return maxima


def _tendencia_valencia(fechas, valencias):
      """
          Pendiente de la valencia en el tiempo (unidades de valencia por dia).
              Negativa = el estudiante viene empeorando. Usa regresion lineal simple.
                  """
    if len(valencias) < 2:
              return 0.0
    dias = np.array([(f - fechas.min()).total_seconds() / 86400 for f in fechas])
    if dias.max() == dias.min():
              return 0.0
    pendiente = np.polyfit(dias, np.array(valencias, dtype=float), 1)[0]
    return float(pendiente)


def _senales(factores, resumen):
      """Traduce los factores altos a frases legibles para el profesional."""
    senales = []
    if factores["valencia_negativa"] >= 0.5:
              senales.append(
                            f"Valencia promedio reciente negativa ({resumen['valencia_prom_reciente']:.2f})."
              )
    if factores["prop_apagamiento"] >= 0.4:
              senales.append(
                            f"{resumen['prop_apagamiento'] * 100:.0f}% de registros de apagamiento "
                            "(baja energia + animo bajo, cuadrante Triste)."
              )
    if factores["prop_negativos"] >= 0.5:
              senales.append(
                            f"{resumen['prop_negativos'] * 100:.0f}% de registros recientes negativos."
              )
    if factores["persistencia"] >= 0.5:
              senales.append(
                            f"Racha de {resumen['racha_negativa']} registros negativos seguidos."
              )
    if factores["tendencia"] >= 0.5:
              senales.append("Tendencia a empeorar en las ultimas semanas.")
    if factores["intensidad_negativa"] >= 0.6:
              senales.append("Emociones negativas de alta intensidad.")
    if not senales:
              senales.append("Sin senales emocionales de alerta relevantes.")
    return senales


def _evaluar_estudiante(df_estudiante, fecha_referencia):
      """Calcula el resumen y el puntaje de riesgo de un solo estudiante."""
    df_estudiante = df_estudiante.sort_values("fecha_hora")

    inicio_ventana = fecha_referencia - pd.Timedelta(days=DIAS_VENTANA)
    recientes = df_estudiante[df_estudiante["fecha_hora"] >= inicio_ventana]

    # Si no hay actividad reciente, se evalua sobre los ultimos registros disponibles.
    if len(recientes) < MIN_REGISTROS:
              recientes = df_estudiante.tail(MIN_REGISTROS)

    n_recientes = len(recientes)
    valencias = recientes["valencia"].tolist()
    valencia_prom = float(np.mean(valencias)) if valencias else 0.0

    prop_negativos = float(np.mean([v < 0 for v in valencias])) if valencias else 0.0
    prop_apagamiento = (
              float(np.mean(recientes["cuadrante"] == "Negativa-Baja")) if n_recientes else 0.0
    )
    racha = _racha_negativa_maxima(valencias)
    pendiente = _tendencia_valencia(recientes["fecha_hora"], valencias)

    negativos = recientes[recientes["valencia"] < 0]
    intensidad_neg_prom = (
              float(negativos["intensidad_normalizada"].mean()) if len(negativos) else 0.0
    )

    # --- Factores normalizados a 0..1 ---
    factores = {
              # valencia -0.2 -> 0 ; valencia -1.0 -> 1
        "valencia_negativa": _clamp((-valencia_prom - 0.2) / 0.8),
              "prop_negativos": _clamp(prop_negativos),
              "prop_apagamiento": _clamp(prop_apagamiento),
              # 6 o mas registros negativos seguidos -> 1
              "persistencia": _clamp(racha / 6.0),
              # una caida proyectada de 0.6 de valencia en la ventana -> 1
              "tendencia": _clamp((-pendiente * DIAS_VENTANA) / 0.6),
              "intensidad_negativa": _clamp(intensidad_neg_prom),
    }

    puntaje = sum(PESOS[k] * factores[k] for k in PESOS) * 100
    puntaje = round(puntaje, 1)

    datos_suficientes = len(df_estudiante) >= MIN_REGISTROS
    if not datos_suficientes:
              nivel = "Sin datos suficientes"
elif puntaje >= UMBRAL_ROJO:
        nivel = "Rojo"
elif puntaje >= UMBRAL_NARANJA:
        nivel = "Naranja"
elif puntaje >= UMBRAL_AMARILLO:
        nivel = "Amarillo"
else:
        nivel = "Verde"

    resumen = {
              "n_registros": len(df_estudiante),
              "n_recientes": n_recientes,
              "valencia_prom_reciente": round(valencia_prom, 3),
              "activacion_prom_reciente": round(float(recientes["activacion"].mean()), 3),
              "prop_negativos": round(prop_negativos, 3),
              "prop_apagamiento": round(prop_apagamiento, 3),
              "racha_negativa": racha,
              "tendencia_valencia": round(pendiente, 5),
              "intensidad_neg_prom": round(intensidad_neg_prom, 3),
              "puntaje_riesgo": puntaje,
              "nivel_riesgo": nivel,
    }
    resumen["senales"] = " | ".join(_senales(factores, resumen))
    return resumen


def calcular_riesgo(df_procesado):
      """
          Recibe el DataFrame de registros ya procesados y devuelve un DataFrame con
              una fila por estudiante, ordenado de mayor a menor riesgo.
                  """
    if df_procesado.empty:
              print("No hay registros procesados para calcular riesgo.")
        return pd.DataFrame()

    df = df_procesado.copy()
    df["fecha_hora"] = pd.to_datetime(df["fecha_hora"], errors="coerce")
    fecha_referencia = df["fecha_hora"].max()

    filas = []
    for id_estudiante, grupo in df.groupby("id_estudiante"):
              resumen = _evaluar_estudiante(grupo, fecha_referencia)
        resumen["id_estudiante"] = int(id_estudiante)
        filas.append(resumen)

    df_riesgo = pd.DataFrame(filas)

    orden_nivel = {"Rojo": 0, "Naranja": 1, "Amarillo": 2, "Verde": 3,
                                      "Sin datos suficientes": 4}
    df_riesgo["_orden"] = df_riesgo["nivel_riesgo"].map(orden_nivel)
    df_riesgo = df_riesgo.sort_values(
              ["_orden", "puntaje_riesgo"], ascending=[True, False]
    ).drop(columns="_orden")

    # Reordenar columnas: identificacion primero.
    columnas = ["id_estudiante", "nivel_riesgo", "puntaje_riesgo"] + [
              c for c in df_riesgo.columns
              if c not in ("id_estudiante", "nivel_riesgo", "puntaje_riesgo")
    ]
    return df_riesgo[columnas].reset_index(drop=True)
