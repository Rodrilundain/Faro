"""
Análisis y enriquecimiento del tablero de riesgo.

Une el resultado del cálculo de riesgo con los datos de los estudiantes (nombre,
grupo, edad) y produce resúmenes agregados útiles para el profesional: cuántos
estudiantes hay en cada nivel, riesgo promedio por grupo, etc.
"""

import pandas as pd


def unir_con_estudiantes(df_riesgo, df_estudiantes):
    """Agrega nombre, edad, sexo y grupo a cada fila del tablero de riesgo."""
    if df_riesgo.empty:
        return df_riesgo

    columnas_est = ["id_estudiante", "nombre", "edad", "sexo", "grupo"]
    columnas_disponibles = [c for c in columnas_est if c in df_estudiantes.columns]

    df = df_riesgo.merge(
        df_estudiantes[columnas_disponibles],
        on="id_estudiante",
        how="left",
    )

    # Poner nombre y grupo cerca del inicio para lectura cómoda.
    frente = ["id_estudiante", "nombre", "grupo", "nivel_riesgo", "puntaje_riesgo"]
    frente = [c for c in frente if c in df.columns]
    resto = [c for c in df.columns if c not in frente]
    return df[frente + resto]


def resumen_por_nivel(df_riesgo):
    """Cuenta estudiantes por nivel de riesgo."""
    if df_riesgo.empty:
        return pd.DataFrame(columns=["nivel_riesgo", "cantidad"])
    conteo = (
        df_riesgo["nivel_riesgo"]
        .value_counts()
        .rename_axis("nivel_riesgo")
        .reset_index(name="cantidad")
    )
    return conteo


def resumen_por_grupo(df_riesgo):
    """Riesgo promedio y cantidad de alertas (naranja+rojo) por grupo."""
    if df_riesgo.empty or "grupo" not in df_riesgo.columns:
        return pd.DataFrame()

    df = df_riesgo.copy()
    df["es_alerta"] = df["nivel_riesgo"].isin(["Naranja", "Rojo"])

    resumen = df.groupby("grupo").agg(
        estudiantes=("id_estudiante", "count"),
        puntaje_promedio=("puntaje_riesgo", "mean"),
        alertas=("es_alerta", "sum"),
    ).reset_index()

    resumen["puntaje_promedio"] = resumen["puntaje_promedio"].round(1)
    return resumen.sort_values("puntaje_promedio", ascending=False)


def imprimir_resumen(df_riesgo):
    """Imprime un resumen legible en consola (queda en resultados.txt)."""
    print("\n--- Resumen por nivel de riesgo ---")
    for _, fila in resumen_por_nivel(df_riesgo).iterrows():
        print(f"  {fila['nivel_riesgo']}: {fila['cantidad']} estudiante(s)")

    alertas = df_riesgo[df_riesgo["nivel_riesgo"].isin(["Naranja", "Rojo"])]
    print(f"\nEstudiantes que requieren atención (Naranja/Rojo): {len(alertas)}")
    for _, fila in alertas.iterrows():
        nombre = fila.get("nombre", f"ID {fila['id_estudiante']}")
        grupo = fila.get("grupo", "")
        print(f"  [{fila['nivel_riesgo']}] {nombre} ({grupo}) "
              f"- puntaje {fila['puntaje_riesgo']} - {fila['senales']}")
