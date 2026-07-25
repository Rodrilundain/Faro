"""
Exportador del sitio estático para Netlify.

Genera la carpeta 'sitio/' con DOS páginas y todo lo necesario para que funcione
sin backend:

    sitio/
    ├── index.html     (página de carga: subir CSV o usar el ejemplo)
    ├── panel.html     (panel de resultados con gráficos interactivos)
    ├── estilos.css
    ├── faro_core.js   (el pipeline reescrito en JS)
    ├── faro_ui.js     (interfaz + gráficos interactivos)
    └── datos_faro.js  (tablas de referencia + CSV de ejemplo, embebidos)

Todo el cálculo (sanitación, procesamiento emocional y riesgo) ocurre en el
navegador con la MISMA lógica que el pipeline de Python. No se sube nada a
ningún servidor.

Uso:
    python exportar_sitio.py
"""

import json
import shutil
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATOS_DIR = BASE_DIR / "datos"
WEB_DIR = BASE_DIR / "web"
SITIO_DIR = BASE_DIR / "sitio"

ASSETS = ["estilos.css", "faro_core.js", "faro_ui.js"]


def construir_referencia():
    """Arma el objeto de referencia (etiquetas y estudiantes) para el JS."""
    etiquetas = pd.read_csv(DATOS_DIR / "etiquetas_emocionales.csv", encoding="utf-8")
    estudiantes = pd.read_csv(DATOS_DIR / "estudiantes.csv", encoding="utf-8")
    contextos = pd.read_csv(DATOS_DIR / "contextos.csv", encoding="utf-8")

    ref_etiquetas = [
        {
            "nombre_etiqueta": r["nombre_etiqueta"],
            "valencia_min": float(r["valencia_min"]),
            "valencia_max": float(r["valencia_max"]),
            "activacion_min": float(r["activacion_min"]),
            "activacion_max": float(r["activacion_max"]),
        }
        for _, r in etiquetas.iterrows()
    ]
    ref_estudiantes = [
        {
            "id_estudiante": int(r["id_estudiante"]),
            "nombre": r["nombre"],
            "edad": int(r["edad"]) if pd.notna(r["edad"]) else None,
            "sexo": r["sexo"] if pd.notna(r["sexo"]) else None,
            "grupo": r["grupo"] if pd.notna(r["grupo"]) else None,
        }
        for _, r in estudiantes.iterrows()
    ]
    ref_contextos = [
        {
            "id_contexto": int(r["id_contexto"]),
            "ambito": r["ambito"] if pd.notna(r["ambito"]) else "",
            "situacion": r["situacion"] if pd.notna(r["situacion"]) else "",
        }
        for _, r in contextos.iterrows()
    ]
    return {"etiquetas": ref_etiquetas, "estudiantes": ref_estudiantes, "contextos": ref_contextos}


def exportar():
    if not (WEB_DIR / "carga.html").exists():
        raise SystemExit("Falta web/carga.html. ¿Estás en la carpeta del proyecto?")

    SITIO_DIR.mkdir(parents=True, exist_ok=True)

    # 1) Páginas (renombrando carga.html -> index.html)
    shutil.copyfile(WEB_DIR / "carga.html", SITIO_DIR / "index.html")
    shutil.copyfile(WEB_DIR / "nuevo.html", SITIO_DIR / "nuevo.html")
    shutil.copyfile(WEB_DIR / "panel.html", SITIO_DIR / "panel.html")

    # 2) Assets JS/CSS
    for asset in ASSETS:
        shutil.copyfile(WEB_DIR / asset, SITIO_DIR / asset)

    # 3) datos_faro.js con referencia + CSV de ejemplo embebidos
    referencia = construir_referencia()
    ejemplo_csv = (DATOS_DIR / "registros_emocionales.csv").read_text(encoding="utf-8")

    contenido = (
        "// Datos embebidos por exportar_sitio.py — NO editar a mano.\n"
        "window.FARO_REF = " + json.dumps(referencia, ensure_ascii=False) + ";\n"
        "window.FARO_EJEMPLO_CSV = " + json.dumps(ejemplo_csv, ensure_ascii=False) + ";\n"
    )
    (SITIO_DIR / "datos_faro.js").write_text(contenido, encoding="utf-8")

    # 4) Limpiar gráficos PNG viejos del sitio (ahora los gráficos son interactivos)
    viejo = SITIO_DIR / "graficos"
    if viejo.exists():
        shutil.rmtree(viejo)

    print(f"Sitio estático generado en: {SITIO_DIR}")
    print(f"  - index.html (carga) + panel.html (resultados)")
    print(f"  - {len(referencia['estudiantes'])} estudiantes de referencia embebidos")
    print(f"  - CSV de ejemplo embebido ({len(ejemplo_csv)} caracteres)")
    print("Subilo a Netlify: arrastrá la carpeta 'sitio' a https://app.netlify.com/drop")


if __name__ == "__main__":
    exportar()
