"""Datenpruefung (AP-05): laeuft bei jedem Export und als Test (tests/test_web_data.py).

Erwartete Zaehlungen sind absichtlich fest eingetragen. Aendern sich die Quelldaten,
muessen sie hier bewusst angepasst werden.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from web_rules import KATEGORIEN  # noqa: E402

ERWARTET_QUELLE = {"gesamt": 444, "mit_report": 90, "mit_report_veroeffentlicht": 85,
                   "mit_report_nicht_veroeffentlicht": 5}
MAX_KARTE_MB = 2.0  # Richtwert: Startdatei der Karte (Touren mit Report)
STILE = {"ja", "nein", "offen", "ohne"}


def pruefe(datenordner):
    d = Path(datenordner)
    fehler = []
    meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
    details = json.loads((d / "details.json").read_text(encoding="utf-8"))
    for k, v in ERWARTET_QUELLE.items():
        if meta["quelle"].get(k) != v:
            fehler.append(f"Quelle {k}: {meta['quelle'].get(k)} statt {v}")

    ids = set()
    zaehl = {}
    for name in ("touren_report", "touren_weitere", "touren_entwuerfe"):
        gj = json.loads((d / f"{name}.geojson").read_text(encoding="utf-8"))
        zaehl[name] = len(gj["features"])
        for f in gj["features"]:
            p = f["properties"]
            if p["k"] not in KATEGORIEN:
                fehler.append(f"{p['id']}: Kategorie {p['k']!r} nicht in Whitelist")
            if p["h"] not in STILE:
                fehler.append(f"{p['id']}: Strichart {p['h']!r} ungueltig")
            if (p.get("e") == 1) != (name == "touren_entwuerfe") or details.get(p["id"], {}).get("entwurf") != (p.get("e") == 1):
                fehler.append(f"{p['id']}: Entwurf-Kennzeichnung passt nicht zu Datei {name}")
            if name != "touren_entwuerfe" and (name == "touren_report") != (p["k"] != "nicht_klassifiziert"):
                fehler.append(f"{p['id']}: Kategorie {p['k']} passt nicht zu Datei {name}")
            if f["geometry"]["type"] not in ("LineString", "MultiLineString") or not f["geometry"]["coordinates"]:
                fehler.append(f"{p['id']}: Geometrie ungueltig")
            if p["id"] in ids:
                fehler.append(f"{p['id']}: doppelt")
            ids.add(p["id"])
            if p["id"] not in details:
                fehler.append(f"{p['id']}: kein Eintrag in details.json")
    if zaehl["touren_entwuerfe"] != 188:
        fehler.append(f"Web: {zaehl['touren_entwuerfe']} Entwuerfe statt 188")
    if ids != set(details):
        fehler.append("details.json und Geometrien haben unterschiedliche IDs")
    if zaehl["touren_report"] != ERWARTET_QUELLE["mit_report_veroeffentlicht"]:
        fehler.append(f"Web: {zaehl['touren_report']} Touren mit Report statt "
                      f"{ERWARTET_QUELLE['mit_report_veroeffentlicht']} (veroeffentlicht)")
    if any(t["report"] is None for i, t in details.items() if i in ids and t["kategorie"] != "Nicht klassifiziert"):
        fehler.append("Tour mit Kategorie, aber ohne Report")
    if any("flag" in k for t in details.values() for k in t):
        fehler.append("flag_barrierefrei_av darf nicht uebernommen werden")
    groesse = (d / "touren_report.geojson").stat().st_size / 1e6
    if groesse > MAX_KARTE_MB:
        fehler.append(f"touren_report.geojson {groesse:.2f} MB > {MAX_KARTE_MB} MB")
    return fehler, zaehl


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    ordner = argv[0] if argv else str(Path(__file__).resolve().parent.parent / "web" / "data")
    fehler, zaehl = pruefe(ordner)
    if fehler:
        print("DATENPRUEFUNG FEHLGESCHLAGEN:")
        for f in fehler:
            print(" -", f)
        return 1
    print(f"Datenpruefung ok: Quelle {ERWARTET_QUELLE['gesamt']} / {ERWARTET_QUELLE['mit_report']} / "
          f"{ERWARTET_QUELLE['mit_report_veroeffentlicht']} / {ERWARTET_QUELLE['mit_report_nicht_veroeffentlicht']}; "
          f"Web: {zaehl}")
    return 0


if __name__ == "__main__":
    sys.exit(main())