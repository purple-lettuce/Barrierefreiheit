"""Web-Export (AP-02, AP-03, AP-04): erzeugt aus output/ die schlanken Dateien fuer die Website.

Ausgabe in web/data/:
  touren_report.geojson   veroeffentlichte Touren mit Report (Standardansicht, Geometrie + wenige Attribute)
  touren_weitere.geojson  veroeffentlichte Touren ohne Report (Modus "Alle Touren", wird nachgeladen)
  touren_entwuerfe.geojson nicht veroeffentlichte Touren (Entwuerfe, nur auf Wunsch der Nutzer:innen, gekennzeichnet)
  details.json            Popup-/Listentexte je Tour-ID
  meta.json               Zaehlungen, Datenstand, Kategorien

Nicht veroeffentlichte Touren sind als Entwurf gekennzeichnet (Entscheidung Projektphase "Produkt zeigen":
Standardansicht zeigt sie nicht, sie lassen sich zuschalten). `flag_barrierefrei_av` wird nicht uebernommen.
Danach laeuft die Datenpruefung (AP-05, scripts/check_web_data.py).

    python scripts/build_web_export.py [--bewertung data/bewertung.csv] [--tol 5]
"""
import argparse
import csv
import json
import sys
from datetime import date
from pathlib import Path

import geopandas as gpd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from web_rules import KATEGORIEN, hilfsperson_stil, stufe  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
TOUR_URL = "https://www.alpenvereinaktiv.com/de/tour/{id}/"  # leitet auf die Tour weiter (geprueft 2026-11-20)
BEWERTUNG_FELDER = ["id", "titel", "schluesselstellen", "wc_barrierefrei", "hilfsperson_erforderlich",
                    "geuebt", "status", "bemerkung"]


def lade_bewertung(pfad, report_touren):
    """Liest die Bewertungsdaten (AP-03). Legt eine Vorlage an, wenn die Datei fehlt."""
    if not pfad.exists():
        pfad.parent.mkdir(parents=True, exist_ok=True)
        with open(pfad, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, BEWERTUNG_FELDER)
            w.writeheader()
            for tid, titel in sorted(report_touren.items(), key=lambda x: x[1]):
                w.writerow({"id": tid, "titel": titel, "status": "offen"})
        print(f"Vorlage angelegt: {pfad} ({len(report_touren)} Touren, Status 'offen')")
    daten = {}
    with open(pfad, encoding="utf-8-sig", newline="") as f:
        for z in csv.DictReader(f):
            tid = z["id"].strip()
            if tid not in report_touren:
                raise SystemExit(f"Bewertung: ID {tid} ist keine Tour mit Report")
            if tid in daten:
                raise SystemExit(f"Bewertung: ID {tid} doppelt")
            if z["status"].strip() == "erfasst":
                try:
                    ss = int(z["schluesselstellen"])
                except ValueError:
                    raise SystemExit(f"Bewertung {tid}: schluesselstellen fehlt/keine Zahl")
                wc = z["wc_barrierefrei"].strip().lower()
                hp = z["hilfsperson_erforderlich"].strip().lower()
                gu = z["geuebt"].strip().lower() or "nein"
                for name, val in (("wc_barrierefrei", wc), ("hilfsperson_erforderlich", hp), ("geuebt", gu)):
                    if val not in ("ja", "nein"):
                        raise SystemExit(f"Bewertung {tid}: {name} muss ja/nein sein")
                daten[tid] = {"ss": ss, "wc": wc, "hp": hp, "gu": gu}
            elif z["status"].strip() == "offen":
                daten[tid] = None
            else:
                raise SystemExit(f"Bewertung {tid}: status muss 'erfasst' oder 'offen' sein")
    fehlend = set(report_touren) - set(daten)
    if fehlend:
        raise SystemExit(f"Bewertung: {len(fehlend)} Touren mit Report ohne Eintrag (z. B. {sorted(fehlend)[0]})")
    return daten


def text(v):
    return None if v is None or v != v else str(v)


def zahl(v):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(ROOT / "output" / "team_inklusion_touren_linien.geojson"))
    ap.add_argument("--bewertung", default=str(ROOT / "data" / "bewertung.csv"))
    ap.add_argument("--out", default=str(ROOT / "web" / "data"))
    ap.add_argument("--tol", type=float, default=5.0, help="Vereinfachungstoleranz in Metern")
    a = ap.parse_args()

    gdf = gpd.read_file(a.src)
    quelle = {
        "gesamt": len(gdf),
        "mit_report": int((gdf.hat_report == "Ja").sum()),
        "mit_report_veroeffentlicht": int(((gdf.hat_report == "Ja") & (gdf.veroeffentlicht == "Ja")).sum()),
        "mit_report_nicht_veroeffentlicht": int(((gdf.hat_report == "Ja") & (gdf.veroeffentlicht != "Ja")).sum()),
    }
    pub = gdf.copy()
    pub["geometry"] = (pub.to_crs(3035).geometry.simplify(a.tol, preserve_topology=True)
                       .to_crs(4326))

    report_touren = dict(zip(gdf[gdf.hat_report == "Ja"].id.astype(str), gdf[gdf.hat_report == "Ja"].title))
    bew = lade_bewertung(Path(a.bewertung), report_touren)

    report_f, weitere_f, entwuerfe_f, details = [], [], [], {}
    for _, r in pub.iterrows():
        tid = str(r.id)
        cat = r.category
        entwurf = r.veroeffentlicht != "Ja"
        d = bew.get(tid)
        s, grund = stufe(cat, d and d["ss"], d and d["wc"], d and d["hp"])
        stil = hilfsperson_stil(d and d["hp"], d and d["gu"]) if r.hat_report == "Ja" else "ohne"
        geom = json.loads(gpd.GeoSeries([r.geometry]).to_json(show_bbox=False))["features"][0]["geometry"]
        geom["coordinates"] = _runden(geom["coordinates"])
        feat = {"type": "Feature", "geometry": geom, "properties": {"id": tid, "k": cat, "h": stil}}
        if entwurf:
            feat["properties"]["e"] = 1
            entwuerfe_f.append(feat)
        else:
            (report_f if r.hat_report == "Ja" else weitere_f).append(feat)
        details[tid] = {
            "titel": r.title,
            "entwurf": bool(entwurf),
            "aktivitaet": text(r.activity),
            "kategorie": KATEGORIEN[cat]["label"],
            "geraet": text(r.device),
            "stufe": s,
            "stufe_grund": grund,
            "hilfsperson": stil,
            "report": None if r.hat_report != "Ja" else {
                "gehbehinderung": text(r.report_gehbehinderung),
                "hoerbeeintraechtigung": text(r.report_hoerbeeintraechtigung),
                "sehbeeintraechtigung": text(r.report_sehbeeintraechtigung),
                "kognitive_beeintraechtigung": text(r.report_kognitive_beeintraechtigung),
            },
            "strecke_km": None if zahl(r.strecke_m) is None else round(zahl(r.strecke_m) / 1000, 1),
            "aufstieg_m": zahl(r.aufstieg_hm),
            "abstieg_m": zahl(r.abstieg_hm),
            "region": text(r.region),
            "land": text(r.land),
            "kurzbeschreibung": text(r.kurzbeschreibung),
            "url": None if entwurf else TOUR_URL.format(id=tid),
        }
        if d:
            details[tid]["bewertung"] = {"schluesselstellen": d["ss"], "wc": d["wc"], "hilfsperson": d["hp"],
                                         "geuebt": d["gu"]}

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for name, feats in (("touren_report", report_f), ("touren_weitere", weitere_f),
                         ("touren_entwuerfe", entwuerfe_f)):
        (out / f"{name}.geojson").write_text(
            json.dumps({"type": "FeatureCollection", "features": feats}, separators=(",", ":")), encoding="utf-8")
    (out / "details.json").write_text(json.dumps(details, ensure_ascii=False, separators=(",", ":")),
                                      encoding="utf-8")
    meta = {
        "stand": date.today().isoformat(),
        "quelle": quelle,
        "web": {"mit_report": len(report_f), "ohne_report": len(weitere_f),
                "entwuerfe": len(entwuerfe_f), "entwuerfe_mit_report": sum(1 for f in entwuerfe_f if f["properties"]["k"] != "nicht_klassifiziert")},
        "bewertung_erfasst": sum(1 for v in bew.values() if v),
        "bewertung_offen": sum(1 for v in bew.values() if not v),
        "kategorien": {k: v for k, v in KATEGORIEN.items()},
    }
    (out / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    for n in ("touren_report.geojson", "touren_weitere.geojson", "touren_entwuerfe.geojson", "details.json"):
        print(f"{n}: {(out / n).stat().st_size / 1e6:.2f} MB")

    import check_web_data
    sys.exit(check_web_data.main([str(out)]))


def _runden(c):
    if isinstance(c[0], (int, float)):
        return [round(c[0], 5), round(c[1], 5)]
    return [_runden(x) for x in c]


if __name__ == "__main__":
    main()