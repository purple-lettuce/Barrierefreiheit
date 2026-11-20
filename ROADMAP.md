# Roadmap – Website „Barrierefreiheitslayer“

Stand: 2026-11-20. Vorschlag zur Abstimmung, noch nicht umgesetzt.

## 1. Ausgangslage aus den Daten

- **444 Touren** mit Linie in `output/team_inklusion_touren_linien.geojson` (rund 5,2 MB, EPSG:4326).
- **90 Touren mit Report**, davon **85 veröffentlicht** und **5 nicht veröffentlicht**.
- Kategorien bei Touren mit Report: R1 = 2, R2 = **0**, R3 = 33, Handbike = 42, unklar = 12, sonstiges = 1. Die übrigen 354 sind „nicht klassifiziert“. Handbike kommt nur bei Radtour bzw. Fernradweg vor, die Rollstuhl-Kategorien nur bei Wanderung (geprüft).
- Der Export enthält **nicht**: Anzahl der Schlüsselstellen, Vorhandensein eines barrierefreien WCs, Angabe „Hilfsperson erforderlich“. Ohne diese Felder lässt sich die Stufe „vollständig“ oder „teilweise“ nicht berechnen (→ AP-03).
- `flag_barrierefrei_av` ist laut Skript nur eine Selbstangabe aus dem Export. Die Website verwendet es nicht als Einstufung.
- Die Kriterien stammen aus dem Leitfaden und der Checkliste (Dateien im Projektordner).

## 2. Entscheidungen und offene Punkte

| # | Frage | Hintergrund |
|---|---|---|
| D1 | Was bedeutet „teilweise barrierefrei“? | Leitfaden: höchstens 2 Schlüsselstellen **und** aktive Hilfsperson. Checkliste: „alle anderen Touren“. Der Fall „keine Schlüsselstelle, aber kein WC“ ist nur in der Checkliste geregelt. Die Checkliste spricht von drei Stufen, nennt aber nur zwei. **Entschieden: Leitfaden.** Abweichungen und offene Folgefragen: `output/Abweichung_Leitfaden_Checkliste.md`. |
| D2 | Erhalten Handbike-Touren eigene Stufen? | **Teilweise beantwortet:** Handbike-Touren sind Aktivität „Radfahren“. Die Checkliste bewertet Radtouren über die technische Schwierigkeit 1 bis 6. Der Leitfaden enthält nur Kriterien für Rollstuhl-Touren (Wandern). Offen: ob Handbike zusätzlich nach Schlüsselstellen und Hilfsperson eingestuft wird. 42 Touren mit Report betroffen. |
| D3 | Sollen die 5 nicht veröffentlichten Touren mit Report sichtbar sein? | **Entschieden: nein.** Standardfilter nur „veröffentlicht“. |
| D4 | Dürfen Kriterientexte auf der öffentlichen Seite stehen? | **Entschieden: ja.** Der Leitfaden ist mit „zur internen Verwendung“ gekennzeichnet. |
| D5 | Welche Basiskarte? | **Entschieden: OSM.** Die Nutzungsrichtlinien der OSM-Kacheln sind bei der Umsetzung zu beachten. |
| D6 | Wer ist Verantwortliche/r für Hosting, Domain, Impressum und Datenschutz? | **tbd.** Blockiert AP-15. |
| D7 | Wer pflegt die Bewertungsdaten (Schlüsselstellen, WC, Hilfsperson)? | **tbd.** Blockiert AP-03. Laut Checkliste Abschnitt VIII werden Touren erst nach Meldung an barrierefreiewege@jugend.alpenverein.at sichtbar. |

**Rollenverteilung:** Die inhaltliche Arbeit (Touren, Reports, Bewertungen) hat das Team Inklusion geleistet. Die technische Umsetzung übernehmen wir.

## 3. Farbkonzept (Vorschlag)

**Prinzip:** Farbe = Gerät, für das die Strecke geeignet ist. Strichart = Bedingung.

- **Farbe (Gerät):** Die Kategorie ist eindeutig und deckt sich mit den Leitfaden-Stufen R1 bis R3.
- **Strichart (Bedingung):** durchgezogen = keine Hilfsperson nötig. Gestrichelt = aktive Hilfsperson erforderlich und/oder nur für Geübte empfohlen.

Warum nicht eine Farbe pro Bedingung: Die Bedingungen überlappen. Eine Tour kann zugleich elektrisch, nur mit Hilfsperson und nur für Geübte sein. Eine einzige Farbe müsste dann eine Bedingung verschweigen.

| Kategorie | Bedeutung | Farbe | Hex | Kontrast zum OSM-Hintergrund (#F2EFE9) |
|---|---|---|---|---|
| R1 | ohne Antrieb (ggf. mit FreeWheel) | Grün | `#00785A` | 4,8 : 1 |
| R2 | leichte Antriebshilfe (z. B. Smoov, Emotion) | Blau | `#0072B2` | 4,5 : 1 |
| R3 | starke Antriebshilfe (z. B. Swiss Trac) | Orange | `#B34700` | 4,8 : 1 |
| Handbike | Handbike, Aktivität Radfahren (Stufen offen, siehe D2) | Violett | `#9C3D7E` | 5,4 : 1 |
| unklar / sonstiges | Gerät nicht bestimmbar bzw. Sonstiges | Grau | `#5E5E5E` | 5,7 : 1 |
| nicht klassifiziert | nur im Modus „Alle Touren“ | Hellgrau, dünn | `#8A8A8A` | 3,0 : 1 (knapp) |

Die Kontraste sind gegen die Grenze von 3 : 1 für Grafikelemente (WCAG 2.1, 1.4.11) geprüft. Die Farbe ist nie die einzige Unterscheidung: Die Strichart kommt hinzu, und Rot-Grün-Paare werden vermieden.

**Zuordnung zu den Vorschlägen aus der Anfrage:**

- „alle befahrbar“ → grün, durchgezogen (R1 ohne Hilfsperson)
- „nur mit Hilfsperson“ → gestrichelt
- „nur mit elektrischem Antrieb“ → blau (R2) oder orange (R3)
- „geübt“ → gestrichelt (laut Leitfaden „nur für Geübte“)

**Hinweis:** Zum Stand des Exports gibt es keine blauen Linien (R2 = 0). Die Legende zeigt R2 trotzdem, damit die Kategorie nicht verloren geht, sobald Touren nachgetragen werden.

## 4. Arbeitspakete

Größe: S = wenige Stunden, M = etwa 1 bis 2 Tage, L = mehrere Tage. Die Reihenfolge ergibt sich aus den Abhängigkeiten.

### Phase 0 – Klärung

**AP-01 Regeln festlegen** (S)
- Offen: D2 (Handbike-Stufen), D6 und D7. D1 sowie D3 bis D5 sind entschieden.`n- Eine Seite Regelkarte.
- Ergebnis: abgestimmte Definition von „vollständig“, „teilweise“ und Handbike.
- Abnahme: Regelkarte liegt im Projekt.

### Phase 1 – Daten

**AP-02 Datenmodell für die Website** (S)
- Felder: `id`, `title`, `kategorie`, `geraet`, `hat_report`, `veroeffentlicht`, `url`, `kurzbeschreibung`, Report-Kategorien.
- Nicht übernehmen: `flag_barrierefrei_av`.
- Ergebnis: Schema als kurze Dokumentation.

**AP-03 Bewertungsdaten übernehmen** (S–M, abhängig von D1 und D7)
- Je Tour: Anzahl Schlüsselstellen, barrierefreies WC ja/nein, Hilfsperson erforderlich ja/nein.
- Das Team Inklusion pflegt die Daten. Wir übernehmen die Werte als Lieferung, z. B. als CSV.`n- Quelle: Reports in alpenvereinaktiv (My Business → Inhalte → „Report für Barrierefreiheit“), gepflegt vom Team Inklusion.
- Ergebnis: CSV mit Zuordnung über die Tour-ID, im Build-Schritt eingelesen.
- Abnahme: Für jede der 90 Touren mit Report ist ein Eintrag vorhanden oder ausdrücklich „offen“.

**AP-04 Web-Export** (M, abhängig von AP-02)
- Build-Schritt, der aus `output/` eine schlanke Datei erzeugt: Geometrie und wenige Attribute für die Karte, Popup-Texte in einer separaten Datei.
- Zielgröße unter 2 MB für die Karte (Richtwert, zu prüfen).
- Abnahme: 444 Linien, 90 mit Report, 85 veröffentlicht.

**AP-05 Datenprüfung automatisieren** (S)
- Zählungen als Test: 444 / 90 / 85 / 5.
- Nur Werte aus der Whitelist der Kategorien zulassen.
- Der Test läuft bei jedem Export.

### Phase 2 – Karte

**AP-06 Kartengrundgerüst** (M)
- Statische Seite mit Leaflet, OSM-Standardkacheln als Prototyp (D5).
- Attribution „© OpenStreetMap-Mitwirkende“.
- Vollbild, mobile Ansicht.
- Abnahme: Karte lädt, Attribution sichtbar, auf dem Smartphone nutzbar.

**AP-07 Layer ein- und ausschalten** (S)
- Schalter für den Barrierefreiheitslayer, Grundkarte bleibt unverändert.
- Optional: Zustand im Link speichern.

**AP-08 Farbkonzept umsetzen** (S, abhängig von AP-01)
- Linienfarben und Strichart nach Abschnitt 3.
- Legende auf der Karte.

### Phase 3 – Filter und Inhalte

**AP-09 Anzeigefilter** (M)
- Zwei Modi: „Nur Touren mit Report“ (Standard) und „Alle Touren“.
- Optional: Filter nach Gerät (R1, R2, R3, Handbike).
- Optional nach AP-03: Filter „nur vollständig barrierefrei“.
- Abnahme: Zählung im Filter stimmt mit AP-05 überein.

**AP-10 Popup und Detailansicht** (M)
- Titel, Gerät, Stufe, Report-Kategorien, Link zur Tour.
- Immer der Hinweis: „Die Einstufung gilt nur für das dokumentierte Gerät. Eine Tour gilt nie pauschal als barrierefrei.“
- Link-Muster der Tour-URL prüfen, da `url` im Export leer ist.

**AP-11 Erklärseite** (S–M, abhängig von D4)
- Kategorien R1 bis R3, Handbike, „geübt“, „Hilfsperson“, Schlüsselstelle.
- Text aus Leitfaden und Checkliste, nur nach Klärung von D4.

**AP-12 Listenansicht als Alternative zur Karte** (M)
- Tabelle mit denselben Filtern, sortierbar.
- Für Menschen, die die Karte nicht bedienen können, und für Suchmaschinen.

### Phase 4 – Qualität

**AP-13 Barrierefreiheit der Website** (M)
- Ziel WCAG 2.1 AA.
- Prüfen: Tastaturbedienung, sichtbarer Fokus, Skip-Link, alternative Texte, Kontrast (Werte aus Abschnitt 3).
- Strichart zusätzlich zur Farbe, damit Farbsehschwächen keine Information verlieren.
- Prüfen, ob das österreichische Umsetzungsgesetz zum European Accessibility Act für die Seite gilt (Rechtsprüfung nötig).

**AP-14 Tests** (S–M)
- Browser: aktuelle Versionen von Chrome, Firefox, Safari.
- Mobile Geräte, Stichprobe mit Screenreader, Ladezeit.

### Phase 5 – Betrieb

**AP-15 Hosting, Domain, Impressum, Datenschutz** (M, abhängig von D6)
- Statisches Hosting, Domain.
- Datenschutzhinweis: OSM-Kacheln werden von einem Drittanbieter geladen. Keine Tracker auf der Seite.

**AP-16 Lizenz und Quellen** (S)
- Hinweis zur ODbL der OSM-Daten.
- Angabe der Datenquelle (Team Inklusion ÖAV) und des Datenstands.
- Hinweis, dass die Einstufung gerätebezogen ist.

**AP-17 Aktualisierungsablauf** (S, abhängig von D7)
- Ablauf: Skripte laufen lassen → Export → Prüfung (AP-05) → Veröffentlichung.
- Verantwortliche Person: tbd (D7). Meldeweg laut Checkliste VIII: barrierefreiewege@jugend.alpenverein.at.

## 5. Meilensteine

| Meilenstein | Inhalt | Pakete |
|---|---|---|
| M1 | Regeln und Daten stehen | AP-01 bis AP-05 |
| M2 | Karten-Prototyp mit Layer und Farben | AP-06 bis AP-08 |
| M3 | Filter, Popups, Listenansicht | AP-09 bis AP-12 |
| M4 | Qualität geprüft | AP-13, AP-14 |
| M5 | Veröffentlichung | AP-15 bis AP-17 |

## 6. Quellen im Projekt

- `Leitfaden Erfassung Rollstuhl Touren.pdf`: Kriterien R1 bis R3, Schlüsselstelle, geübte Person.
- `Checkliste Rolltuhltouren.pdf`: Beschreibung, Report-Kategorien, Veröffentlichungsweg.
- `output/team_inklusion_touren_linien.geojson`: Layer-Daten.
- `output/DATA_QUALITY.md`, `output/validation_report.json`: Prüfbericht.
- `scripts/build_team_inklusion_excel.py`: Einstufungslogik für Kategorien und Geräte.




