"""
Procesamiento emocional (modelo circumplejo valencia-activación).

Este módulo mantiene la lógica del proyecto de clase: a partir de la valencia y
la activación de cada registro calcula intensidad, cuadrante y etiqueta
emocional. Es la base sobre la que después se calcula el riesgo.
"""

import math


def calcular_intensidad(valencia, activacion):
    """
    Intensidad emocional = distancia al punto neutro (0,0) en el plano
    valencia-activación. Dos emociones de la misma etiqueta pueden tener muy
    distinta intensidad; esto lo captura.
    """
    return math.sqrt(valencia ** 2 + activacion ** 2)


def calcular_intensidad_normalizada(intensidad):
    """
    Normaliza la intensidad al rango aproximado 0..1 (el máximo posible es
    raíz de 2, cuando valencia y activación valen 1 en módulo).
    """
    return intensidad / math.sqrt(2)


def determinar_cuadrante(valencia, activacion, umbral_centro=0.30):
    """
    Ubica la emoción en un cuadrante. El umbral_centro define cuándo la emoción
    está tan cerca del neutro que conviene llamarla 'Centro'.
    """
    if abs(valencia) < umbral_centro and abs(activacion) < umbral_centro:
        return "Centro"
    if valencia >= 0 and activacion >= 0:
        return "Positiva-Alta"
    elif valencia >= 0 and activacion < 0:
        return "Positiva-Baja"
    elif valencia < 0 and activacion >= 0:
        return "Negativa-Alta"
    else:
        return "Negativa-Baja"


def clasificar_emocion(valencia, activacion, df_etiquetas):
    """
    Asigna una etiqueta emocional usando los rangos de la tabla
    etiquetas_emocionales. Devuelve 'Sin clasificar' si ninguna coincide.
    """
    for _, etiqueta in df_etiquetas.iterrows():
        cumple_valencia = (
            valencia >= etiqueta["valencia_min"]
            and valencia <= etiqueta["valencia_max"]
        )
        cumple_activacion = (
            activacion >= etiqueta["activacion_min"]
            and activacion <= etiqueta["activacion_max"]
        )
        if cumple_valencia and cumple_activacion:
            return etiqueta["nombre_etiqueta"]
    return "Sin clasificar"


def procesar_emociones(df_registros_validos, df_etiquetas):
    """
    Agrega a cada registro: intensidad, intensidad_normalizada, cuadrante y
    etiqueta_emocional. Devuelve un DataFrame nuevo (no modifica el original).
    """
    df = df_registros_validos.copy()

    df["intensidad"] = df.apply(
        lambda fila: calcular_intensidad(fila["valencia"], fila["activacion"]),
        axis=1,
    )
    df["intensidad_normalizada"] = df["intensidad"].apply(
        calcular_intensidad_normalizada
    )
    df["cuadrante"] = df.apply(
        lambda fila: determinar_cuadrante(fila["valencia"], fila["activacion"]),
        axis=1,
    )
    df["etiqueta_emocional"] = df.apply(
        lambda fila: clasificar_emocion(
            fila["valencia"], fila["activacion"], df_etiquetas
        ),
        axis=1,
    )
    return df
