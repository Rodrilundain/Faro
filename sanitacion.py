"""
Sanitación / validación de los registros emocionales.

Recibe el DataFrame crudo del CSV y separa los registros válidos de los
inválidos, aplicando reglas claras. Cada registro inválido conserva el motivo
del rechazo, para poder auditarlo después.

Reglas de validación:
  - No pueden faltar columnas obligatorias.
  - valencia y activacion deben ser numéricas y estar en el rango [-1, 1].
  - fecha_hora debe poder interpretarse como fecha/hora válida.
  - id_registro e id_estudiante deben ser enteros presentes.
  - Se eliminan filas totalmente duplicadas.
"""

import pandas as pd

COLUMNAS_OBLIGATORIAS = [
    "id_registro",
    "id_estudiante",
    "id_contexto",
    "fecha_hora",
    "valencia",
    "activacion",
]

VALOR_MIN = -1.0
VALOR_MAX = 1.0


def _a_numero(valor):
    """Convierte a float o devuelve None si no se puede."""
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def _a_entero(valor):
    """Convierte a int o devuelve None si no se puede."""
    try:
        return int(float(valor))
    except (TypeError, ValueError):
        return None


def _validar_fila(fila):
    """Devuelve None si la fila es válida, o un texto con el motivo de rechazo."""
    for columna in COLUMNAS_OBLIGATORIAS:
        if columna not in fila or pd.isna(fila[columna]):
            return f"Falta valor en '{columna}'"

    if _a_entero(fila["id_registro"]) is None:
        return "id_registro no es entero"
    if _a_entero(fila["id_estudiante"]) is None:
        return "id_estudiante no es entero"

    valencia = _a_numero(fila["valencia"])
    activacion = _a_numero(fila["activacion"])

    if valencia is None:
        return "valencia no es numérica"
    if activacion is None:
        return "activacion no es numérica"
    if not (VALOR_MIN <= valencia <= VALOR_MAX):
        return f"valencia fuera de rango [{VALOR_MIN},{VALOR_MAX}]"
    if not (VALOR_MIN <= activacion <= VALOR_MAX):
        return f"activacion fuera de rango [{VALOR_MIN},{VALOR_MAX}]"

    fecha = pd.to_datetime(fila["fecha_hora"], errors="coerce")
    if pd.isna(fecha):
        return "fecha_hora inválida"

    return None


def sanitizar(df):
    """
    Separa registros válidos e inválidos.

    Devuelve (df_validos, df_invalidos). En df_validos las columnas numéricas
    quedan convertidas y se agrega 'fecha_hora' normalizada a datetime.
    """
    if df.empty:
        print("El DataFrame de entrada está vacío. No hay nada que sanitizar.")
        return df.copy(), df.copy()

    total_inicial = len(df)
    df = df.drop_duplicates().copy()
    duplicados = total_inicial - len(df)
    if duplicados:
        print(f"Se eliminaron {duplicados} filas duplicadas.")

    motivos = df.apply(_validar_fila, axis=1)

    mascara_validos = motivos.isna()
    df_validos = df[mascara_validos].copy()
    df_invalidos = df[~mascara_validos].copy()
    df_invalidos["motivo_rechazo"] = motivos[~mascara_validos]

    # Normalizar tipos en los válidos.
    df_validos["id_registro"] = df_validos["id_registro"].apply(_a_entero)
    df_validos["id_estudiante"] = df_validos["id_estudiante"].apply(_a_entero)
    df_validos["id_contexto"] = df_validos["id_contexto"].apply(_a_entero)
    df_validos["valencia"] = df_validos["valencia"].apply(_a_numero)
    df_validos["activacion"] = df_validos["activacion"].apply(_a_numero)
    df_validos["fecha_hora"] = pd.to_datetime(
        df_validos["fecha_hora"], errors="coerce"
    )

    print(f"Registros válidos: {len(df_validos)}")
    print(f"Registros inválidos: {len(df_invalidos)}")

    return df_validos, df_invalidos
