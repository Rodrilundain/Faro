# 🔦 FARO — Sistema de alerta temprana de bienestar estudiantil

FARO es una herramienta pensada para **escuelas y liceos**: procesa los
registros emocionales (check-ins de estado de ánimo) de los estudiantes y genera
un **tablero de riesgo** que ayuda a un **psicólogo o asistente social** a
detectar tempranamente a quiénes conviene acompañar, *antes* de que una
situación de malestar se agrave.

> ⚠️ **Herramienta de apoyo, no de diagnóstico.** Prioriza; no decide. Toda
> intervención es responsabilidad de un profesional humano. Leé
> [`PROTOCOLO_INTERVENCION.md`](PROTOCOLO_INTERVENCION.md).

El proyecto tiene **dos implementaciones de la misma lógica**:

1. **Pipeline en Python** (uso local / análisis, estilo del proyecto de clase):
   sanitación → procesamiento emocional → riesgo → análisis → visualizaciones,
   con log INFO/ERROR y carga desde MySQL/CSV.
2. **Sitio web estático** (para Netlify): reescribe esa misma lógica en
   JavaScript para que funcione **en el navegador, sin backend**. Tiene una
   página para **cargar datos** (subir un CSV o usar el ejemplo) y otra para
   **mostrar** el panel con **gráficos interactivos**.

> El cálculo en JS da resultados idénticos al de Python (validado: mismos niveles
> y puntajes para los 30 estudiantes del ejemplo).

---

## ¿Cómo funciona? (pipeline)

```
CSV de registros → [1] Sanitación → [2] Procesamiento → [3] Riesgo → [4] Análisis → [5] Visualizaciones
                                          emocional      (por alumno)   (agregados)     (gráficos)
```

1. **Sanitación**: valida columnas, rangos de valencia/activación `[-1, 1]`,
   fechas y duplicados. Separa válidos e inválidos.
2. **Procesamiento emocional**: calcula `intensidad`, `cuadrante` y
   `etiqueta_emocional` (modelo circumplejo valencia–activación).
3. **Cálculo de riesgo**: produce un **puntaje 0–100** y un **nivel de semáforo**
   (Verde/Amarillo/Naranja/Rojo), **solo con variables emocionales** y de forma
   **transparente** (guarda las señales que justifican cada alerta).
4. **Análisis**: resúmenes por nivel y por grupo.
5. **Visualizaciones**: gráficos.

- En Python: módulos `sanitacion.py`, `procesamiento_emocional.py`,
  `calculo_riesgo.py`, `analisis.py`, `visualizaciones.py`, orquestados por
  `ejecutar_pipeline.py` (log en `resultados.txt`, filtrable con `buscar_resultados.py`).
- En JavaScript: todo en `web/faro_core.js`.

📄 Diagrama editable del flujo: [`docs/flujo_faro.drawio`](docs/flujo_faro.drawio)
(abrilo en <https://app.diagrams.net>).

---

## Modelo de riesgo (solo emocional)

Para cada estudiante, sobre sus registros recientes (últimos 28 días), combina:

| Factor | Peso | Qué mide |
|--------|------|----------|
| Valencia negativa | 0.25 | Qué tan bajo está el ánimo promedio |
| Apagamiento (cuadrante *Triste*) | 0.25 | Ánimo bajo + baja energía |
| Proporción de registros negativos | 0.15 | Frecuencia del malestar |
| Persistencia | 0.15 | Rachas negativas consecutivas |
| Tendencia | 0.15 | Si viene empeorando en el tiempo |
| Intensidad negativa | 0.05 | Fuerza de las emociones negativas |

Pesos y umbrales: al inicio de `calculo_riesgo.py` (Python) y de `web/faro_core.js` (JS).

---

## Cómo usarlo

### Requisitos (solo para la parte Python)
```bash
pip install -r requirements.txt
```

### A) Generar y publicar el sitio web (Netlify)
```bash
# (opcional) regenerar los datos de ejemplo — determinista
python generar_datos_ejemplo.py

# arma la carpeta sitio/ (embebe datos/ y la lógica JS)
python exportar_sitio.py
```
Después:
- **Arrastrá la carpeta `sitio/`** a <https://app.netlify.com/drop>, o
- conectá un repositorio en Netlify con **publish directory = `sitio`**.

> El sitio calcula todo en el navegador, así que **no necesita correr el pipeline
> Python** antes de exportar. Solo usa los CSV de `datos/`.

**Probar el sitio localmente:** como las dos páginas se comunican por
`sessionStorage`, conviene servirlo (no abrirlo con `file://`):
```bash
cd sitio
python -m http.server 8000
# abrí http://localhost:8000
```

### B) Correr el pipeline en Python (análisis local, opcional)
```bash
python ejecutar_pipeline.py
```
Genera `salida/*.csv`, `graficos/*.png` y el log `resultados.txt`. Si tenés
MySQL/XAMPP con la base `faro` (ver `faro_schema.sql`), lee las tablas de
referencia desde ahí; si no, cae automáticamente a los CSV de `datos/`.

Para volcar los registros del CSV dentro de la tabla `registros_emocionales` de
MySQL (idempotente, se puede correr las veces que quieras):
```bash
python cargar_registros_mysql.py
```

---

## El sitio web (tres páginas)

- **`index.html` — Cargar CSV:** subir tu propio CSV (se procesa en el navegador
  y muestra cuántos registros son válidos/ inválidos) o usar el dataset de ejemplo.
- **`nuevo.html` — Cargar registros:** formulario para ingresar check-ins uno por
  uno (con desplegables de estudiante y contexto). Al terminar podés:
  - **Descargar CSV** (`registros_emocionales.csv`) para el pipeline o para volver
    a cargarlo acá,
  - **Descargar SQL** (`registros.sql`) con los `INSERT INTO registros_emocionales`
    para **importar en phpMyAdmin** y llenar la base MySQL `faro`,
  - **Procesar en el panel** directamente.
- **`panel.html` — Panel:** KPIs por nivel, tabla ordenable con buscador y
  filtros, ficha de cada estudiante (señales + sparkline + historial) y
  **gráficos interactivos**: al tocar una barra o un punto se muestran **los
  datos que lo forman** (y podés abrir la ficha del estudiante).

Todo es responsive y con tema claro/oscuro automático.

> ⚠️ Un sitio estático **no puede** escribir tu archivo CSV ni conectarse a tu
> MySQL local. Por eso `nuevo.html` **descarga** el CSV y **genera el SQL** para
> que vos los apliques (reemplazar el CSV / importar en phpMyAdmin).

---

## Estructura del proyecto

```
FARO/
├── ejecutar_pipeline.py        # Orquestador de los 5 pasos (Python)
├── buscar_resultados.py        # Buscador del log (consola)
├── exportar_sitio.py           # Genera sitio/ para Netlify
├── generar_datos_ejemplo.py    # Generador determinista de datos
├── cargar_registros_mysql.py   # Carga el CSV de registros a la tabla MySQL
├── config.txt · faro_schema.sql · requirements.txt
├── README.md · PROTOCOLO_INTERVENCION.md
│
├── carga_csv.py · carga_base_datos.py       # E/S de datos (Python)
├── sanitacion.py · procesamiento_emocional.py
├── calculo_riesgo.py           # ★ Motor de riesgo (Python)
├── analisis.py · visualizaciones.py
├── main_*.py                   # Un archivo por paso del pipeline
│
├── web/                        # Fuentes del sitio estático
│   ├── carga.html · panel.html
│   ├── estilos.css
│   ├── faro_core.js            # ★ Pipeline completo en JavaScript
│   └── faro_ui.js              # Interfaz + gráficos interactivos
│
├── datos/                      # CSV de entrada (registros, estudiantes, etc.)
├── salida/ · graficos/         # Generados por el pipeline Python
├── sitio/                      # Sitio generado → esto se sube a Netlify
└── docs/                       # Diagrama de flujo (.drawio)
```

---

## Aviso ético y de datos

Los datos incluidos son **sintéticos** y no representan personas reales. Los
registros emocionales de estudiantes son **datos sensibles de menores**: su uso
real exige consentimiento, marco institucional y resguardo según la normativa
vigente. En el sitio web, los datos que subís **se procesan solo en tu navegador**
y no se envían a ningún servidor. Ver detalles en
[`PROTOCOLO_INTERVENCION.md`](PROTOCOLO_INTERVENCION.md).
