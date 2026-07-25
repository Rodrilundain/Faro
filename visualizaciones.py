"""
Visualizaciones del proyecto FARO.

Genera imágenes PNG en la carpeta 'graficos/' a partir de los registros
procesados y del tablero de riesgo. Usa el backend 'Agg' de matplotlib para
poder generar imágenes sin ventana gráfica (útil al correr desde el servidor).
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
GRAFICOS_DIR = BASE_DIR / "graficos"

# Colores de semáforo consistentes en todos los gráficos.
COLORES_NIVEL = {
    "Rojo": "#d64545",
    "Naranja": "#e8873b",
    "Amarillo": "#e8c63b",
    "Verde": "#4a9d5b",
    "Sin datos suficientes": "#9aa0a6",
}


def _guardar(fig, nombre):
    GRAFICOS_DIR.mkdir(parents=True, exist_ok=True)
    ruta = GRAFICOS_DIR / nombre
    fig.tight_layout()
    fig.savefig(ruta, dpi=110)
    plt.close(fig)
    print(f"Gráfico guardado: {nombre}")


def grafico_distribucion_niveles(df_riesgo):
    conteo = df_riesgo["nivel_riesgo"].value_counts()
    orden = ["Rojo", "Naranja", "Amarillo", "Verde", "Sin datos suficientes"]
    conteo = conteo.reindex([n for n in orden if n in conteo.index])

    fig, ax = plt.subplots(figsize=(7, 4.5))
    colores = [COLORES_NIVEL.get(n, "#888") for n in conteo.index]
    ax.bar(conteo.index, conteo.values, color=colores)
    ax.set_title("Estudiantes por nivel de riesgo")
    ax.set_ylabel("Cantidad de estudiantes")
    for i, v in enumerate(conteo.values):
        ax.text(i, v + 0.1, str(int(v)), ha="center", va="bottom")
    _guardar(fig, "distribucion_niveles_riesgo.png")


def grafico_top_estudiantes(df_riesgo, top=10):
    df = df_riesgo.sort_values("puntaje_riesgo", ascending=False).head(top)
    etiquetas = df.get("nombre", df["id_estudiante"].astype(str))

    fig, ax = plt.subplots(figsize=(8, 5))
    colores = [COLORES_NIVEL.get(n, "#888") for n in df["nivel_riesgo"]]
    ax.barh(etiquetas[::-1], df["puntaje_riesgo"][::-1], color=colores[::-1])
    ax.set_title(f"Top {top} estudiantes por puntaje de riesgo")
    ax.set_xlabel("Puntaje de riesgo (0-100)")
    _guardar(fig, "top_estudiantes_riesgo.png")


def grafico_dispersion(df_procesado):
    cuadrantes = df_procesado["cuadrante"].unique()
    fig, ax = plt.subplots(figsize=(6.5, 6))
    for cuad in cuadrantes:
        sub = df_procesado[df_procesado["cuadrante"] == cuad]
        ax.scatter(sub["valencia"], sub["activacion"], s=8, alpha=0.4, label=cuad)
    ax.axhline(0, color="#555", linewidth=0.8)
    ax.axvline(0, color="#555", linewidth=0.8)
    ax.set_title("Registros en el plano valencia-activación")
    ax.set_xlabel("Valencia (desagradable  ←→  agradable)")
    ax.set_ylabel("Activación (baja  ←→  alta)")
    ax.legend(fontsize=7, markerscale=2)
    _guardar(fig, "dispersion_valencia_activacion.png")


def grafico_distribucion_emociones(df_procesado):
    conteo = df_procesado["etiqueta_emocional"].value_counts()
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(conteo.index, conteo.values, color="#5b7fa6")
    ax.set_title("Distribución de etiquetas emocionales (todos los registros)")
    ax.set_ylabel("Cantidad de registros")
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    _guardar(fig, "distribucion_emociones.png")


def grafico_riesgo_por_grupo(df_riesgo):
    if "grupo" not in df_riesgo.columns:
        return
    resumen = df_riesgo.groupby("grupo")["puntaje_riesgo"].mean().sort_values()
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(resumen.index, resumen.values, color="#7a6fa6")
    ax.set_title("Puntaje de riesgo promedio por grupo")
    ax.set_ylabel("Puntaje promedio (0-100)")
    plt.setp(ax.get_xticklabels(), rotation=0)
    _guardar(fig, "riesgo_por_grupo.png")


def grafico_serie_temporal(df_procesado):
    df = df_procesado.copy()
    df["fecha_hora"] = pd.to_datetime(df["fecha_hora"], errors="coerce")
    df = df.dropna(subset=["fecha_hora"])
    por_semana = (
        df.set_index("fecha_hora")
        .resample("W")["valencia"]
        .mean()
    )
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(por_semana.index, por_semana.values, marker="o", color="#4a9d5b")
    ax.axhline(0, color="#d64545", linewidth=0.8, linestyle="--")
    ax.set_title("Valencia promedio semanal (todo el centro)")
    ax.set_ylabel("Valencia promedio")
    ax.set_xlabel("Semana")
    _guardar(fig, "serie_temporal_valencia.png")


def generar_todos(df_procesado, df_riesgo):
    """Genera todos los gráficos disponibles según los datos recibidos."""
    if not df_procesado.empty:
        grafico_dispersion(df_procesado)
        grafico_distribucion_emociones(df_procesado)
        grafico_serie_temporal(df_procesado)
    if not df_riesgo.empty:
        grafico_distribucion_niveles(df_riesgo)
        grafico_top_estudiantes(df_riesgo)
        grafico_riesgo_por_grupo(df_riesgo)
