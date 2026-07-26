FARO -- Sistema de alerta temprana de bienestar estudiantil
=============================================================

FARO es una herramienta pensada para escuelas y liceos: procesa los
registros emocionales (check-ins de estado de animo) de los estudiantes y genera
un tablero de riesgo que ayuda a un psicologo o asistente social a
detectar tempranamente a quienes conviene acompanar, antes de que una
situacion de malestar se agrave.

Herramienta de apoyo, no de diagnostico. Prioriza; no decide. Toda
intervencion es responsabilidad de un profesional humano. Lee
PROTOCOLO_INTERVENCION.md.

El proyecto tiene dos implementaciones de la misma logica. La primera es un
pipeline en Python (uso local / analisis, estilo del proyecto de clase):
sanitacion, procesamiento emocional, riesgo, analisis y visualizaciones, con
log INFO/ERROR y carga desde MySQL/CSV. La segunda es un sitio web estatico
(para Netlify) que reescribe esa misma logica en JavaScript para que funcione
en el navegador, sin backend. Tiene una pagina para cargar datos (subir un
CSV o usar el ejemplo) y otra para mostrar el panel con graficos interactivos.

Nota: el calculo en JS da resultados identicos al de Python (validado: mismos
niveles y puntajes para los 30 estudiantes del ejemplo, cubierto ahora por
pruebas automaticas, ver mas abajo).


Como funciona el pipeline
-------------------------

CSV de registros, luego Sanitacion, luego Procesamiento emocional, luego
Calculo de riesgo, luego Analisis, luego Visualizaciones.

La sanitacion valida columnas, rangos de valencia y activacion entre -1 y 1,
fechas y duplicados, y separa registros validos de invalidos.

El procesamiento emocional calcula intensidad, cuadrante y etiqueta_emocional
usando el modelo circumplejo valencia-activacion.

El calculo de riesgo produce un puntaje de 0 a 100 y un nivel de semaforo
(Verde, Amarillo, Naranja, Rojo), solo con variables emocionales y de forma
transparente: guarda las senales que justifican cada alerta.

El paso de analisis arma resumenes por nivel y por grupo, y el de
visualizaciones genera los graficos.

En Python estos pasos viven en los modulos sanitacion.py,
procesamiento_emocional.py, calculo_riesgo.py, analisis.py y
visualizaciones.py, orquestados por ejecutar_pipeline.py (log en
resultados.txt, filtrable con buscar_resultados.py). En JavaScript todo el
pipeline esta en web/faro_core.js.

Diagrama editable del flujo: docs/flujo_faro.drawio (abrilo en
https://app.diagrams.net).


Modelo de riesgo (solo emocional)
----------------------------------

Para cada estudiante, sobre sus registros recientes (ultimos 28 dias), se
combinan seis factores: valencia negativa (peso 0.25, que tan bajo esta el
animo promedio), apagamiento o cuadrante Triste (peso 0.25, animo bajo mas
baja energia), proporcion de registros negativos (peso 0.15, frecuencia del
malestar), persistencia (peso 0.15, rachas negativas consecutivas), tendencia
(peso 0.15, si viene empeorando en el tiempo) e intensidad negativa (peso
0.05, fuerza de las emociones negativas).

Los pesos y umbrales viven en config/riesgo_config.json, que es la unica
fuente de verdad: la lee tanto calculo_riesgo.py (Python) como, embebido en
datos_faro.js por exportar_sitio.py, web/faro_core.js (JS). Asi ambas
implementaciones no pueden desincronizarse entre si.


Como usarlo
-----------

Requisitos (solo para la parte Python):

pip install -r requirements.txt

Para generar y publicar el sitio web en Netlify, primero corre (opcional,
regenera los datos de ejemplo de forma determinista):

python generar_datos_ejemplo.py

y despues arma la carpeta sitio/ con:

python exportar_sitio.py

Luego arrastra la carpeta sitio/ a https://app.netlify.com/drop, o conecta un
repositorio en Netlify con publish directory igual a sitio.

Nota: el sitio calcula todo en el navegador, asi que no necesita correr el
pipeline Python antes de exportar. Solo usa los CSV de datos/ y la config de
config/riesgo_config.json.

Para probar el sitio localmente conviene servirlo en vez de abrirlo con
file://, ya que las paginas se comunican por sessionStorage:

cd sitio
python -m http.server 8000

Para correr el pipeline en Python de forma local (analisis, opcional):

python ejecutar_pipeline.py

Esto genera salida/*.csv, graficos/*.png y el log resultados.txt. Si tenes
MySQL o XAMPP con la base faro (ver faro_schema.sql), lee las tablas de
referencia desde ahi; si no, cae automaticamente a los CSV de datos/.


Pruebas automaticas
--------------------

El repo incluye pruebas de regresion para los dos motores de riesgo (Python y
JS), usando el dataset de ejemplo real de datos/ para asegurar que ambas
implementaciones sigan dando los mismos resultados entre si y a lo largo del
tiempo. Un workflow de GitHub Actions (.github/workflows/tests.yml) las corre
automaticamente en cada push y pull request.

Para correr las pruebas de Python:

pip install -r requirements.txt -r requirements-dev.txt
pytest -q

Para correr las pruebas de JavaScript (sin dependencias, solo Node):

node tests/test_faro_core.js


El sitio web (tres paginas)
-----------------------------

index.html es la pagina para cargar CSV: subis tu propio CSV (se procesa en
el navegador y muestra cuantos registros son validos e invalidos) o usas el
dataset de ejemplo.

nuevo.html es la pagina para cargar registros: un formulario para ingresar
check-ins uno por uno. Al terminar podes descargar el CSV, descargar el SQL
para importar en phpMyAdmin, o procesar en el panel directamente.

panel.html es el panel: KPIs por nivel, tabla ordenable con buscador y
filtros (con un boton para limpiarlos y con los filtros reflejados en la URL
para poder compartir un enlace directo a una vista filtrada), ficha de cada
estudiante y graficos interactivos donde tocar una barra o un punto muestra
los datos que lo forman.

Todo es responsivo y con tema claro/oscuro automatico.

Nota: un sitio estatico no puede escribir tu archivo CSV ni conectarse a tu
MySQL local. Por eso nuevo.html descarga el CSV y genera el SQL para que vos
los apliques.


Seguridad y proteccion de datos
----------------------------------

Este proyecto procesa datos emocionales de menores, que son datos sensibles.
Si se llega a usar con datos reales (no sinteticos), recomendamos como minimo
lo siguiente: cifrado en reposo de cualquier base de datos o archivo que
contenga registros reales, y cifrado en transito si se monta un backend real;
seudonimizacion o anonimizacion de los CSV y SQL exportados antes de moverlos
entre maquinas o de subirlos a cualquier repositorio; control de acceso real
a la base de datos en vez de depender solo de que la maquina este protegida;
no versionar datos reales en git; y marco institucional y consentimiento
antes de cualquier uso real, segun la normativa de proteccion de datos y de
menores vigente en tu jurisdiccion (ver PROTOCOLO_INTERVENCION.md).

En el sitio web estatico, los datos que subis se procesan solo en tu
navegador y no se envian a ningun servidor.


Estructura del proyecto
--------------------------

La raiz del proyecto tiene ejecutar_pipeline.py (orquestador de los 5 pasos
en Python), buscar_resultados.py (buscador del log en consola),
exportar_sitio.py (genera sitio/ para Netlify), generar_datos_ejemplo.py
(generador determinista de datos), ademas de config.txt, faro_schema.sql,
requirements.txt, requirements-dev.txt, README.md, PROTOCOLO_INTERVENCION.md
y LICENSE.

La carpeta config/ tiene riesgo_config.json, con los pesos y umbrales
(fuente unica para Python y JS).

Tambien en la raiz estan sanitacion.py, procesamiento_emocional.py,
calculo_riesgo.py (el motor de riesgo), analisis.py, visualizaciones.py y los
main_*.py (un archivo por paso del pipeline).

La carpeta web/ tiene las fuentes del sitio estatico: carga.html,
panel.html, nuevo.html, estilos.css, faro_core.js (el pipeline completo en
JavaScript) y faro_ui.js (la interfaz y los graficos interactivos).

La carpeta tests/ tiene las pruebas automaticas (pytest y Node), y
.github/workflows/ tiene el workflow de CI que las corre en cada push y pull
request.

Por ultimo, datos/ tiene los CSV de entrada (registros, estudiantes, etc.),
salida/ y graficos/ son generados por el pipeline en Python, sitio/ es el
sitio generado que se sube a Netlify, y docs/ tiene el diagrama de flujo
(.drawio).


Aviso etico y de datos
--------------------------

Los datos incluidos son sinteticos y no representan personas reales. Los
registros emocionales de estudiantes son datos sensibles de menores: su uso
real exige consentimiento, marco institucional y resguardo segun la
normativa vigente. En el sitio web, los datos que subis se procesan solo en
tu navegador y no se envian a ningun servidor. Ver detalles en
PROTOCOLO_INTERVENCION.md.
