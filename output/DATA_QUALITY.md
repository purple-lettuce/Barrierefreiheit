# Datenqualität – Linien der Team-Inklusion-ÖAV-Touren

Automatisch erzeugt durch `scripts/extract_team_inklusion_tracks.py`.

## Überblick

- Touren in der Excel (Team Inklusion ÖAV): **444**
- davon mit zugeordneter Linie: **444**, ohne Linie: **0**
- Geometrien im Shapefile: **228532**, davon Team Inklusion: **444**
- Geometrien ohne passende Tour: 0 (ID nicht im gesamten Excel-Export); 228088 gehören zu anderen Quellen
- Mehrfach zugeordnete Geometrien (IDs mit >1 Feature): 0; doppelte IDs im Shapefile gesamt: 0

## Touren ohne Linie

Keine.

## Quelle und Join

- Ebene: `av_routes_lnString_261020` (LineString), Attribute: ID, AKTIVITäT
- Tour-ID-Attribut: `ID` (Gleitkommazahl, z. B. `804034456.0`); Join-Feld in der Excel: `id`
- ID-Normalisierung: siehe `scripts/tour_ids.py` (Text, Leerzeichen/Dezimalendung/Präfix/führende Nullen entfernen). Angewandt im Shapefile: {'float_zu_int': 228532}; in der Excel: 0 IDs verändert.
- CRS laut .prj: WGS 84 (EPSG:4326); Transformation nach EPSG:4326: nicht nötig

## Geometrieprüfung

- Leere Geometrien: 0; ungültig vor Reparatur: 0; repariert: 0; nicht repariert: 0
- Z-Werte entfernt (auf 2D reduziert): 0
- Touren aus mehreren Shapefile-Features: 0 (Ergebnis: MultiLineString erhalten: 0)


## Vereinfachung und Dateigrößen

- Douglas-Peucker, preserve_topology=True, Toleranz 1.0 m in EPSG:3035, danach Rundung auf 6 Nachkommastellen
- Stützpunkte: 178108 → 176243 (−1.0 %)
- Abweichung (Hausdorff, Meter): max 1.0, Median 0.0
- Größen: Shapefile gesamt 1309.1 MB; Team-Linien unvereinfacht (GeoJSON) 4.39 MB; GPKG 3.35 MB; GeoJSON 4.95 MB

## Aufschlüsselung der Touren mit Linie

- veröffentlicht: Ja: 256, Nein: 188
- mit Report: Nein: 354, Ja: 90
- Kategorie: nicht_klassifiziert: 354, handbike: 42, rollstuhl_r3: 33, rollstuhl_unklar: 12, rollstuhl_r1: 2, sonstiges: 1

Kombination veröffentlicht | Report | Kategorie:

- Ja|Ja|handbike: 40
- Ja|Ja|rollstuhl_r1: 2
- Ja|Ja|rollstuhl_r3: 32
- Ja|Ja|rollstuhl_unklar: 10
- Ja|Ja|sonstiges: 1
- Ja|Nein|nicht_klassifiziert: 171
- Nein|Ja|handbike: 2
- Nein|Ja|rollstuhl_r3: 1
- Nein|Ja|rollstuhl_unklar: 2
- Nein|Nein|nicht_klassifiziert: 183

## Plausibilität der Koordinaten

- Bounding Box (lon_min, lat_min, lon_max, lat_max): [-5.09846, 43.0719, 16.69815, 57.26557]; Erwartung Alpenraum inkl. Rand: [5.0, 43.5, 17.5, 49.5]
- Touren außerhalb der Alpen-Box: 27 (liegen laut Titel/Koordinaten in Deutschland bzw. Schottland, also außerhalb der Alpen, aber plausibel); außerhalb der Europa-Box [-11.0, 35.0, 25.0, 60.0]: 0
- Verdacht auf vertauschte Längen-/Breitengrade: 0
  - 803913571: Karl-Heine-Kanal
  - 801832763: Etappe 1 FünfFlüsseRadweg Eckenthal - Amberg 19.06.23
  - 58301793: Elberadweg Dresden - Magdeburg
  - 40952482: Demmin Loitz
  - 41020657: Waren Müritz
  - 51703342: Handbike-Tour Nabburg
  - 812002463: Rollstuhlwanderung am Erlebnispfad Silberborn (barrierefrei)
  - 811813152: Rollstuhltour JH Lauterbach - Prinzenstein (barrierefrei)
  - 805104063: Handbike-Tour Saar-Mosel (barrierefrei)
  - 806015572: Swisstrack-Wanderung am Loch Affric
  - 806014835: Swisstrack-Wanderung um den Loch an Eilein
  - 51703318: Handbike-Tour Schönsee Oberpfälzer Wald
  - 803910244: Handbiketour Potsdam - Werder
  - 41231514: Tour 2 Bayreuth
  - 41228699: Bayreuth
  - 802051391: Etappe 6: FünfFlüsseRadweg Nürnberg-Eckenthal 24.06.23
  - 803719386: Potsdam - Werder - Schlänitzsee
  - 803910448: Handbike Tour Schlösserrunde Potsdam
  - 803738646: Tourenplanung am 2023-09-17
  - 41112559: Müritz Nationalpark
  - 808795145: Lange Radtour von Sankt Georgen im Lavanttal auf die Sella di Camporosso (Saifnitzer Sattel) nach Rimini über Treviso, Padova (Padua) und Rovigo
  - 808795144: Tourenplanung am 07.07.2025 08:58:20
  - 806014654: Swisstrack-Wanderung um den Glencoe Lochan
  - 805006538: Handbike-Tour Etappe 2: Merzig - Trier (barrierefrei)
  - 805007612: Handbike-Tour Etappe 4: Bernkastel-Cochem (barrierefrei)
  - 805007407: Handbike-Tour Etappe 3: Trier - Bernkastel (barrierefrei)
  - 805007725: Handbike-Tour Etappe 5: Cochem - Koblenz (barrierefrei)

## Hinweise

- Eine Tour gilt nie pauschal als barrierefrei; `category`/`device` beziehen sich nur auf das dokumentierte Gerät.
- Nicht Team-Inklusion-Geometrien werden nicht ausgegeben.
