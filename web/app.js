// Karte (AP-06 bis AP-10)
(async function () {
  seiteAufbauen("index.html");
  const $ = id => document.getElementById(id);
  const farben = {};
  const state = { layer: true, modus: "report", geraete: new Set(GERAETE.map(g => g[0])), vollstaendig: false, entwuerfe: false };

  const [meta, details, reportData] = await Promise.all([
    ladeJson("data/meta.json"), ladeJson("data/details.json"), ladeJson("data/touren_report.geojson")]);
  for (const [k, v] of Object.entries(meta.kategorien)) farben[k] = v.farbe;

  // --- Zustand aus dem Link (AP-07, optional)
  const p = new URLSearchParams(location.hash.slice(1));
  if (p.get("layer") === "0") state.layer = false;
  if (p.get("modus") === "alle") state.modus = "alle";
  if (p.get("geraet")) state.geraete = new Set(p.get("geraet").split(","));
  if (p.get("voll") === "1") state.vollstaendig = true;
  if (p.get("entwurf") === "1") state.entwuerfe = true;

  // --- Karte
  const map = L.map("map", { zoomControl: true }).setView([47.3, 12.5], 7);
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap-Mitwirkende</a>',
  }).addTo(map);
  const gruppe = L.layerGroup();
  const eintraege = [];

  function stil(pr) {
    const nk = pr.k === "nicht_klassifiziert";
    return { color: farben[pr.k], weight: nk ? 3 : (pr.e ? 3 : 5), opacity: (nk || !pr.e) ? 1 : 0.8, dashArray: STRICH[pr.h], lineJoin: "round" };
  }
  function aufnehmen(gj) {
    L.geoJSON(gj, {
      style: f => stil(f.properties),
      onEachFeature(f, layer) {
        layer.bindPopup(() => detailHtml(details[f.properties.id]), { maxWidth: 340 });
        eintraege.push({ layer, pr: f.properties });
      },
    });
  }
  aufnehmen(reportData);
  let weitereGeladen = false, weitereLaedt = false, entwuerfeGeladen = false, entwuerfeLaedt = false;
  async function entwuerfeLaden() {
    if (entwuerfeGeladen || entwuerfeLaedt) return;
    entwuerfeLaedt = true;
    aufnehmen(await ladeJson("data/touren_entwuerfe.geojson"));
    entwuerfeGeladen = true;
    anwenden();
  }
  async function weitereLaden() {
    if (weitereGeladen || weitereLaedt) return;
    weitereLaedt = true;
    aufnehmen(await ladeJson("data/touren_weitere.geojson"));
    weitereGeladen = true;
    anwenden();
  }

  function sichtbar(pr) {
    if (pr.e && !state.entwuerfe) return false;
    if (pr.k === "nicht_klassifiziert") return state.modus === "alle" && !state.vollstaendig;
    if (!state.geraete.has(geraetGruppe(pr.k))) return false;
    if (state.vollstaendig && details[pr.id].stufe !== "vollständig") return false;
    return true;
  }

  function anwenden() {
    gruppe.clearLayers();
    let n = 0;
    if (state.layer) {
      for (const e of eintraege) if (sichtbar(e.pr)) { gruppe.addLayer(e.layer); n++; }
      if (!map.hasLayer(gruppe)) gruppe.addTo(map);
    } else map.removeLayer(gruppe);
    $("zaehlung").textContent = state.layer
      ? n + (n === 1 ? " Tour wird angezeigt." : " Touren werden angezeigt.") : "Layer ist ausgeblendet.";
    if (state.modus === "alle" && !weitereGeladen) weitereLaden();
    if (state.entwuerfe && !entwuerfeGeladen) entwuerfeLaden();
    const q = new URLSearchParams();
    if (!state.layer) q.set("layer", "0");
    if (state.modus === "alle") q.set("modus", "alle");
    if (state.geraete.size !== GERAETE.length) q.set("geraet", [...state.geraete].join(","));
    if (state.vollstaendig) q.set("voll", "1");
    if (state.entwuerfe) q.set("entwurf", "1");
    history.replaceState(null, "", q.toString() ? "#" + q : location.pathname);
    $("zur-liste").href = "liste.html" + (q.toString() ? "#" + q : "");
  }

  // --- Bedienelemente
  $("layer-an").checked = state.layer;
  document.querySelector(`input[name=modus][value=${state.modus}]`).checked = true;
  $("layer-an").addEventListener("change", e => { state.layer = e.target.checked; anwenden(); });
  $("entwuerfe").checked = state.entwuerfe;
  $("entwuerfe").addEventListener("change", e => { state.entwuerfe = e.target.checked; anwenden(); });
  document.querySelectorAll("input[name=modus]").forEach(r =>
    r.addEventListener("change", e => { state.modus = e.target.value; anwenden(); }));
  for (const [k, t] of GERAETE) {
    const l = document.createElement("label");
    l.innerHTML = `<input type="checkbox" value="${k}"> ${esc(t)}`;
    const cb = l.firstChild;
    cb.checked = state.geraete.has(k);
    cb.addEventListener("change", () => { cb.checked ? state.geraete.add(k) : state.geraete.delete(k); anwenden(); });
    $("geraete").appendChild(l);
  }
  const cbVoll = $("nur-vollstaendig");
  cbVoll.checked = state.vollstaendig;
  if (!meta.bewertung_erfasst) {
    cbVoll.disabled = true;
    state.vollstaendig = false;
    cbVoll.checked = false;
    $("stufe-notiz").textContent = "Noch nicht verfügbar: Die Bewertungsdaten (Schlüsselstellen, WC, Hilfsperson) liegen noch nicht vor.";
  }
  cbVoll.addEventListener("change", () => { state.vollstaendig = cbVoll.checked; anwenden(); });

  // --- Legende (AP-08)
  const zeilen = [
    ["rollstuhl_r1", "nein", "R1 – ohne Antrieb"], ["rollstuhl_r2", "nein", "R2 – leichte Antriebshilfe (aktuell keine Tour)"],
    ["rollstuhl_r3", "nein", "R3 – starke Antriebshilfe"], ["handbike", "nein", "Handbike"],
    ["rollstuhl_unklar", "nein", "Gerät unklar / Sonstiges"], ["nicht_klassifiziert", "ohne", "Nicht klassifiziert (nur „Alle Touren“)"],
  ];
  const linie = (k, h) => `<svg width="48" height="10" aria-hidden="true"><line x1="0" y1="5" x2="48" y2="5" stroke="${farben[k]}" stroke-width="${k === "nicht_klassifiziert" ? 3 : 5}"${STRICH[h] ? ` stroke-dasharray="${STRICH[h]}"` : ""}/></svg>`;
  $("legende").innerHTML = zeilen.map(([k, h, t]) => `<li>${linie(k, h)}<span>${esc(t)}</span></li>`).join("") +
    `<li><svg width="48" height="10" aria-hidden="true"><line x1="0" y1="5" x2="48" y2="5" stroke="#444" stroke-width="3" opacity="0.8"/></svg><span>dünner: Entwurf (nicht veröffentlicht)</span></li>
     <li><svg width="48" height="10" aria-hidden="true"><line x1="0" y1="5" x2="48" y2="5" stroke="#444" stroke-width="5"/></svg><span>durchgezogen: keine Hilfsperson nötig</span></li>
     <li><svg width="48" height="10" aria-hidden="true"><line x1="0" y1="5" x2="48" y2="5" stroke="#444" stroke-width="5" stroke-dasharray="${STRICH.ja}"/></svg><span>gestrichelt: Hilfsperson erforderlich und/oder nur für Geübte</span></li>
     <li><svg width="48" height="10" aria-hidden="true"><line x1="0" y1="5" x2="48" y2="5" stroke="#444" stroke-width="5" stroke-dasharray="${STRICH.offen}"/></svg><span>strichpunktiert: Angabe noch nicht erfasst</span></li>`;

  anwenden();
})().catch(e => {
  document.getElementById("map").textContent = "Die Daten konnten nicht geladen werden: " + e.message;
});