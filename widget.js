/* Pronósticos Basket Elo — widget para Blogger.
   Uso: <div class="pbe-app" data-view="all" data-lg="ACB"></div>
        <script src="https://manuosunaca-coder.github.io/pronosticos-basket-elo/widget.js"></script>
   data-view: all | picks | cards | results | ranking | help | games | mini
   data-lg:   ACB | EL  (vacío = las dos)   data-max: nº de tarjetas en "cards" */
(function () {
  var SCRIPT = document.currentScript;
  var BASE = SCRIPT && SCRIPT.src ? SCRIPT.src.replace(/[^\/]*$/, "") : "";
  var CSS = "\
.pbe{--o:#c2410c;--o2:#ea580c;--ol:#ffedd5;--n:#1e1b4b;--ink:#0f172a;--mut:#64748b;--line:#e2e8f0;--soft:#f8fafc;--g:#15803d;--red:#b91c1c;\
font:14px/1.45 system-ui,-apple-system,'Segoe UI',Roboto,Arial,sans-serif;color:var(--ink);max-width:100%;overflow:hidden;text-align:left}\
.pbe *{box-sizing:border-box}.pbe a{color:inherit}\
.pbe-stats{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin:0 0 12px}\
.pbe-stat{background:var(--soft);border:1px solid var(--line);border-radius:10px;padding:10px 12px}\
.pbe-stat b{display:block;font-size:22px;line-height:1.1;font-variant-numeric:tabular-nums;color:var(--n)}.pbe-stat span{font-size:12px;color:var(--mut)}\
.pbe-tabs{display:flex;gap:4px;border-bottom:2px solid var(--o);margin-bottom:10px;overflow-x:auto}\
.pbe-tab{border:0;background:var(--soft);color:var(--ink);padding:8px 14px;border-radius:8px 8px 0 0;cursor:pointer;font:600 14px inherit;font-family:inherit;white-space:nowrap}\
.pbe-tab.on{background:var(--o);color:#fff}\
.pbe-filters{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-bottom:10px}\
.pbe-filters input[type=search],.pbe-filters select{padding:7px 9px;border:1px solid var(--line);border-radius:8px;font:inherit;background:#fff;color:var(--ink);min-width:0}\
.pbe-filters input[type=search]{flex:1 1 160px}.pbe-filters label{display:flex;gap:6px;align-items:center;font-size:13px;cursor:pointer;white-space:nowrap}\
.pbe-wrap{overflow-x:auto;-webkit-overflow-scrolling:touch}\
.pbe table{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums;margin:0}\
.pbe th{background:var(--n);color:#fff;font-weight:600;font-size:12px;padding:7px 6px;text-align:left;white-space:nowrap;border:0}\
.pbe td{padding:7px 6px;border:0;border-bottom:1px solid var(--line);vertical-align:middle}\
.pbe tr.pbe-sure td{background:#fff7ed}.pbe tr:hover td{background:#f1f5f9}\
.pbe-day td{background:var(--soft)!important;font-weight:700;font-size:12px;color:var(--mut)}\
.pbe-lg{display:inline-flex;align-items:center;gap:5px;white-space:nowrap;font-size:12px;color:var(--mut)}\
.pbe-tag{display:inline-block;font-size:10px;font-weight:800;letter-spacing:.04em;padding:2px 6px;border-radius:5px;background:var(--ol);color:var(--o)}\
.pbe-tag.el{background:#e0e7ff;color:#3730a3}\
.pbe-m{min-width:190px}.pbe-m b{font-weight:800;color:var(--o)}.pbe-up{color:var(--g);font-weight:700}.pbe-dn{color:var(--red);font-weight:700}\
.pbe-bar{display:flex;height:8px;border-radius:4px;overflow:hidden;min-width:90px;background:#e2e8f0}.pbe-bar i{display:block;background:var(--o2)}.pbe-bar i+i{background:#94a3b8}\
.pbe-pp{font-size:11px;color:var(--mut);display:flex;justify-content:space-between;gap:6px;margin-top:2px}\
.pbe-c{display:inline-block;min-width:30px;text-align:center;padding:3px 6px;border-radius:999px;font-weight:700;font-size:12px;background:#e2e8f0}\
.pbe-c.c7{background:#fed7aa;color:#7c2d12}.pbe-c.c8{background:#fdba74;color:#7c2d12}.pbe-c.c9{background:#fb923c;color:#fff}.pbe-c.c10{background:var(--o);color:#fff}\
.pbe-ok{color:var(--g);font-weight:700}.pbe-ko{color:var(--red);font-weight:700}\
.pbe-note{font-size:12px;color:var(--mut);margin:10px 0 0}\
.pbe-rg{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px}\
.pbe-rg table td,.pbe-rg table th{padding:6px 8px}\
.pbe-help{background:var(--soft);border:1px solid var(--line);border-radius:10px;padding:12px 16px}.pbe-help p{margin:0 0 8px}\
.pbe-18{display:flex;gap:10px;align-items:center;margin-top:12px;padding:10px 12px;border-radius:10px;background:#fff7ed;border:1px solid #fed7aa;font-size:12px;color:#7c2d12}\
.pbe-18 strong{display:inline-grid;place-items:center;min-width:34px;height:34px;border-radius:50%;border:2px solid #c2410c;font-size:13px;color:#c2410c}\
.pbe-empty{padding:24px;text-align:center;color:var(--mut)}\
.pbe-cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:14px;padding:3px 1px}\
.pbe-card{background:#fff;border:1px solid var(--line);border-radius:14px;padding:14px 16px;display:flex;flex-direction:column;gap:10px;transition:transform .15s,box-shadow .15s}\
.pbe-card:hover{transform:translateY(-2px);box-shadow:0 10px 24px rgba(194,65,12,.14)}\
.pbe-card.hot{border-color:#fdba74;background:linear-gradient(180deg,#fff7ed,#fff 55%)}\
.pbe-card header{display:flex;justify-content:space-between;align-items:center;gap:8px;font-size:12px;color:var(--mut)}\
.pbe-card time{white-space:nowrap;font-variant-numeric:tabular-nums;font-weight:600}\
.pbe-teams{display:grid;gap:1px;font-size:15px;line-height:1.3}\
.pbe-teams .vs{font-size:10px;color:var(--mut);text-transform:uppercase;letter-spacing:.1em}\
.pbe-teams .on{font-weight:800;color:var(--o)}.pbe-teams small{color:var(--mut);font-size:11px;font-weight:400}\
.pbe-pick{display:flex;justify-content:space-between;align-items:center;background:var(--n);color:#fff;border-radius:10px;padding:8px 12px;font-weight:600;font-size:14px}\
.pbe-pick b{font-size:20px;font-variant-numeric:tabular-nums;color:#fdba74}\
.pbe-meter{display:flex;align-items:center;gap:3px}\
.pbe-meter i{flex:1;height:6px;border-radius:3px;background:#e2e8f0}.pbe-meter i.on{background:#fb923c}.pbe-card.hot .pbe-meter i.on{background:var(--o)}\
.pbe-meter em{font-style:normal;font-size:12px;font-weight:800;margin-left:6px;color:var(--ink)}\
.pbe-card footer{display:flex;justify-content:space-between;font-size:12px;color:var(--mut)}\
.pbe-mini ol{margin:0;padding:0;list-style:none;border:1px solid var(--line);border-radius:10px;overflow:hidden}.pbe-mini li{padding:7px 10px;border-bottom:1px solid var(--line)}.pbe-mini small{color:var(--mut)}\
@media(max-width:640px){.pbe-stats{grid-template-columns:repeat(2,1fr)}.pbe-hm{display:none}.pbe td,.pbe th{padding:6px 4px}.pbe{font-size:13px}.pbe-m{min-width:140px}}\
";
  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); }
  function tag(lg) { return '<span class="pbe-tag' + (lg === "EL" ? " el" : "") + '">' + (lg === "EL" ? "EUROLIGA" : "ACB") + '</span>'; }
  function tr(v) { return v > 0 ? ' <span class="pbe-up" title="En racha">↑</span>' : v < 0 ? ' <span class="pbe-dn" title="Mala racha">↓</span>' : ""; }
  function rec(r) { return r && (r[0] + r[1]) ? " <small>(" + r[0] + "-" + r[1] + ")</small>" : ""; }
  function iso(x) { return x.getFullYear() + "-" + ("0" + (x.getMonth() + 1)).slice(-2) + "-" + ("0" + x.getDate()).slice(-2); }
  function fmtDay(d) { var s = new Date(d + "T12:00:00").toLocaleDateString("es-ES", { weekday: "long", day: "numeric", month: "long" }); return s.charAt(0).toUpperCase() + s.slice(1); }
  function dayShort(d) { var t = new Date(); if (d === iso(t)) return "Hoy"; t.setDate(t.getDate() + 1); if (d === iso(t)) return "Mañana"; return fmtDay(d).split(",")[0]; }
  function pickName(u) { return u.pick === "1" ? u.home : u.away; }

  function init(root) {
    if (root.__pbe) return; root.__pbe = 1;
    var src = root.getAttribute("data-src") || BASE + "data.json";
    root.className += " pbe";
    root.innerHTML = '<div class="pbe-empty">Cargando pronósticos…</div>';
    fetch(src + (src.indexOf("?") < 0 ? "?" : "&") + "t=" + Math.floor(Date.now() / 600000))
      .then(function (r) { return r.json(); })
      .then(function (d) { render(root, d, root.getAttribute("data-view") || "all"); })
      .catch(function () { root.innerHTML = '<div class="pbe-empty">No se han podido cargar los pronósticos. Inténtalo en unos minutos.</div>'; });
  }

  function st(ps) { if (!ps.length) return { n: 0, hits: 0, hit_rate: 0 }; var h = 0; ps.forEach(function (p) { if (p.win) h++; }); return { n: ps.length, hits: h, hit_rate: Math.round(1000 * h / ps.length) / 10 }; }

  function render(root, d, view) {
    var STRONG = (d.model && d.model.strong) || 7, now = Date.now();
    d.upcoming = d.upcoming.filter(function (u) { var k = Date.parse(u.date + "T" + u.time + ":00+01:00"); return isNaN(k) || k > now - 3 * 3600 * 1000; });
    var lg = root.getAttribute("data-lg") || "";
    var model = d.stats.season_model;
    if (lg) {
      var f = function (x) { return x.lg === lg; };
      d.upcoming = d.upcoming.filter(f); d.recent = d.recent.filter(f); d.leagues = d.leagues.filter(f); d.last_games = (d.last_games || []).filter(f);
      var mo = new Date().toISOString().slice(0, 7), strong = d.recent.filter(function (p) { return p.conf >= STRONG; });
      d.stats = { all: st(d.recent), strong: st(strong), month: st(d.recent.filter(function (p) { return p.date.slice(0, 7) === mo; })), season_model: (d.stats.season_by_lg || {})[lg] || model };
      model = d.stats.season_model;
    }
    var upd = new Date(d.generated).toLocaleString("es-ES", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
    var foot = '<div class="pbe-18"><strong>+18</strong><span>Pronósticos generados por un modelo estadístico, con fines informativos. Ningún resultado es seguro: si apuestas, hazlo con responsabilidad. Ayuda: <a href="https://www.jugarbien.es" target="_blank" rel="nofollow noopener">jugarbien.es</a> · Actualizado ' + esc(upd) + '.</span></div>';

    if (view === "cards" || view === "mini") {
      var max = +(root.getAttribute("data-max") || (view === "mini" ? 6 : 6));
      var pool = d.upcoming.slice().sort(function (a, b) { return b.conf - a.conf || (a.date + a.time).localeCompare(b.date + b.time); }).slice(0, max);
      if (!pool.length) { root.innerHTML = '<div class="pbe-empty">No hay partidos en los próximos días. El modelo vuelve a calcular dos veces al día.</div>'; return; }
      if (view === "mini") {
        root.innerHTML = '<div class="pbe-mini"><ol>' + pool.map(function (u) {
          return '<li><span class="pbe-c c' + u.conf + '">' + u.conf + '</span> <b>' + esc(pickName(u)) + '</b> ' + u.pick_prob + '%<br><small>' + esc(u.home) + ' – ' + esc(u.away) + ' · ' + dayShort(u.date) + ' ' + esc(u.time) + '</small></li>';
        }).join("") + '</ol></div>';
        return;
      }
      root.innerHTML = '<div class="pbe-cards">' + pool.map(function (u) {
        var seg = ""; for (var i = 1; i <= 10; i++) seg += '<i class="' + (i <= u.conf ? "on" : "") + '"></i>';
        return '<article class="pbe-card' + (u.conf >= STRONG ? " hot" : "") + '">' +
          '<header><span class="pbe-lg">' + tag(u.lg) + ' ' + esc(u.round) + '</span><time>' + dayShort(u.date) + ' · ' + esc(u.time) + '</time></header>' +
          '<div class="pbe-teams"><span' + (u.pick === "1" ? ' class="on"' : "") + '>' + esc(u.home) + tr(u.tr_h) + rec(u.rec_h) + '</span><span class="vs">vs</span><span' + (u.pick === "2" ? ' class="on"' : "") + '>' + esc(u.away) + tr(u.tr_a) + rec(u.rec_a) + '</span></div>' +
          '<div class="pbe-pick"><span>Gana ' + esc(pickName(u)) + '</span><b>' + u.pick_prob + '%</b></div>' +
          '<div class="pbe-meter" title="Confianza ' + u.conf + ' de 10">' + seg + '<em>' + u.conf + '/10</em></div>' +
          '<footer><span>Ventaja esperada <b>+' + u.margin + ' pts</b></span>' + (u.tv ? '<span title="Televisión">📺 ' + esc(u.tv.split(",")[0]) + '</span>' : '') + '</footer></article>';
      }).join("") + '</div>';
      return;
    }

    function tiles() {
      var a = d.stats.all, s = d.stats.strong;
      function t(v, l) { return '<div class="pbe-stat"><b>' + v + '</b><span>' + l + '</span></div>'; }
      return '<div class="pbe-stats">' +
        t(model && model.n ? model.hit_rate + "%" : "—", "Acierto del modelo esta temporada · " + (model ? model.n : 0) + " partidos") +
        t(a.n ? a.hit_rate + "%" : "—", a.n ? "Aciertos publicados · últimos " + a.n : "Aciertos publicados (al jugarse los primeros)") +
        t(s.n ? s.hit_rate + "%" : "—", "Aciertos pronósticos fuertes (" + STRONG + "-10)") +
        t(d.upcoming.length, "Partidos en los próximos días") + '</div>';
    }
    var tabs = [["picks", "Pronósticos"], ["results", "Aciertos"], ["games", "Resultados"], ["ranking", "Ranking Elo"], ["help", "Cómo funciona"]];
    if (view !== "all") tabs = tabs.filter(function (t) { return t[0] === view; });
    root.innerHTML = (view === "all" || view === "picks" || view === "results" ? tiles() : "") +
      (tabs.length > 1 ? '<div class="pbe-tabs">' + tabs.map(function (t, i) { return '<button class="pbe-tab' + (i ? "" : " on") + '" data-t="' + t[0] + '">' + t[1] + '</button>'; }).join("") + '</div>' : "") +
      '<div class="pbe-body"></div>' + foot;
    var body = root.querySelector(".pbe-body");
    var state = { q: "", lg: "", day: "", sure: false };

    function picks() {
      var days = {}; d.upcoming.forEach(function (u) { days[u.date] = 1; });
      body.innerHTML = '<div class="pbe-filters"><input type="search" placeholder="Buscar equipo…">' +
        (lg ? "" : '<select data-f="lg"><option value="">ACB y Euroliga</option><option value="ACB">Liga Endesa (ACB)</option><option value="EL">Euroliga</option></select>') +
        '<select data-f="day"><option value="">Todos los días</option>' + Object.keys(days).sort().map(function (k) { return '<option value="' + k + '">' + fmtDay(k) + '</option>'; }).join("") + '</select>' +
        '<label><input type="checkbox"> Solo pronósticos fuertes (' + STRONG + '-10)</label></div><div class="pbe-wrap pbe-t"></div>' +
        '<p class="pbe-note">En naranja, el equipo que el modelo ve ganador. La barra muestra la probabilidad de victoria de cada equipo. <b>Ventaja</b> = por cuántos puntos debería ganar el favorito. ↑↓ = racha. Entre paréntesis, victorias y derrotas de la temporada.</p>';
      var q = body.querySelector("input[type=search]"), l = body.querySelector("[data-f=lg]"), dy = body.querySelector("[data-f=day]"), cb = body.querySelector("input[type=checkbox]");
      q.oninput = function () { state.q = q.value; table(); };
      if (l) l.onchange = function () { state.lg = l.value; table(); };
      dy.onchange = function () { state.day = dy.value; table(); };
      cb.onchange = function () { state.sure = cb.checked; table(); };
      table();
    }
    function table() {
      var q = state.q.toLowerCase();
      var rows = d.upcoming.filter(function (u) {
        return (!state.lg || u.lg === state.lg) && (!state.day || u.date === state.day) && (!state.sure || u.conf >= STRONG) && (!q || (u.home + " " + u.away).toLowerCase().indexOf(q) >= 0);
      });
      var t = body.querySelector(".pbe-t");
      if (!rows.length) { t.innerHTML = '<div class="pbe-empty">No hay partidos con esos filtros.</div>'; return; }
      var h = '<table><thead><tr><th>Hora</th><th class="pbe-hm">Comp.</th><th>Partido</th><th>Probabilidad</th><th class="pbe-hm">Ventaja</th><th>Conf.</th></tr></thead><tbody>', last = "";
      rows.forEach(function (u) {
        if (u.date !== last) { last = u.date; h += '<tr class="pbe-day"><td colspan="6">' + fmtDay(u.date) + '</td></tr>'; }
        var hn = esc(u.home), an = esc(u.away);
        if (u.pick === "1") hn = "<b>" + hn + "</b>"; else an = "<b>" + an + "</b>";
        h += '<tr class="' + (u.conf >= STRONG ? "pbe-sure" : "") + '" title="Elo ' + esc(u.home) + ': ' + u.elo_h + ' · Elo ' + esc(u.away) + ': ' + u.elo_a + '">' +
          '<td>' + esc(u.time) + '</td><td class="pbe-hm">' + tag(u.lg) + '</td>' +
          '<td class="pbe-m">' + hn + tr(u.tr_h) + rec(u.rec_h) + ' – ' + an + tr(u.tr_a) + rec(u.rec_a) + (u.tv ? '<br><small style="color:#64748b">📺 ' + esc(u.tv) + '</small>' : '') + '</td>' +
          '<td><div class="pbe-bar"><i style="width:' + u.p_home + '%"></i><i style="width:' + u.p_away + '%"></i></div><div class="pbe-pp"><span>' + u.p_home + '%</span><span>' + u.p_away + '%</span></div></td>' +
          '<td class="pbe-hm">+' + u.margin + '</td><td><span class="pbe-c c' + u.conf + '">' + u.conf + '</span></td></tr>';
      });
      t.innerHTML = h + "</tbody></table>";
    }
    function results() {
      if (!d.recent.length) { body.innerHTML = '<div class="pbe-empty">Aún no hay pronósticos terminados. En cuanto se jueguen los primeros partidos aparecerán aquí con su resultado, aciertos y fallos incluidos.</div>'; return; }
      var s = d.stats;
      var h = '<p class="pbe-note" style="margin:0 0 8px">Este mes: ' + s.month.n + ' pronósticos, ' + s.month.hit_rate + '% de aciertos.</p><div class="pbe-wrap"><table><thead><tr><th>Fecha</th><th class="pbe-hm">Comp.</th><th>Partido</th><th>Pronóstico</th><th>Resultado</th><th></th></tr></thead><tbody>';
      d.recent.forEach(function (p) {
        h += '<tr class="' + (p.conf >= STRONG ? "pbe-sure" : "") + '"><td>' + p.date.slice(8, 10) + "/" + p.date.slice(5, 7) + '</td><td class="pbe-hm">' + tag(p.lg) + '</td>' +
          '<td class="pbe-m">' + esc(p.home) + ' – ' + esc(p.away) + '</td><td>' + esc(p.pick === "1" ? p.home : p.away) + ' ' + p.pick_prob + '% <span class="pbe-c c' + p.conf + '">' + p.conf + '</span></td>' +
          '<td>' + esc(p.score) + '</td><td class="' + (p.win ? "pbe-ok" : "pbe-ko") + '">' + (p.win ? "✔" : "✘") + '</td></tr>';
      });
      body.innerHTML = h + "</tbody></table></div>";
    }
    function games() {
      var g = d.last_games || [];
      if (!g.length) { body.innerHTML = '<div class="pbe-empty">No hay resultados recientes.</div>'; return; }
      var h = '<div class="pbe-wrap"><table><thead><tr><th>Fecha</th><th class="pbe-hm">Comp.</th><th>Local</th><th></th><th>Visitante</th></tr></thead><tbody>';
      g.forEach(function (x) {
        var hw = x.hs > x.as;
        h += '<tr><td>' + x.date.slice(8, 10) + "/" + x.date.slice(5, 7) + '</td><td class="pbe-hm">' + tag(x.lg) + ' ' + esc(x.round) + '</td><td' + (hw ? ' style="font-weight:800"' : "") + '>' + esc(x.home) + '</td><td style="white-space:nowrap;font-weight:700">' + x.hs + ' - ' + x.as + '</td><td' + (!hw ? ' style="font-weight:800"' : "") + '>' + esc(x.away) + '</td></tr>';
      });
      body.innerHTML = h + "</tbody></table></div>";
    }
    function ranking() {
      body.innerHTML = '<div class="pbe-rg">' + d.leagues.map(function (l) {
        return '<div><h4 style="margin:0 0 6px">' + tag(l.lg) + ' ' + esc(l.league) + ' ' + esc(d.season) + '</h4><div class="pbe-wrap"><table><thead><tr><th>#</th><th>Equipo</th><th>V-D</th><th>Elo</th></tr></thead><tbody>' +
          l.teams.map(function (t, i) { return '<tr><td>' + (i + 1) + '</td><td>' + esc(t.team) + tr(t.tr) + '</td><td>' + t.w + '-' + t.l + '</td><td><b>' + t.elo + '</b></td></tr>'; }).join("") + '</tbody></table></div></div>';
      }).join("") + '</div>';
    }
    function help() {
      body.innerHTML = '<div class="pbe-help">' +
        '<p><b>1. Rating Elo.</b> Cada equipo tiene una puntuación que sube al ganar y baja al perder. Gana más puntos si vence a un rival fuerte o por mucha diferencia. Usamos ' + d.model.games.toLocaleString("es-ES") + ' partidos de las últimas ' + d.model.seasons + ' temporadas de la ACB y la Euroliga; al empezar cada temporada los ratings se acercan un poco a la media.</p>' +
        '<p><b>2. Ventaja de campo.</b> Jugar en casa vale unos ' + d.model.home_adv.ACB + ' puntos Elo en la ACB y ' + d.model.home_adv.EL + ' en la Euroliga (en torno a 3 puntos en el marcador).</p>' +
        '<p><b>3. Probabilidad y ventaja esperada.</b> Con la diferencia de Elo calculamos la probabilidad de victoria de cada equipo y por cuántos puntos debería ganar el favorito (28 puntos Elo ≈ 1 punto).</p>' +
        '<p><b>4. Confianza 1-10.</b> Depende de lo probable que sea el pronóstico: 5/10 ronda el 70 % y 10/10 supera el 90 %. Los <b>pronósticos fuertes</b> son los de ' + STRONG + ' o más.</p>' +
        '<p><b>5. Transparencia.</b> Todos los pronósticos se guardan y se comprueban solos al terminar el partido. El "acierto del modelo" mide cuántas veces ganó el favorito del Elo en los partidos de esta temporada.</p>' +
        '<p style="margin:0">Se actualiza automáticamente dos veces al día. Datos: acb.com (Liga Endesa), api-live.euroleague.net (Euroliga) y TheSportsDB (temporadas anteriores de la ACB).</p></div>';
    }
    var views = { picks: picks, results: results, games: games, ranking: ranking, help: help };
    root.querySelectorAll(".pbe-tab").forEach(function (b) {
      b.onclick = function () { root.querySelectorAll(".pbe-tab").forEach(function (x) { x.classList.remove("on"); }); b.classList.add("on"); views[b.getAttribute("data-t")](); };
    });
    views[tabs[0][0]]();
  }

  function boot() {
    if (!document.getElementById("pbe-css")) { var s = document.createElement("style"); s.id = "pbe-css"; s.textContent = CSS; document.head.appendChild(s); }
    document.querySelectorAll("#pbe-app,.pbe-app").forEach(init);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot); else boot();
})();
