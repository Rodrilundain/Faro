# Protocolo de uso e intervención — FARO

> **FARO es una herramienta de apoyo a la tarea profesional, no un instrumento
> de diagnóstico.** Señala prioridades para que un psicólogo o asistente social
> decida a quién mirar primero. Ninguna acción sobre un estudiante debe basarse
> únicamente en el puntaje del sistema.

---

## 1. Qué hace y qué NO hace FARO

**Hace:**
- Ordena a los estudiantes por señales emocionales de alerta.
- Muestra *por qué* aparece cada alerta (señales transparentes).
- Permite ver la evolución de cada estudiante en el tiempo.

**No hace:**
- No diagnostica trastornos ni "predice" conductas.
- No reemplaza la entrevista, la observación ni el criterio profesional.
- No debe usarse para etiquetar, exponer ni sancionar a ningún estudiante.

---

## 2. Niveles del semáforo y acción sugerida

| Nivel | Puntaje | Lectura | Acción sugerida del profesional |
|-------|---------|---------|---------------------------------|
| 🟢 **Verde** | 0–24 | Sin señales relevantes | Seguimiento normal del grupo. |
| 🟡 **Amarillo** | 25–44 | Señales leves / a observar | Observación reforzada. Conversar de forma natural. Revisar en 1–2 semanas. |
| 🟠 **Naranja** | 45–69 | Atención | Contacto directo con el estudiante en instancia de orientación. Evaluar situación familiar y vincular. Registrar. |
| 🔴 **Rojo** | 70–100 | Prioridad | Entrevista lo antes posible. Activar el protocolo del centro y de ANEP/MSP. Considerar contacto con la familia y derivación a salud. |
| ⚪ **Sin datos** | — | Pocos registros | Promover que el estudiante complete más check-ins antes de concluir. |

> Los umbrales son configurables en `calculo_riesgo.py` (constantes `UMBRAL_*`).
> Deben ajustarse junto al equipo de psicología del centro, no de forma aislada.

---

## 3. Señales que pesan más

El modelo es **solo emocional** y da más peso a:
- **Apagamiento** (cuadrante *Triste*: ánimo bajo + baja energía), que suele
  asociarse a retraimiento y pérdida de interés.
- **Valencia negativa sostenida** en las últimas semanas.
- **Tendencia a empeorar** (la valencia baja con el tiempo).
- **Persistencia** (rachas de registros negativos consecutivos).

---

## 4. Ante señales de riesgo de vida

Si en una entrevista o registro aparecen indicios de riesgo de autolesión o
suicidio, **actuar de inmediato** según el protocolo del centro y no dejar
solo/a al estudiante. Recursos en Uruguay:

- **Línea Vida (prevención del suicidio, MSP/ASSE):** `0800 0767` · `*0767` desde celular.
- **Emergencias:** `911`.
- Protocolos de referencia: *Protocolo de actuación en intento de autoeliminación
  y suicidio en instituciones educativas* (ANEP) y líneas del MSP.

---

## 5. Cuidado de los datos

- Los registros emocionales son **datos sensibles de menores**. Deben tratarse
  con confidencialidad y acceso restringido al equipo autorizado.
- Usar identificadores internos y evitar exponer nombres fuera del equipo.
- Este proyecto usa **datos sintéticos de ejemplo**; para uso real se requiere
  consentimiento, marco institucional y resguardo acorde a la normativa vigente.
