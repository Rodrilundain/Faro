"""
Generador de datos de ejemplo para FARO.

Crea 'datos/registros_emocionales.csv' con check-ins de estado de ánimo de
estudiantes a lo largo de ~12 semanas. Es DETERMINISTA (semilla fija), por lo
que siempre produce el mismo dataset: así la demo del panel muestra siempre las
mismas alertas.

Los datos son SINTÉTICOS. No representan personas reales. Sirven únicamente para
probar y demostrar el sistema.

Cada estudiante tiene un "perfil emocional" que define cómo evolucionan sus
registros en el tiempo. La mayoría son estables; unos pocos presentan un
deterioro progresivo (valencia cada vez más negativa y baja activación), que es
justamente el patrón que el sistema debe detectar.
"""

import csv
import random
from datetime import date, datetime, timedelta
from pathlib import Path

# Semilla fija -> dataset reproducible.
random.seed(42)

BASE_DIR = Path(__file__).resolve().parent
RUTA_ESTUDIANTES = BASE_DIR / "datos" / "estudiantes.csv"
RUTA_SALIDA = BASE_DIR / "datos" / "registros_emocionales.csv"

# Ventana temporal del dataset (fija, para que sea reproducible).
FECHA_FIN = date(2026, 7, 25)
SEMANAS = 12
FECHA_INICIO = FECHA_FIN - timedelta(weeks=SEMANAS)

CONTEXTOS = [1, 2, 3, 4, 5, 6, 7, 8]

# Perfil por estudiante: (valencia_base, activacion_base, deterioro_semanal, dispersion)
# deterioro_semanal < 0 => la valencia y la activación bajan con las semanas.
PERFILES = {
    "estable_positivo":  (0.45,  0.35,  0.00, 0.18),
    "estable_neutro":    (0.10,  0.05,  0.00, 0.22),
    "variable":          (0.20,  0.20,  0.00, 0.38),
    "deterioro_leve":    (0.30,  0.25, -0.030, 0.22),
    "deterioro_moderado":(0.18,  0.08, -0.072, 0.24),
    "riesgo_alto":       (0.05, -0.05, -0.085, 0.20),
}

# Asignación de perfiles. Los IDs no listados quedan como estable/variable.
ASIGNACION = {
    17: "riesgo_alto",       # Sofía Díaz
    30: "riesgo_alto",       # Santiago Olivera
    11: "deterioro_moderado",# Lucía Méndez
    4:  "deterioro_moderado",# Diego Fernández
    24: "deterioro_leve",    # Ignacio Ríos
    9:  "deterioro_leve",    # Inés Acosta
    3:  "variable",
    14: "variable",
    22: "variable",
    2:  "estable_neutro",
    8:  "estable_neutro",
    16: "estable_neutro",
    28: "estable_neutro",
}

# Frases de comentario según cuadrante emocional. Son de contexto para el
# profesional; el cálculo de riesgo NO las usa (el modelo es solo emocional).
COMENTARIOS = {
    "Positiva-Alta": [
        "Me sentí con energía y participé en clase.",
        "Buen día, trabajé cómodo con el grupo.",
        "Me gustó la actividad de hoy.",
    ],
    "Positiva-Baja": [
        "Tranquilo, sin novedades.",
        "Día normal, bastante calmado.",
        "Me sentí en paz durante la jornada.",
    ],
    "Negativa-Alta": [
        "Me puse nervioso con la prueba.",
        "Me frustré porque no me salían las cosas.",
        "Discutí con un compañero y quedé alterado.",
    ],
    "Negativa-Baja": [
        "No tenía ganas de nada hoy.",
        "Me sentí bastante bajoneado.",
        "Preferí estar solo, no quería hablar.",
        "Me cuesta todo últimamente.",
    ],
    "Centro": [
        "Día común, ni bien ni mal.",
        "Sin mucho para decir.",
        "Normal.",
    ],
    "Neutra-Alta": [
        "Un poco inquieto, sin razón clara.",
        "Estuve algo acelerado.",
    ],
    "Neutra-Baja": [
        "Cansado, dormí poco.",
        "Con pocas energías hoy.",
        "Agotado, sin ganas.",
    ],
    "Neutra-Media-Alta": [
        "Atento pero un poco tenso.",
        "Alerta durante la clase.",
    ],
}


def _cuadrante(valencia, activacion, umbral=0.30):
    if abs(valencia) < umbral and abs(activacion) < umbral:
        return "Centro"
    if valencia >= 0 and activacion >= 0:
        return "Positiva-Alta"
    if valencia >= 0 and activacion < 0:
        return "Positiva-Baja"
    if valencia < 0 and activacion >= 0:
        return "Negativa-Alta"
    return "Negativa-Baja"


def _comentario_para(valencia, activacion):
    cuad = _cuadrante(valencia, activacion)
    opciones = COMENTARIOS.get(cuad, COMENTARIOS["Centro"])
    return random.choice(opciones)


def _clamp(valor, minimo=-1.0, maximo=1.0):
    return max(minimo, min(maximo, valor))


def _leer_ids_estudiantes():
    ids = []
    with open(RUTA_ESTUDIANTES, "r", encoding="utf-8") as archivo:
        lector = csv.DictReader(archivo)
        for fila in lector:
            ids.append(int(fila["id_estudiante"]))
    return ids


def _perfil_de(id_estudiante):
    nombre_perfil = ASIGNACION.get(id_estudiante)
    if nombre_perfil is None:
        # Reparto por defecto: mezcla de estables para el resto del grupo.
        nombre_perfil = random.choice(
            ["estable_positivo", "estable_positivo", "estable_neutro"]
        )
    return PERFILES[nombre_perfil]


def generar():
    ids = _leer_ids_estudiantes()
    filas = []
    id_registro = 1000

    for id_estudiante in ids:
        val_base, act_base, deterioro, dispersion = _perfil_de(id_estudiante)

        # Frecuencia de check-ins por semana (2 a 4).
        checkins_semana = random.randint(2, 4)

        for semana in range(SEMANAS):
            for _ in range(checkins_semana):
                # A mayor semana, más deterioro acumulado (si el perfil lo tiene).
                corrimiento = deterioro * semana

                valencia = _clamp(random.gauss(val_base + corrimiento, dispersion))
                activacion = _clamp(random.gauss(act_base + corrimiento * 0.7, dispersion))

                valencia = round(valencia, 2)
                activacion = round(activacion, 2)

                dia = FECHA_INICIO + timedelta(
                    weeks=semana, days=random.randint(0, 6)
                )
                hora = f"{random.randint(8, 17):02d}:{random.choice(['00', '15', '30', '45'])}"
                fecha_hora = f"{dia.isoformat()} {hora}"

                filas.append({
                    "id_registro": id_registro,
                    "id_estudiante": id_estudiante,
                    "id_contexto": random.choice(CONTEXTOS),
                    "fecha_hora": fecha_hora,
                    "valencia": valencia,
                    "activacion": activacion,
                    "comentario": _comentario_para(valencia, activacion),
                })
                id_registro += 1

    # Ordenar por fecha para que se parezca a un registro real acumulado.
    filas.sort(key=lambda f: datetime.strptime(f["fecha_hora"], "%Y-%m-%d %H:%M"))

    # Reasignar id_registro correlativo tras ordenar.
    for indice, fila in enumerate(filas, start=1000):
        fila["id_registro"] = indice

    RUTA_SALIDA.parent.mkdir(parents=True, exist_ok=True)
    with open(RUTA_SALIDA, "w", encoding="utf-8", newline="") as archivo:
        campos = ["id_registro", "id_estudiante", "id_contexto",
                  "fecha_hora", "valencia", "activacion", "comentario"]
        escritor = csv.DictWriter(archivo, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(filas)

    print(f"Generados {len(filas)} registros en {RUTA_SALIDA}")


if __name__ == "__main__":
    generar()
