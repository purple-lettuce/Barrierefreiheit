# Datenmodell der Website (AP-02)

Erzeugt von `scripts/build_web_export.py` aus `output/team_inklusion_touren_linien.geojson` in `web/data/`.

## Dateien
| Datei | Inhalt |
|---|---|
| `touren_report.geojson` | veröffentlichte Touren mit Report (Startdatei der Karte) |
| `touren_weitere.geojson` | veröffentlichte Touren ohne Report (nachgeladen im Modus „Alle Touren") |
| `touren_entwuerfe.geojson` | nicht veröffentlichte Touren, Property `e = 1` (nachgeladen, nur auf Wunsch) |
| `details.json` | Texte je Tour-ID für Popup und Liste |
| `meta.json` | Datenstand, Zählungen, Kategorien mit Farben |

## Properties in den GeoJSON-Dateien
| Feld | Bedeutung |
|---|---|
| `id` | Tour-ID (Text) |
| `k` | Kategorie: `rollstuhl_r1`, `rollstuhl_r2`, `rollstuhl_r3`, `handbike`, `rollstuhl_unklar`, `sonstiges`, `nicht_klassifiziert` |
| `h` | Linienart: `ja` (Hilfsperson und/oder Geübte), `nein`, `offen` (nicht erfasst), `ohne` (kein Report) |
| `e` | nur bei Entwürfen: 1 |

## Felder in `details.json`
`titel`, `entwurf`, `aktivitaet`, `kategorie` (Anzeigename), `geraet`, `stufe`, `stufe_grund`, `hilfsperson` (wie `h`), `report` (vier Gruppen: Geh-, Hör-, Seh-, kognitive Beeinträchtigung), `strecke_km`, `aufstieg_m`, `abstieg_m`, `region`, `land`, `kurzbeschreibung`, `url` (bei Entwürfen `null`), `bewertung` (nur wenn erfasst).

## Nicht übernommen
`flag_barrierefrei_av` (nur Selbstangabe, keine Einstufung), interne Felder wie Bearbeitungsstatus.

## Vereinfachung
Douglas-Peucker 5 m, Koordinaten auf 5 Nachkommastellen. Das Quell-GeoJSON ist bereits mit 1 m vereinfacht.

## Bewertungsdaten (AP-03)
`data/bewertung.csv`, eine Zeile je Tour mit Report (Zuordnung über `id`).

| Spalte | Werte |
|---|---|
| `schluesselstellen` | ganze Zahl |
| `wc_barrierefrei` | `ja` / `nein` |
| `hilfsperson_erforderlich` | `ja` / `nein` |
| `geuebt` | `ja` / `nein` (leer = nein) |
| `status` | `erfasst` oder `offen` |
| `bemerkung` | Freitext |

Der Export bricht ab bei unbekannter oder doppelter ID, fehlenden Zeilen oder ungültigen Werten. Quelle der Werte: Reports in alpenvereinaktiv, gepflegt vom Team Inklusion (D7).