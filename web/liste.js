// Listenansicht (AP-12)
(async function () {
  seiteAufbauen("liste.html");
  const $ = id => document.getElementById(id);
  const state = { modus: "report", geraete: new Set(GERAETE.map(g => g[0])), vollstaendig: false, entwuerfe: false, sort: "titel", richtung: 1 };

  const [meta, details, report] = await Promise.all([
    ladeJson("data/meta.json"), ladeJson("data/details.json"), ladeJson("data/touren_report.geojson")]);
  const eintrag = f => ({ id: f.properties.id, k: f.properties.k, e: !!f.properties.e });
  let touren = report.features.map(eintrag);
  let weitereGeladen = false, entwuerfeGeladen = false;

  const p = new URLSearchParams(location.hash.slice(1));
  if (p.get("modus") === "alle") state.modus = "alle";
  if (p.get("geraet")) state.geraete = new Set(p.get("geraet").split(","));
  if (p.get("entwurf") === "1") state.entwuerfe = true;
  if (p.get("voll") === "1" && meta.bewertung_erfasst) state.vollstaendig = true;

  const spalten = [
    ["titel", "Titel"], ["kategorie", "Gerät"], ["stufe", "Stufe"], ["status", "Status"], ["hilfsperson", "Hilfsperson / Geübte"],
    ["region", "Region"], ["strecke_km", "Länge (km)"],
  ];
  const HP = { ja: "erforderlich und/oder nur für Geübte", nein: "nicht nötig", offen: "noch nicht erfasst", ohne: "–" };
  const wert = (t, s) => s === "status" ? (details[t.id].entwurf ? "Entwurf" : "veröffentlicht") : s === "hilfsperson" ? HP[details[t.id].hilfsperson] : details[t.id][s];

  function sichtbar(t) {
    if (t.e && !state.entwuerfe) return false;
    if (t.k === "nicht_klassifiziert") return state.modus === "alle" && !state.vollstaendig;
    if (!state.geraete.has(geraetGruppe(t.k))) return false;
    return !(state.vollstaendig && details[t.id].stufe !== "vollständig");
  }

  function zeichnen() {
    const l = touren.filter(sichtbar).sort((a, b) => {
      const x = wert(a, state.sort), y = wert(b, state.sort);
      if (x == null) return 1; if (y == null) return -1;
      return (typeof x === "number" ? x - y : String(x).localeCompare(String(y), "de")) * state.richtung;
    });
    $("kopf").innerHTML = spalten.map(([s, t]) => {
      const aktiv = state.sort === s;
      return `<th scope="col" aria-sort="${aktiv ? (state.richtung === 1 ? "ascending" : "descending") : "none"}"><button type="button" data-s="${s}">${t}${aktiv ? (state.richtung === 1 ? " ▲" : " ▼") : ""}</button></th>`;
    }).join("");
    $("zeilen").innerHTML = l.map(t => {
      const d = details[t.id];
      return `<tr><th scope="row" style="font-weight:400">${d.url ? `<a href="${esc(d.url)}" target="_blank" rel="noopener">${esc(d.titel)}<span class="sr-only"> (öffnet in neuem Tab)</span></a>` : esc(d.titel)}</th>
        <td>${esc(d.kategorie)}${d.geraet ? "<br><small>" + esc(d.geraet) + "</small>" : ""}</td><td>${esc(d.stufe)}</td><td>${d.entwurf ? "<strong>Entwurf</strong> (nicht veröffentlicht, Daten vorläufig)" : "veröffentlicht"}</td>
        <td>${esc(HP[d.hilfsperson])}</td><td>${esc(d.region || "")}</td><td>${d.strecke_km ?? ""}</td></tr>`;
    }).join("");
    document.querySelectorAll("#kopf button").forEach(b => b.addEventListener("click", () => {
      state.richtung = state.sort === b.dataset.s ? -state.richtung : 1; state.sort = b.dataset.s; zeichnen();
      document.querySelector(`#kopf button[data-s="${state.sort}"]`).focus();
    }));
    $("zaehlung").textContent = l.length + (l.length === 1 ? " Tour" : " Touren") + " in der Liste.";
    const q = new URLSearchParams();
    if (state.modus === "alle") q.set("modus", "alle");
    if (state.geraete.size !== GERAETE.length) q.set("geraet", [...state.geraete].join(","));
    if (state.vollstaendig) q.set("voll", "1");
    if (state.entwuerfe) q.set("entwurf", "1");
    history.replaceState(null, "", q.toString() ? "#" + q : location.pathname);
    $("zur-karte").href = "index.html" + (q.toString() ? "#" + q : "");
  }

  async function aendern() {
    if (state.entwuerfe && !entwuerfeGeladen) {
      const w = await ladeJson("data/touren_entwuerfe.geojson");
      touren = touren.concat(w.features.map(eintrag));
      entwuerfeGeladen = true;
    }
    if (state.modus === "alle" && !weitereGeladen) {
      const w = await ladeJson("data/touren_weitere.geojson");
      touren = touren.concat(w.features.map(eintrag));
      weitereGeladen = true;
    }
    zeichnen();
  }

  document.querySelector(`input[name=modus][value=${state.modus}]`).checked = true;
  $("entwuerfe").checked = state.entwuerfe;
  $("entwuerfe").addEventListener("change", e => { state.entwuerfe = e.target.checked; aendern(); });
  document.querySelectorAll("input[name=modus]").forEach(r =>
    r.addEventListener("change", e => { state.modus = e.target.value; aendern(); }));
  for (const [k, t] of GERAETE) {
    const l = document.createElement("label");
    l.innerHTML = `<input type="checkbox" value="${k}"> ${esc(t)}`;
    const cb = l.firstChild; cb.checked = state.geraete.has(k);
    cb.addEventListener("change", () => { cb.checked ? state.geraete.add(k) : state.geraete.delete(k); zeichnen(); });
    $("geraete").appendChild(l);
  }
  const cbVoll = $("nur-vollstaendig");
  cbVoll.checked = state.vollstaendig;
  if (!meta.bewertung_erfasst) { cbVoll.disabled = true; $("stufe-notiz").textContent = "Noch nicht verfügbar: Bewertungsdaten fehlen."; }
  cbVoll.addEventListener("change", () => { state.vollstaendig = cbVoll.checked; zeichnen(); });
  aendern();
})().catch(e => { document.getElementById("zaehlung").textContent = "Die Daten konnten nicht geladen werden: " + e.message; });