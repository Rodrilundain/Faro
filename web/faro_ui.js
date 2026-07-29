/*
 * faro_ui.js — Interfaz del panel: KPIs, tabla, ficha y gráficos interactivos.
 * Depende de los datos ya calculados (por faro_core.js o embebidos).
 */
(function () {
  "use strict";

  var COLOR = { Rojo: "#e0524f", Naranja: "#ee8b3a", Amarillo: "#e0b91c",
                Verde: "#3f9d63", "Sin datos suficientes": "#9aa4ad" };
  var NS = "http://www.w3.org/2000/svg";

  var estado = { nivel: "", grupo: "", texto: "", orden: "puntaje_riesgo", asc: false, datos: null };

  // ---- helpers ----
  function $(id) { return document.getElementById(id); }
  function fmt(x, d) { d = d === undefined ? 2 : d; return (x === null || x === undefined || isNaN(x)) ? "—" : Number(x).toFixed(d); }
  function pct(x) { return (x === null || x === undefined || isNaN(x)) ? "—" : Math.round(x * 100) + "%"; }
  function claseNivel(n) { return (n || "Sin").split(" ")[0]; }
  function svgEl(tag, attrs) {
    var e = document.createElementNS(NS, tag);
    for (var k in attrs) e.setAttribute(k, attrs[k]);
    return e;
  }
  function esc(s) { var d = document.createElement("div"); d.textContent = s == null ? "" : s; return d.innerHTML; }

  // ================= PANEL =================
  function iniciarPanel(datos) {
    estado.datos = datos;
    var gen = $("fechaGen"); if (gen) gen.textContent = datos.origen ? ("Fuente: " + datos.origen) : "";
    var sub = $("subtitulo");
    if (sub) sub.textContent = datos.estudiantes.length + " estudiante(s) evaluado(s). Ordenados por prioridad. Tocá una fila para ver la ficha.";

    // filtro grupo
    var grupos = [];
    datos.estudiantes.forEach(function (e) { if (e.grupo && grupos.indexOf(e.grupo) < 0) grupos.push(e.grupo); });
    grupos.sort();
    var selG = $("filtroGrupo");
    selG.innerHTML = '<option value="">Todos los grupos</option>' +
      grupos.map(function (g) { return '<option>' + esc(g) + '</option>'; }).join("");

    $("buscar").oninput = function (e) { estado.texto = e.target.value.toLowerCase(); render(); };
    selG.onchange = function (e) { estado.grupo = e.target.value; render(); };
    $("filtroNivel").onchange = function (e) { estado.nivel = e.target.value; render(); };
var limpiarBtn = $("limpiarFiltros");
    if (limpiarBtn) {
      limpiarBtn.onclick = function () {
        estado.nivel = ""; estado.grupo = ""; estado.texto = "";
        $("buscar").value = ""; selG.value = ""; $("filtroNivel").value = "";
        render();
      };
    }
    // Restaurar filtros desde la URL (para poder compartir un enlace con filtros aplicados).
    var parametrosURL = new URLSearchParams(window.location.search);
    if (parametrosURL.get("nivel")) estado.nivel = parametrosURL.get("nivel");
    if (parametrosURL.get("grupo")) estado.grupo = parametrosURL.get("grupo");
    if (parametrosURL.get("q")) estado.texto = parametrosURL.get("q").toLowerCase();
    $("buscar").value = parametrosURL.get("q") || "";
    selG.value = estado.grupo;
    $("filtroNivel").value = estado.nivel;
    document.querySelectorAll("th[data-col]").forEach(function (th) {
      th.onclick = function () {
        var c = th.dataset.col;
        if (estado.orden === c) estado.asc = !estado.asc; else { estado.orden = c; estado.asc = false; }
        render();
      };
    });

    $("cerrar").onclick = cerrarFicha;
    $("overlay").onclick = function (e) { if (e.target.id === "overlay") cerrarFicha(); };
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") cerrarFicha(); });

    pintarKpis();
    dibujarGraficos();
    render();
  }

  var NIVELES = ["Rojo", "Naranja", "Amarillo", "Verde"];
  var ETIQ = { Rojo: "intervención inmediata", Naranja: "contactar", Amarillo: "seguimiento", Verde: "sin señales" };

  function pintarKpis() {
    var cont = estado.datos.conteo_nivel || {};
    $("kpis").innerHTML = NIVELES.map(function (n) {
      return '<button class="kpi bg-' + n + (estado.nivel === n ? " activo" : "") + '" data-nivel="' + n + '">' +
             '<div class="num">' + (cont[n] || 0) + '</div><div class="lbl">' + n + " · " + ETIQ[n] + '</div></button>';
    }).join("");
    document.querySelectorAll(".kpi").forEach(function (b) {
      b.onclick = function () {
        estado.nivel = (estado.nivel === b.dataset.nivel) ? "" : b.dataset.nivel;
        $("filtroNivel").value = estado.nivel;
        render();
      };
    });
  }

  function filtrar() {
    return estado.datos.estudiantes.filter(function (e) {
      return (!estado.nivel || e.nivel_riesgo === estado.nivel) &&
             (!estado.grupo || e.grupo === estado.grupo) &&
             (!estado.texto || (e.nombre || "").toLowerCase().indexOf(estado.texto) >= 0);
    }).sort(function (a, b) {
      var va = a[estado.orden], vb = b[estado.orden];
      if (typeof va === "string") { va = va || ""; vb = vb || ""; return estado.asc ? va.localeCompare(vb) : vb.localeCompare(va); }
      return estado.asc ? (va - vb) : (vb - va);
    });
  }
function actualizarURL() {
  if (!window.history || !window.history.replaceState) return;
  var params = new URLSearchParams();
  if (estado.nivel) params.set("nivel", estado.nivel);
  if (estado.grupo) params.set("grupo", estado.grupo);
  if (estado.texto) params.set("q", estado.texto);
  var qs = params.toString();
  var url = window.location.pathname + (qs ? "?" + qs : "");
  window.history.replaceState(null, "", url);
}
  
  function render() {
    pintarKpis();
    var filas = filtrar();
    $("conteoVisible").textContent = filas.length + " visible(s)";
    $("cuerpoTabla").innerHTML = filas.map(function (e) {
      var s = (e.senales && e.senales[0]) ? e.senales[0] : "";
      var cl = claseNivel(e.nivel_riesgo);
      return '<tr data-id="' + e.id_estudiante + '">' +
        '<td><span class="pill n-' + cl + '">' + esc(e.nivel_riesgo) + '</span></td>' +
        '<td><strong>' + fmt(e.puntaje_riesgo, 1) + '</strong>' +
          '<div class="barra"><span class="bg-' + cl + '" style="width:' + Math.min(100, e.puntaje_riesgo) + '%"></span></div></td>' +
        '<td>' + esc(e.nombre) + '</td><td>' + esc(e.grupo) + '</td>' +
        '<td>' + fmt(e.valencia_prom_reciente) + '</td><td>' + pct(e.prop_apagamiento) + '</td>' +
        '<td class="muted" style="max-width:280px">' + esc(s) + '</td></tr>';
    }).join("") || '<tr><td colspan="7" class="muted">Sin estudiantes para este filtro.</td></tr>';
    document.querySelectorAll("#cuerpoTabla tr[data-id]").forEach(function (tr) {
      tr.onclick = function () { abrirFicha(+tr.dataset.id); };
    });
  actualizarURL();
  }

  // ================= FICHA =================
  function abrirFicha(id) {
    var e = estado.datos.estudiantes.find(function (x) { return x.id_estudiante === id; });
    if (!e) return;
    $("mNivel").textContent = e.nivel_riesgo;
    $("mNivel").style.background = COLOR[e.nivel_riesgo];
    $("mNombre").textContent = e.nombre;
    $("mMeta").textContent = "Grupo " + e.grupo + (e.edad ? " · " + e.edad + " años" : "") + (e.sexo ? " · " + e.sexo : "") + " · ID " + e.id_estudiante;
    $("mMetricas").innerHTML = [
      ["Puntaje", fmt(e.puntaje_riesgo, 1)], ["Valencia rec.", fmt(e.valencia_prom_reciente)],
      ["Activación rec.", fmt(e.activacion_prom_reciente)], ["Apagamiento", pct(e.prop_apagamiento)],
      ["Reg. negativos", pct(e.prop_negativos)], ["Racha negativa", e.racha_negativa],
    ].map(function (m) { return '<div class="metrica"><div class="v">' + m[1] + '</div><div class="k">' + m[0] + '</div></div>'; }).join("");
    var sinS = e.senales.length === 1 && e.senales[0].toLowerCase().indexOf("sin señales") >= 0;
    $("mSenales").innerHTML = e.senales.map(function (s) { return '<div class="senal ' + (sinS ? "ok" : "") + '">• ' + esc(s) + '</div>'; }).join("");
    dibujarSpark(e.historial || []);
    $("mHistorial").innerHTML = (e.historial || []).slice().reverse().map(function (h) {
      return '<tr><td style="white-space:nowrap">' + esc(h.fecha_hora) + '</td><td>' + fmt(h.valencia) + '</td>' +
        '<td>' + fmt(h.activacion) + '</td><td>' + esc(h.cuadrante) + '</td><td>' + esc(h.etiqueta_emocional) +
        '</td><td class="muted">' + esc(h.comentario) + '</td></tr>';
    }).join("") || '<tr><td colspan="6" class="muted">Sin registros.</td></tr>';
    $("overlay").classList.add("abierto");
  }
  function cerrarFicha() { $("overlay").classList.remove("abierto"); }

  function dibujarSpark(hist) {
    var svg = $("mSpark"), W = 600, H = 80, p = 8;
    svg.innerHTML = "";
    if (!hist.length) return;
    var vals = hist.map(function (h) { return h.valencia; });
    var x = function (i) { return hist.length < 2 ? W / 2 : p + i * (W - 2 * p) / (hist.length - 1); };
    var y = function (v) { return H - p - ((v + 1) / 2) * (H - 2 * p); };
    var d = vals.map(function (v, i) { return (i ? "L" : "M") + x(i).toFixed(1) + "," + y(v).toFixed(1); }).join(" ");
    svg.appendChild(svgEl("line", { x1: 0, y1: y(0), x2: W, y2: y(0), stroke: "#e0524f", "stroke-dasharray": "4 4", opacity: ".5" }));
    svg.appendChild(svgEl("path", { d: d, fill: "none", stroke: "#3f7cb8", "stroke-width": 2 }));
    vals.forEach(function (v, i) {
      svg.appendChild(svgEl("circle", { cx: x(i).toFixed(1), cy: y(v).toFixed(1), r: 2.6, fill: v < 0 ? "#e0524f" : "#3f9d63" }));
    });
  }

  // ================= GRÁFICOS INTERACTIVOS =================
  function dibujarGraficos() {
    var d = estado.datos;
    // 1) Distribución por nivel
    var porNivel = NIVELES.map(function (n) {
      return { label: n, valor: (d.conteo_nivel[n] || 0), color: COLOR[n], nivel: n };
    });
    barras($("gNiveles"), porNivel, "estudiantes", function (it) {
      estado.nivel = it.nivel; $("filtroNivel").value = it.nivel; render();
      detalleEstudiantes("Nivel " + it.nivel, d.estudiantes.filter(function (e) { return e.nivel_riesgo === it.nivel; }));
    });
    // 2) Riesgo promedio por grupo
    var grupos = (d.resumen_grupo || []).map(function (g) {
      return { label: g.grupo, valor: g.puntaje_promedio, color: "#7a6fa6", grupo: g.grupo };
    });
    barras($("gGrupos"), grupos, "puntaje prom.", function (it) {
      estado.grupo = it.grupo; $("filtroGrupo").value = it.grupo; render();
      detalleEstudiantes("Grupo " + it.grupo, d.estudiantes.filter(function (e) { return e.grupo === it.grupo; }));
    });
    // 3) Top 10 por puntaje (barras horizontales)
    var top = d.estudiantes.slice().sort(function (a, b) { return b.puntaje_riesgo - a.puntaje_riesgo; }).slice(0, 10)
      .map(function (e) { return { label: e.nombre, valor: e.puntaje_riesgo, color: COLOR[e.nivel_riesgo], est: e }; });
    barrasH($("gTop"), top, function (it) { abrirFicha(it.est.id_estudiante); });
    // 4) Dispersión valencia/activación por estudiante
    dispersion($("gDispersion"), d.estudiantes);
  }

  function barras(svg, items, unidad, onClick) {
    svg.innerHTML = "";
    var W = 360, H = 230, ml = 34, mb = 46, mt = 14, mr = 10;
    var max = Math.max.apply(null, items.map(function (i) { return i.valor; }).concat([1]));
    var pw = W - ml - mr, ph = H - mt - mb;
    var bw = pw / items.length * 0.62, gap = pw / items.length;
    svg.appendChild(svgEl("line", { class: "gaxis", x1: ml, y1: mt, x2: ml, y2: mt + ph }));
    svg.appendChild(svgEl("line", { class: "gaxis", x1: ml, y1: mt + ph, x2: W - mr, y2: mt + ph }));
    items.forEach(function (it, i) {
      var h = it.valor / max * ph;
      var x = ml + i * gap + (gap - bw) / 2, y = mt + ph - h;
      var rect = svgEl("rect", { class: "gbar", x: x, y: y, width: bw, height: Math.max(0, h), rx: 4, fill: it.color });
      rect.onclick = function () { onClick(it); };
      var tt = svgEl("title"); tt.textContent = it.label + ": " + it.valor + " " + unidad; rect.appendChild(tt);
      svg.appendChild(rect);
      var vtxt = svgEl("text", { class: "gval", x: x + bw / 2, y: y - 4, "text-anchor": "middle" });
      vtxt.textContent = (Math.round(it.valor * 10) / 10); svg.appendChild(vtxt);
      var ltxt = svgEl("text", { class: "glabel", x: x + bw / 2, y: mt + ph + 16, "text-anchor": "middle" });
      ltxt.textContent = it.label; svg.appendChild(ltxt);
    });
  }

  function barrasH(svg, items, onClick) {
    svg.innerHTML = "";
    var W = 360, H = 230, ml = 4, mr = 10, mt = 6, mb = 6;
    var max = Math.max.apply(null, items.map(function (i) { return i.valor; }).concat([1]));
    var ph = H - mt - mb, bh = ph / Math.max(items.length, 1) * 0.7, gap = ph / Math.max(items.length, 1);
    items.forEach(function (it, i) {
      var y = mt + i * gap + (gap - bh) / 2;
      var maxw = W - 150;
      var w = it.valor / max * maxw;
      var rect = svgEl("rect", { class: "gbar", x: 130, y: y, width: Math.max(1, w), height: bh, rx: 3, fill: it.color });
      rect.onclick = function () { onClick(it); };
      var tt = svgEl("title"); tt.textContent = it.label + ": " + it.valor; rect.appendChild(tt);
      svg.appendChild(rect);
      var name = svgEl("text", { class: "glabel", x: 126, y: y + bh / 2 + 4, "text-anchor": "end" });
      name.textContent = it.label.length > 18 ? it.label.slice(0, 17) + "…" : it.label; svg.appendChild(name);
      var v = svgEl("text", { class: "gval", x: 134 + w, y: y + bh / 2 + 4 });
      v.textContent = fmt(it.valor, 1); svg.appendChild(v);
    });
  }

  function dispersion(svg, estudiantes) {
    svg.innerHTML = "";
    var W = 360, H = 230, m = 26;
    var pw = W - 2 * m, ph = H - 2 * m;
    var X = function (v) { return m + (v + 1) / 2 * pw; };
    var Y = function (a) { return m + (1 - (a + 1) / 2) * ph; };
    // ejes en 0
    svg.appendChild(svgEl("line", { class: "gaxis", x1: X(0), y1: m, x2: X(0), y2: m + ph }));
    svg.appendChild(svgEl("line", { class: "gaxis", x1: m, y1: Y(0), x2: m + pw, y2: Y(0) }));
    svg.appendChild(txt(m, H - 4, "valencia →", "glabel"));
    svg.appendChild(txt(2, m + 8, "activ.↑", "glabel"));
    estudiantes.forEach(function (e) {
      var c = svgEl("circle", { class: "gpt", cx: X(e.valencia_prom_reciente).toFixed(1), cy: Y(e.activacion_prom_reciente).toFixed(1),
                                r: 5, fill: COLOR[e.nivel_riesgo], "fill-opacity": .75, stroke: "#fff", "stroke-width": .6 });
      c.onclick = function () { abrirFicha(e.id_estudiante); };
      var tt = svgEl("title"); tt.textContent = e.nombre + " (" + e.grupo + ") · " + e.nivel_riesgo; c.appendChild(tt);
      svg.appendChild(c);
    });
  }
  function txt(x, y, s, cls) { var t = svgEl("text", { x: x, y: y, class: cls }); t.textContent = s; return t; }

  function detalleEstudiantes(titulo, lista) {
    var cont = $("detalle");
    if (!lista.length) { cont.innerHTML = ""; return; }
    var filas = lista.map(function (e) {
      return '<tr data-id="' + e.id_estudiante + '"><td><span class="pill n-' + claseNivel(e.nivel_riesgo) + '">' +
        esc(e.nivel_riesgo) + '</span></td><td><strong>' + fmt(e.puntaje_riesgo, 1) + '</strong></td>' +
        '<td>' + esc(e.nombre) + '</td><td>' + esc(e.grupo) + '</td>' +
        '<td class="muted">' + esc((e.senales && e.senales[0]) || "") + '</td></tr>';
    }).join("");
    cont.innerHTML = '<div class="detalle-box"><h3>📋 Datos que forman esta selección: ' + esc(titulo) +
      ' (' + lista.length + ')</h3><table><thead><tr><th>Nivel</th><th>Puntaje</th><th>Estudiante</th>' +
      '<th>Grupo</th><th>Señal principal</th></tr></thead><tbody>' + filas + '</tbody></table></div>';
    cont.querySelectorAll("tr[data-id]").forEach(function (tr) { tr.onclick = function () { abrirFicha(+tr.dataset.id); }; });
    cont.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  window.FARO_UI = { iniciarPanel: iniciarPanel };
})();
