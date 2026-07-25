/*
 * Pruebas de regresion para el motor de riesgo en JavaScript (web/faro_core.js).
 *
 * Corren con Node puro (sin dependencias externas) y usan el mismo dataset
 * de ejemplo real que las pruebas de Python, para verificar que ambas
 * implementaciones sigan dando los mismos resultados.
 *
 * Uso: node tests/test_faro_core.js
 */
"use strict";

const fs = require("fs");
const path = require("path");
const assert = require("assert");

const FARO = require("../web/faro_core.js");

const DATOS_DIR = path.join(__dirname, "..", "datos");

function leerCSV(nombre) {
    const texto = fs.readFileSync(path.join(DATOS_DIR, nombre), "utf-8");
    return FARO.parseCSV(texto);
}

const etiquetas = leerCSV("etiquetas_emocionales.csv").map(function (e) {
    return {
          nombre_etiqueta: e.nombre_etiqueta,
          valencia_min: parseFloat(e.valencia_min),
          valencia_max: parseFloat(e.valencia_max),
          activacion_min: parseFloat(e.activacion_min),
          activacion_max: parseFloat(e.activacion_max),
    };
});

const estudiantes = leerCSV("estudiantes.csv").map(function (e) {
    return {
          id_estudiante: parseInt(e.id_estudiante, 10),
          nombre: e.nombre,
          edad: e.edad ? parseInt(e.edad, 10) : null,
          sexo: e.sexo || null,
          grupo: e.grupo || null,
    };
});

const referencia = { etiquetas: etiquetas, estudiantes: estudiantes, contextos: [] };
const csvTexto = fs.readFileSync(path.join(DATOS_DIR, "registros_emocionales.csv"), "utf-8");

const resultado = FARO.construirResultado(csvTexto, referencia);

assert.strictEqual(resultado.estudiantes.length, 30, "Deben evaluarse 30 estudiantes");

const conteo = resultado.conteo_nivel;
assert.strictEqual(conteo.Rojo, 3, "Deben ser 3 en Rojo");
assert.strictEqual(conteo.Naranja, 1, "Debe ser 1 en Naranja");
assert.strictEqual(conteo.Amarillo, 1, "Debe ser 1 en Amarillo");
assert.strictEqual(conteo.Verde, 25, "Deben ser 25 en Verde");

const maxPuntaje = Math.max.apply(null, resultado.estudiantes.map(function (e) { return e.puntaje_riesgo; }));
assert.strictEqual(maxPuntaje, 86.7, "El puntaje maximo esperado es 86.7 (dataset de ejemplo)");

console.log("OK: todas las pruebas de faro_core.js pasaron (" + resultado.estudiantes.length + " estudiantes, max=" + maxPuntaje + ").");
