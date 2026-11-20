# Barrierefreiheitslayer – Team Inklusion ÖAV

Kartenlayer mit den Touren des „Team Inklusion ÖAV“ (alpenvereinaktiv, Quellen-ID 806030126).
Gelöschte Touren (Status „Gelöscht“) sind entfernt: **444 Touren**, alle mit Linie.

## Ergebnisdateien (`output/`)
| Datei | Zweck |
|---|---|
| `team_inklusion_touren_linien.gpkg` | Layer-Basis (QGIS u. a.), Linien + alle Attribute, EPSG:4326 |
| `team_inklusion_touren_linien.geojson` | gleicher Inhalt für Web-Anwendungen |
| `team_inklusion_touren_alle.xlsx` | Tabelle und Auswertung (Alle Touren, Filterbilanz, Abweichungen, Qualität) |
| `validation_report.json`, `DATA_QUALITY.md` | Prüfbericht zu Zuordnung und Geometrien |

## Layer-Logik
- Standardansicht: `hat_report = 'Ja'` (Touren mit Report zur Barrierefreiheit); übrige Touren lassen sich über denselben Filter zuschalten.
- Weitere Filter: `veroeffentlicht` (Regel: „Veröffentlicht am“ enthält ein Datum), `category`, `activity`.
- Kategorien: `rollstuhl_r1`, `rollstuhl_r2`, `rollstuhl_r3`, `rollstuhl_unklar`, `handbike`, `sonstiges`, `nicht_klassifiziert`.
- Eine Tour gilt nie pauschal als barrierefrei; die Einstufung bezieht sich nur auf das dokumentierte Gerät (`device`).

## Neu erzeugen
Rohdaten (nicht im Repository): Excel-Export `av_routes_*.xlsx` und Shapefile-Ordner `routes/`.

    pip install -r requirements.txt
    python scripts/build_team_inklusion_excel.py --routes <av_routes.xlsx> --out output
    python scripts/extract_team_inklusion_tracks.py --shp <routes/….shp> --tours output/team_inklusion_touren_alle.xlsx --out output --full-export <av_routes.xlsx>

`scripts/tour_ids.py` enthält die gemeinsame ID-Normalisierung.

## Website (Demo)
Statische Seite in `web/` (Leaflet, OSM-Kacheln). Dokumentation in `docs/`: Regelkarte, Datenmodell, Aktualisierung, Betrieb, Qualität. Ergebnisse von `ROADMAP.md` AP-01 bis AP-17, soweit nicht durch D2, D6, D7 blockiert.

    python scripts/build_web_export.py      # erzeugt web/data/ und prüft die Daten
    python -m unittest discover -s tests
    python -m http.server 8765 --directory web   # http://localhost:8765