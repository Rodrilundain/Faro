/*
 * faro_core.js — Núcleo del pipeline FARO reescrito en JavaScript.
 *
 * Replica EXACTAMENTE la lógica de los módulos Python (sanitacion.py,
 * procesamiento_emocional.py, calculo_riesgo.py) para que el sitio pueda
 * procesar un CSV en el navegador, sin backend.
 *
 * No usa el DOM: sirve tanto en el navegador como en Node (para tests).
 */
(function (global) {
  "use strict";

  // ---- Constantes del modelo (idénticas a calculo_riesgo.py) ----
  var DIAS_VENTANA = 28;
  var MIN_REGISTROS = 4;
  var PESOS = {
    valencia_negativa: 0.25,
    prop_negativos: 0.15,
    prop_apagamiento: 0.25,
    persistencia: 0.15,
    tendencia: 0.15,
    intensidad_negativa: 0.05,
  };
  var UMBRAL_ROJO = 70, UMBRAL_NARANJA = 45, UMBRAL_AMARILLO = 25;
  var COLUMNAS_OBLIGATORIAS = ["id_registro", "id_estudiante", "id_contexto",
                               "fecha_hora", "valencia", "activacion"];
  var RAIZ2 = Math.sqrt(2);

  // ---- Utilidades ----
  function clamp(v, min, max) {
    if (min === undefined) min = 0;
    if (max === undefined) max = 1;
    return Math.max(min, Math.min(max, v));
  }

  function esNumero(v) {
    if (v === null || v === undefined || v === "") return false;
    return !isNaN(parseFloat(v)) && isFinite(v);
  }

  function parseFecha(texto) {
    // Acepta "YYYY-MM-DD HH:MM" o "YYYY-MM-DD HH:MM:SS" o con 'T'.
    if (!texto) return null;
    var t = String(texto).trim().replace("T", " ");
    var m = t.match(/^(\d{4})-(\d{2})-(\d{2})[ ]?(\d{2})?:?(\d{2})?/);
    if (!m) {
      var d0 = new Date(t);
      return isNaN(d0.getTime()) ? null : d0;
    }
    var d = new Date(
      parseInt(m[1], 10), parseInt(m[2], 10) - 1, parseInt(m[3], 10),
      parseInt(m[4] || "0", 10), parseInt(m[5] || "0", 10)
    );
    return isNaN(d.getTime()) ? null : d;
  }

  function fmtFecha(d) {
    function p(n) { return (n < 10 ? "0" : "") + n; }
    return d.getFullYear() + "-" + p(d.getMonth() + 1) + "-" + p(d.getDate()) +
           " " + p(d.getHours()) + ":" + p(d.getMinutes());
  }

  // ---- Parser CSV (maneja comillas y comas dentro de campos) ----
  function parseCSV(texto) {
    var filas = [];
    var campo = "", fila = [], enComillas = false;
    texto = texto.replace(/\r\n/g, "\n").replace(/\r/g, "\n");
    for (var i = 0; i < texto.length; i++) {
      var c = texto[i];
      if (enComillas) {
        if (c === '"') {
          if (texto[i + 1] === '"') { campo += '"'; i++; }
          else enComillas = false;
        } else campo += c;
      } else {
        if (c === '"') enComillas = true;
        else if (c === ",") { fila.push(campo); campo = ""; }
        else if (c === "\n") { fila.push(campo); filas.push(fila); fila = []; campo = ""; }
        else campo += c;
      }
    }
    if (campo !== "" || fila.length) { fila.push(campo); filas.push(fila); }
    if (!filas.length) return [];
    var cabecera = filas[0].map(function (h) { return h.trim(); });
    var objetos = [];
    for (var r = 1; r < filas.length; r++) {
      if (filas[r].length === 1 && filas[r][0] === "") continue; // línea vacía
      var obj = {};
      for (var k = 0; k < cabecera.length; k++) obj[cabecera[k]] = filas[r][k];
      objetos.push(obj);
    }
    return objetos;
  }

  // ---- PASO 1: Sanitación ----
  function validarFila(fila) {
    for (var i = 0; i < COLUMNAS_OBLIGATORIAS.length; i++) {
      var col = COLUMNAS_OBLIGATORIAS[i];
      if (!(col in fila) || fila[col] === "" || fila[col] === null || fila[col] === undefined)
        return "Falta valor en '" + col + "'";
    }
    if (!esNumero(fila.id_registro)) return "id_registro no es entero";
    if (!esNumero(fila.id_estudiante)) return "id_estudiante no es entero";
    if (!esNumero(fila.valencia)) return "valencia no es numérica";
    if (!esNumero(fila.activacion)) return "activacion no es numérica";
    var v = parseFloat(fila.valencia), a = parseFloat(fila.activacion);
    if (v < -1 || v > 1) return "valencia fuera de rango [-1,1]";
    if (a < -1 || a > 1) return "activacion fuera de rango [-1,1]";
    if (!parseFecha(fila.fecha_hora)) return "fecha_hora inválida";
    return null;
  }

  function sanitizar(registros) {
    var vistos = {}, validos = [], invalidos = [];
    registros.forEach(function (fila) {
      var clave = JSON.stringify(fila);
      if (vistos[clave]) return; // duplicado exacto
      vistos[clave] = true;
      var motivo = validarFila(fila);
      if (motivo) {
        var inv = Object.assign({}, fila);
        inv.motivo_rechazo = motivo;
        invalidos.push(inv);
      } else {
        validos.push({
          id_registro: parseInt(fila.id_registro, 10),
          id_estudiante: parseInt(fila.id_estudiante, 10),
          id_contexto: parseInt(fila.id_contexto, 10),
          fecha_hora: parseFecha(fila.fecha_hora),
          valencia: parseFloat(fila.valencia),
          activacion: parseFloat(fila.activacion),
          comentario: fila.comentario || "",
        });
      }
    });
    return { validos: validos, invalidos: invalidos };
  }

  // ---- PASO 2: Procesamiento emocional ----
  function cuadrante(v, a, umbral) {
    if (umbral === undefined) umbral = 0.30;
    if (Math.abs(v) < umbral && Math.abs(a) < umbral) return "Centro";
    if (v >= 0 && a >= 0) return "Positiva-Alta";
    if (v >= 0 && a < 0) return "Positiva-Baja";
    if (v < 0 && a >= 0) return "Negativa-Alta";
    return "Negativa-Baja";
  }

  function clasificar(v, a, etiquetas) {
    for (var i = 0; i < etiquetas.length; i++) {
      var e = etiquetas[i];
      if (v >= e.valencia_min && v <= e.valencia_max &&
          a >= e.activacion_min && a <= e.activacion_max) return e.nombre_etiqueta;
    }
    return "Sin clasificar";
  }

  function procesarEmociones(validos, etiquetas) {
    return validos.map(function (r) {
      var intensidad = Math.sqrt(r.valencia * r.valencia + r.activacion * r.activacion);
      return Object.assign({}, r, {
        intensidad: intensidad,
        intensidad_normalizada: intensidad / RAIZ2,
        cuadrante: cuadrante(r.valencia, r.activacion),
        etiqueta_emocional: clasificar(r.valencia, r.activacion, etiquetas),
      });
    });
  }

  // ---- PASO 3: Cálculo de riesgo ----
  function rachaNegativa(valencias) {
    var max = 0, act = 0;
    valencias.forEach(function (v) {
      if (v < 0) { act++; if (act > max) max = act; } else act = 0;
    });
    return max;
  }

  function pendienteValencia(fechas, valencias) {
    if (valencias.length < 2) return 0;
    var min = Math.min.apply(null, fechas.map(function (f) { return f.getTime(); }));
    var xs = fechas.map(function (f) { return (f.getTime() - min) / 86400000; });
    var maxx = Math.max.apply(null, xs);
    if (maxx === Math.min.apply(null, xs)) return 0;
    var n = xs.length;
    var mx = xs.reduce(function (a, b) { return a + b; }, 0) / n;
    var my = valencias.reduce(function (a, b) { return a + b; }, 0) / n;
    var num = 0, den = 0;
    for (var i = 0; i < n; i++) { num += (xs[i] - mx) * (valencias[i] - my); den += (xs[i] - mx) * (xs[i] - mx); }
    return den === 0 ? 0 : num / den;
  }

  function senalesDe(f, resumen) {
    var s = [];
    if (f.valencia_negativa >= 0.5) s.push("Valencia promedio reciente negativa (" + resumen.valencia_prom_reciente.toFixed(2) + ").");
    if (f.prop_apagamiento >= 0.4) s.push(Math.round(resumen.prop_apagamiento * 100) + "% de registros de apagamiento (baja energía + ánimo bajo, cuadrante Triste).");
    if (f.prop_negativos >= 0.5) s.push(Math.round(resumen.prop_negativos * 100) + "% de registros recientes negativos.");
    if (f.persistencia >= 0.5) s.push("Racha de " + resumen.racha_negativa + " registros negativos seguidos.");
    if (f.tendencia >= 0.5) s.push("Tendencia a empeorar en las últimas semanas.");
    if (f.intensidad_negativa >= 0.6) s.push("Emociones negativas de alta intensidad.");
    if (!s.length) s.push("Sin señales emocionales de alerta relevantes.");
    return s;
  }

  function evaluarEstudiante(regs, fechaRef) {
    regs = regs.slice().sort(function (a, b) { return a.fecha_hora - b.fecha_hora; });
    var inicio = new Date(fechaRef.getTime() - DIAS_VENTANA * 86400000);
    var recientes = regs.filter(function (r) { return r.fecha_hora >= inicio; });
    if (recientes.length < MIN_REGISTROS) recientes = regs.slice(-MIN_REGISTROS);

    var valencias = recientes.map(function (r) { return r.valencia; });
    var prom = valencias.length ? valencias.reduce(function (a, b) { return a + b; }, 0) / valencias.length : 0;
    var actProm = recientes.length ? recientes.reduce(function (a, b) { return a + b.activacion; }, 0) / recientes.length : 0;
    var propNeg = valencias.length ? valencias.filter(function (v) { return v < 0; }).length / valencias.length : 0;
    var propApag = recientes.length ? recientes.filter(function (r) { return r.cuadrante === "Negativa-Baja"; }).length / recientes.length : 0;
    var racha = rachaNegativa(valencias);
    var pend = pendienteValencia(recientes.map(function (r) { return r.fecha_hora; }), valencias);
    var negativos = recientes.filter(function (r) { return r.valencia < 0; });
    var intNeg = negativos.length ? negativos.reduce(function (a, b) { return a + b.intensidad_normalizada; }, 0) / negativos.length : 0;

    var factores = {
      valencia_negativa: clamp((-prom - 0.2) / 0.8),
      prop_negativos: clamp(propNeg),
      prop_apagamiento: clamp(propApag),
      persistencia: clamp(racha / 6),
      tendencia: clamp((-pend * DIAS_VENTANA) / 0.6),
      intensidad_negativa: clamp(intNeg),
    };
    var puntaje = 0;
    for (var k in PESOS) puntaje += PESOS[k] * factores[k];
    puntaje = Math.round(puntaje * 1000) / 10;

    var nivel;
    if (regs.length < MIN_REGISTROS) nivel = "Sin datos suficientes";
    else if (puntaje >= UMBRAL_ROJO) nivel = "Rojo";
    else if (puntaje >= UMBRAL_NARANJA) nivel = "Naranja";
    else if (puntaje >= UMBRAL_AMARILLO) nivel = "Amarillo";
    else nivel = "Verde";

    var resumen = {
      n_registros: regs.length,
      n_recientes: recientes.length,
      valencia_prom_reciente: Math.round(prom * 1000) / 1000,
      activacion_prom_reciente: Math.round(actProm * 1000) / 1000,
      prop_negativos: Math.round(propNeg * 1000) / 1000,
      prop_apagamiento: Math.round(propApag * 1000) / 1000,
      racha_negativa: racha,
      tendencia_valencia: Math.round(pend * 100000) / 100000,
      intensidad_neg_prom: Math.round(intNeg * 1000) / 1000,
      puntaje_riesgo: puntaje,
      nivel_riesgo: nivel,
    };
    resumen.senales = senalesDe(factores, resumen);
    return resumen;
  }

  function calcularRiesgo(procesados) {
    if (!procesados.length) return [];
    var fechaRef = new Date(Math.max.apply(null, procesados.map(function (r) { return r.fecha_hora.getTime(); })));
    var porEst = {};
    procesados.forEach(function (r) {
      (porEst[r.id_estudiante] = porEst[r.id_estudiante] || []).push(r);
    });
    var filas = [];
    Object.keys(porEst).forEach(function (id) {
      var resumen = evaluarEstudiante(porEst[id], fechaRef);
      resumen.id_estudiante = parseInt(id, 10);
      filas.push(resumen);
    });
    var orden = { Rojo: 0, Naranja: 1, Amarillo: 2, Verde: 3, "Sin datos suficientes": 4 };
    filas.sort(function (a, b) {
      if (orden[a.nivel_riesgo] !== orden[b.nivel_riesgo]) return orden[a.nivel_riesgo] - orden[b.nivel_riesgo];
      return b.puntaje_riesgo - a.puntaje_riesgo;
    });
    return filas;
  }

  // ---- PASO 4/enriquecimiento: unir estudiantes + historial + resúmenes ----
  function construirResultado(csvTexto, referencia) {
    var registros = parseCSV(csvTexto);
    var san = sanitizar(registros);
    var procesados = procesarEmociones(san.validos, referencia.etiquetas);
    var riesgo = calcularRiesgo(procesados);

    // Historial por estudiante (cronológico, últimos 30).
    var hist = {};
    procesados.forEach(function (r) { (hist[r.id_estudiante] = hist[r.id_estudiante] || []).push(r); });
    Object.keys(hist).forEach(function (id) {
      hist[id].sort(function (a, b) { return a.fecha_hora - b.fecha_hora; });
      hist[id] = hist[id].slice(-30).map(function (r) {
        return {
          fecha_hora: fmtFecha(r.fecha_hora),
          valencia: r.valencia, activacion: r.activacion,
          intensidad_normalizada: Math.round(r.intensidad_normalizada * 1000) / 1000,
          cuadrante: r.cuadrante, etiqueta_emocional: r.etiqueta_emocional,
          comentario: r.comentario,
        };
      });
    });

    var estById = {};
    (referencia.estudiantes || []).forEach(function (e) { estById[e.id_estudiante] = e; });

    var estudiantes = riesgo.map(function (r) {
      var e = estById[r.id_estudiante] || {};
      return {
        id_estudiante: r.id_estudiante,
        nombre: e.nombre || ("ID " + r.id_estudiante),
        grupo: e.grupo || "—",
        edad: e.edad || null, sexo: e.sexo || null,
        nivel_riesgo: r.nivel_riesgo, puntaje_riesgo: r.puntaje_riesgo,
        valencia_prom_reciente: r.valencia_prom_reciente,
        activacion_prom_reciente: r.activacion_prom_reciente,
        prop_negativos: r.prop_negativos, prop_apagamiento: r.prop_apagamiento,
        racha_negativa: r.racha_negativa, tendencia_valencia: r.tendencia_valencia,
        senales: r.senales, historial: hist[r.id_estudiante] || [],
      };
    });

    // Conteo por nivel.
    var conteo = {};
    estudiantes.forEach(function (e) { conteo[e.nivel_riesgo] = (conteo[e.nivel_riesgo] || 0) + 1; });

    // Resumen por grupo.
    var grupos = {};
    estudiantes.forEach(function (e) {
      var g = grupos[e.grupo] = grupos[e.grupo] || { grupo: e.grupo, estudiantes: 0, suma: 0, alertas: 0 };
      g.estudiantes++; g.suma += e.puntaje_riesgo;
      if (e.nivel_riesgo === "Rojo" || e.nivel_riesgo === "Naranja") g.alertas++;
    });
    var resumenGrupo = Object.keys(grupos).map(function (k) {
      var g = grupos[k];
      return { grupo: g.grupo, estudiantes: g.estudiantes,
               puntaje_promedio: Math.round((g.suma / g.estudiantes) * 10) / 10, alertas: g.alertas };
    }).sort(function (a, b) { return b.puntaje_promedio - a.puntaje_promedio; });

    return {
      conteo_nivel: conteo,
      estudiantes: estudiantes,
      resumen_grupo: resumenGrupo,
      n_validos: san.validos.length,
      n_invalidos: san.invalidos.length,
      invalidos: san.invalidos.slice(0, 50),
    };
  }

  var FARO = {
    parseCSV: parseCSV, sanitizar: sanitizar, procesarEmociones: procesarEmociones,
    calcularRiesgo: calcularRiesgo, construirResultado: construirResultado,
    cuadrante: cuadrante, clasificar: clasificar,
  };

  if (typeof module !== "undefined" && module.exports) module.exports = FARO;
  else global.FARO = FARO;
})(typeof window !== "undefined" ? window : this);
