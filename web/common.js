// Gemeinsame Funktionen fuer Karte und Liste.
const STRICH = { ja: "10 8", nein: null, offen: "2 6 10 6", ohne: null };
const STRICH_TEXT = {
  ja: "gestrichelt: aktive Hilfsperson erforderlich und/oder nur für Geübte empfohlen",
  nein: "durchgezogen: keine Hilfsperson nötig",
  offen: "strichpunktiert: Angabe zur Hilfsperson noch nicht erfasst",
  ohne: "dünn durchgezogen: nicht klassifiziert (kein Report)",
};
const GERAETE = [
  ["rollstuhl_r1", "R1 – ohne Antrieb (ggf. mit FreeWheel)"],
  ["rollstuhl_r2", "R2 – leichte Antriebshilfe"],
  ["rollstuhl_r3", "R3 – starke Antriebshilfe"],
  ["handbike", "Handbike"],
  ["unklar", "Gerät unklar / Sonstiges"],
];
const ENTWURF_TEXT = "Entwurf: Diese Tour ist auf alpenvereinaktiv.com noch nicht veröffentlicht. Die Daten sind vorläufig und nicht geprüft.";
const HINWEIS = "Die Einstufung gilt nur für das dokumentierte Gerät. Eine Tour gilt nie pauschal als barrierefrei.";

function geraetGruppe(k) { return (k === "rollstuhl_unklar" || k === "sonstiges") ? "unklar" : k; }

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

async function ladeJson(url) {
  const r = await fetch(url);
  if (!r.ok) throw new Error(url + ": " + r.status);
  return r.json();
}

function reportText(rep) {
  if (!rep) return "kein Report";
  const l = [["Gehbeeinträchtigung", rep.gehbehinderung], ["Hörbeeinträchtigung", rep.hoerbeeintraechtigung],
             ["Sehbeeinträchtigung", rep.sehbeeintraechtigung], ["Kognitive Beeinträchtigung", rep.kognitive_beeintraechtigung]];
  return l.map(([n, v]) => n + ": " + (v || "keine Angabe")).join("; ");
}

function detailHtml(d) {
  const meta = [d.region, d.strecke_km != null ? d.strecke_km + " km" : null,
                d.aufstieg_m != null ? "↑ " + d.aufstieg_m + " m" : null].filter(Boolean).join(" · ");
  return `<h3>${esc(d.titel)}</h3>${d.entwurf ? `<p class="entwurf"><strong>${esc(ENTWURF_TEXT)}</strong></p>` : ""}<dl>
    <dt>Gerät</dt><dd>${esc(d.kategorie)}${d.geraet ? " (" + esc(d.geraet) + ")" : ""}</dd>
    <dt>Stufe</dt><dd>${esc(d.stufe)}</dd>
    <dt>Linie</dt><dd>${esc(STRICH_TEXT[d.hilfsperson])}</dd>
    <dt>Report</dt><dd>${esc(reportText(d.report))}</dd>
    ${meta ? `<dt>Daten</dt><dd>${esc(meta)}</dd>` : ""}</dl>
    <p><strong>${esc(HINWEIS)}</strong></p>
    ${d.url ? `<p><a href="${esc(d.url)}" target="_blank" rel="noopener">Tour auf alpenvereinaktiv.com ansehen<span class="sr-only"> (öffnet in neuem Tab)</span></a></p>` : ""}`;
}

function nav(aktuell) {
  const seiten = [["index.html", "Karte"], ["liste.html", "Liste"], ["erklaerung.html", "Erklärung"], ["quellen.html", "Quellen und Lizenz"]];
  return `<a class="skip" href="#inhalt">Zum Inhalt springen</a>
  <header class="site"><h1>Barrierefreiheitslayer – Team Inklusion ÖAV</h1>
  <nav aria-label="Hauptnavigation"><ul>${seiten.map(([h, t]) =>
    `<li><a href="${h}"${h === aktuell ? ' aria-current="page"' : ""}>${t}</a></li>`).join("")}</ul></nav></header>`;
}

function fuss() {
  return `<footer class="site"><ul><li><a href="impressum.html">Impressum</a></li><li><a href="datenschutz.html">Datenschutz</a></li>
  <li><a href="quellen.html">Quellen und Lizenz</a></li></ul></footer>`;
}

function seiteAufbauen(aktuell) {
  document.body.insertAdjacentHTML("afterbegin", nav(aktuell));
  document.body.insertAdjacentHTML("beforeend", fuss());
}