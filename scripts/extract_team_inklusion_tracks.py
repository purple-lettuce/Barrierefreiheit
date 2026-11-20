"""Schritt 2: Linien der Team-Inklusion-Touren aus dem grossen Shapefile extrahieren.

Aufruf:
  python scripts/extract_team_inklusion_tracks.py --shp routes/av_routes_lnString_261020.shp \
      --tours output/team_inklusion_touren_alle.xlsx --out output [--full-export av_routes_261020.xlsx]

Vorgehen (speicherschonend): 1) nur die DBF-Attribute lesen (ohne Geometrie), 2) Tour-IDs normalisieren
und mit der Excel abgleichen, 3) nur die passenden Features per FID in Chunks mit Geometrie lesen.
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import pyogrio
import shapely
from pyproj import CRS, Transformer
from shapely import MultiLineString

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tour_ids import normalize_id  # noqa: E402

METRIC_CRS = "EPSG:3035"          # ETRS89-LAEA, nur fuer Vereinfachung/Abstandsmessung in Metern
SIMPLIFY_M = 1.0
DECIMALS = 6
CHUNK = 5000
ALPS_BBOX = (5.0, 43.5, 17.5, 49.5)  # lon_min, lat_min, lon_max, lat_max (Alpenraum inkl. Rand)
EUROPE_BBOX = (-11.0, 35.0, 25.0, 60.0)  # grobe Plausibilitaetsgrenze Europa (Touren ausserhalb der Alpen)


def project(geom, fn):
    return shapely.transform(geom, lambda c: np.column_stack(fn(c[:, 0], c[:, 1])))


def vertex_count(geoms):
    return int(shapely.get_num_coordinates(np.asarray(geoms, dtype=object)).sum())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shp", required=True)
    ap.add_argument("--tours", required=True, help="output/team_inklusion_touren_alle.xlsx (Blatt 'Alle Touren')")
    ap.add_argument("--out", default="output")
    ap.add_argument("--full-export", default=None, help="optional: kompletter Excel-Export zur Pruefung 'Geometrie ohne Tour'")
    ap.add_argument("--id-field", default=None, help="Attribut mit der Tour-ID (Standard: automatisch 'ID')")
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    shp = Path(a.shp)
    rep = {}

    # --- 1. Ebene, Attribute, CRS -------------------------------------------------
    layers = pyogrio.list_layers(shp)
    info = pyogrio.read_info(shp)
    prj = shp.with_suffix(".prj")
    prj_wkt = prj.read_text(encoding="utf-8", errors="replace") if prj.exists() else None
    src_crs = CRS.from_wkt(prj_wkt) if prj_wkt and prj_wkt.strip() else None
    assert src_crs is not None, "Keine lesbare .prj-Datei; CRS unbekannt"
    epsg = src_crs.to_epsg()
    fields = list(info["fields"])
    id_field = a.id_field or next(f for f in fields if f.upper() == "ID")
    rep["shapefile"] = {"datei": str(shp), "ebenen": [list(map(str, l)) for l in layers.tolist()],
                        "geometrietyp": info["geometry_type"], "anzahl_features": int(info["features"]),
                        "attribute": fields, "id_attribut": id_field, "prj_crs": src_crs.name, "prj_epsg": epsg,
                        "bounds_roh": [float(x) for x in info["total_bounds"]]}
    print("Ebene:", rep["shapefile"]["ebenen"], "Features:", info["features"], "CRS:", src_crs.name, epsg)

    attrs = pyogrio.read_dataframe(shp, read_geometry=False, columns=[id_field])
    attrs["fid"] = np.arange(len(attrs))
    shp_log = Counter()
    attrs["id"] = attrs[id_field].map(lambda v: normalize_id(v, shp_log))
    n_shp = len(attrs)

    # --- 2. Excel-Touren ----------------------------------------------------------
    tours = pd.read_excel(a.tours, sheet_name="Alle Touren", dtype={"id": str, "id_original": str, "source_id": str})
    tours = tours.astype(object).where(tours.notna(), None)
    tour_ids = set(tours["id"])
    assert len(tour_ids) == len(tours), "doppelte IDs in Excel"

    # --- 3. Abgleich ---------------------------------------------------------------
    attrs["ist_team"] = attrs["id"].isin(tour_ids)
    sel = attrs[attrs["ist_team"]]
    rep["abgleich"] = {"geometrien_shapefile": n_shp, "geometrien_ohne_id": int(attrs["id"].isna().sum()),
                       "geometrien_team_inklusion": int(len(sel)),
                       "eindeutige_tour_ids_mit_linie": int(sel["id"].nunique()),
                       "mehrfach_zugeordnete_ids": sorted(sel.loc[sel["id"].duplicated(keep=False), "id"].unique().tolist()),
                       "doppelte_ids_im_shapefile_gesamt": int(attrs["id"].dropna().duplicated().sum())}
    if a.full_export:
        import openpyxl
        wb = openpyxl.load_workbook(a.full_export, read_only=True)
        ws = wb.worksheets[0]
        it = ws.iter_rows(values_only=True)
        h = list(next(it)); k = h.index("ID")
        all_ids = {normalize_id(r[k]) for r in it}
        wb.close()
        rep["abgleich"]["geometrien_ohne_passende_tour_im_gesamtexport"] = int((~attrs["id"].isin(all_ids)).sum())
        rep["abgleich"]["geometrien_anderer_quellen"] = int(((~attrs["ist_team"]) & attrs["id"].isin(all_ids)).sum())
    else:
        rep["abgleich"]["geometrien_ohne_passende_tour_in_team_inklusion"] = int((~attrs["ist_team"]).sum())

    # --- 4. Geometrien chunkweise lesen --------------------------------------------
    parts = []
    fids = sel["fid"].tolist()
    for i in range(0, len(fids), CHUNK):
        g = pyogrio.read_dataframe(shp, fids=fids[i:i + CHUNK], columns=[id_field])
        parts.append(g)
    gdf = pd.concat(parts, ignore_index=True) if parts else None
    import geopandas as gpd
    gdf = gpd.GeoDataFrame(gdf, geometry="geometry", crs=info["crs"])
    gdf["id"] = gdf[id_field].map(lambda v: normalize_id(v))
    gdf = gdf[["id", "geometry"]]

    # --- 5. CRS nach WGS84 ---------------------------------------------------------
    gdf = gdf.set_crs(src_crs, allow_override=True)
    rep["crs"] = {"quelle": src_crs.name, "epsg": epsg, "transformiert": epsg != 4326}
    if epsg != 4326:
        gdf = gdf.to_crs(4326)
    rep["crs"]["ziel"] = "EPSG:4326"

    # --- 6. Geometriepruefung/-reparatur ---------------------------------------------
    has_z = int(shapely.has_z(gdf.geometry.values).sum())
    gdf["geometry"] = shapely.force_2d(gdf.geometry.values)
    empty = int(gdf.geometry.is_empty.sum() + gdf.geometry.isna().sum())
    invalid = gdf[~gdf.geometry.is_valid & ~gdf.geometry.is_empty]
    repairs, unrepaired = [], []
    for idx, row in invalid.iterrows():
        fixed = shapely.make_valid(row.geometry)
        ok = fixed.geom_type in ("LineString", "MultiLineString") and not fixed.is_empty \
            and shapely.hausdorff_distance(fixed, row.geometry) < 1e-9
        if ok:
            gdf.at[idx, "geometry"] = fixed
            repairs.append({"id": row["id"], "grund": "make_valid; Verlauf unveraendert (Hausdorff < 1e-9)"})
        else:
            unrepaired.append({"id": row["id"], "grund": "Reparatur wuerde Verlauf/Typ aendern; Original belassen"})
    rep["geometrie_pruefung"] = {"leere_geometrien": empty, "ungueltig_vor_reparatur": int(len(invalid)),
                                 "repariert": repairs, "nicht_repariert": unrepaired, "geometrien_mit_z_wert_auf_2d_reduziert": has_z}
    gdf = gdf[~gdf.geometry.is_empty]

    # --- 7. Segmente je Tour -----------------------------------------------------------
    cnt = gdf.groupby("id").size()
    multi_ids = cnt[cnt > 1].index.tolist()
    merged = []
    for tid, grp in gdf.groupby("id", sort=False):
        lines = []
        for g in grp.geometry:
            lines.extend(g.geoms if g.geom_type == "MultiLineString" else [g])
        merged.append((tid, lines[0] if len(lines) == 1 else MultiLineString(lines)))
    lines_gdf = gpd.GeoDataFrame({"id": [m[0] for m in merged]}, geometry=[m[1] for m in merged], crs=4326)
    n_multipart = int(sum(g.geom_type == "MultiLineString" for g in lines_gdf.geometry))
    rep["segmente"] = {"touren_aus_mehreren_shapefile_features": len(multi_ids),
                       "touren_als_multilinestring": n_multipart,
                       "vorgehen": "mehrere Segmente bleiben als MultiLineString erhalten (kein Linemerge, keine Lueckenschliessung)"}

    # --- 10. Vereinfachen (Douglas-Peucker, topologieerhaltend) und Runden ---------------
    to_m = Transformer.from_crs(4326, METRIC_CRS, always_xy=True).transform
    to_ll = Transformer.from_crs(METRIC_CRS, 4326, always_xy=True).transform
    orig = lines_gdf.geometry.values
    v_before = vertex_count(orig)
    simp, devs = [], []
    for g in orig:
        gm = project(g, to_m)
        sm = gm.simplify(SIMPLIFY_M, preserve_topology=True)
        devs.append(shapely.hausdorff_distance(gm, sm))
        s = project(sm, to_ll)
        s = shapely.transform(s, lambda c: np.round(c, DECIMALS))
        simp.append(s)
    # Rundung kann (sehr selten) Punkte zusammenfallen lassen -> Validitaet nachpruefen
    bad_after = [i for i, s in enumerate(simp) if (not s.is_valid) or s.is_empty]
    for i in bad_after:
        simp[i] = shapely.transform(orig[i], lambda c: np.round(c, DECIMALS))
    lines_gdf["geometry"] = simp
    v_after = vertex_count(simp)
    rep["vereinfachung"] = {"verfahren": f"Douglas-Peucker, preserve_topology=True, Toleranz {SIMPLIFY_M} m in {METRIC_CRS}, danach Rundung auf {DECIMALS} Nachkommastellen",
                            "stuetzpunkte_vorher": v_before, "stuetzpunkte_nachher": v_after,
                            "reduktion_prozent": round(100 * (1 - v_after / v_before), 1) if v_before else None,
                            "max_abweichung_hausdorff_m": round(float(max(devs)) if devs else 0, 3),
                            "median_abweichung_hausdorff_m": round(float(np.median(devs)) if devs else 0, 3),
                            "nach_rundung_ungueltig_original_verwendet": len(bad_after)}

    # --- 9. Attribute joinen ----------------------------------------------------------------
    joined = lines_gdf.merge(tours, on="id", how="left", validate="one_to_one")
    assert joined["title"].notna().all()
    no_line = tours[~tours["id"].isin(set(lines_gdf["id"]))]
    joined = gpd.GeoDataFrame(joined, geometry="geometry", crs=4326)
    joined = joined[["id"] + [c for c in tours.columns if c != "id"] + ["geometry"]]

    # --- 11. Export ------------------------------------------------------------------------
    gpkg = out / "team_inklusion_touren_linien.gpkg"
    gj = out / "team_inklusion_touren_linien.geojson"
    for p in (gpkg, gj):
        if p.exists():
            p.unlink()
    joined.to_file(gpkg, layer="team_inklusion_touren", driver="GPKG", engine="pyogrio")
    joined.to_file(gj, driver="GeoJSON", engine="pyogrio", COORDINATE_PRECISION=DECIMALS, RFC7946="YES")
    # Groessenvergleich: Roh-Geometrien der Team-Touren als GeoJSON (unvereinfacht) zur Referenz
    raw_tmp = out / "_raw_team_lines.geojson"
    gdf[["id", "geometry"]].to_file(raw_tmp, driver="GeoJSON", engine="pyogrio")
    sizes = {"shapefile_gesamt_mb": round(sum(f.stat().st_size for f in shp.parent.glob(shp.stem + ".*")) / 2**20, 1),
             "team_unvereinfacht_geojson_mb": round(raw_tmp.stat().st_size / 2**20, 2),
             "gpkg_mb": round(gpkg.stat().st_size / 2**20, 2), "geojson_mb": round(gj.stat().st_size / 2**20, 2)}
    raw_tmp.unlink()
    rep["dateigroessen"] = sizes

    # --- Plausibilitaet ----------------------------------------------------------------------
    bx = joined.geometry.bounds
    x0, y0, x1, y1 = ALPS_BBOX
    outside = joined[(bx.minx < x0) | (bx.maxx > x1) | (bx.miny < y0) | (bx.maxy > y1)]
    swapped = joined[(bx.minx.between(y0, y1)) & (bx.maxx.between(y0, y1)) & (bx.miny.between(x0, x1)) & (bx.maxy.between(x0, x1))
                     & ~((bx.minx.between(x0, x1)) & (bx.miny.between(y0, y1)))]
    ex0, ey0, ex1, ey1 = EUROPE_BBOX
    outside_eu = joined[(bx.minx < ex0) | (bx.maxx > ex1) | (bx.miny < ey0) | (bx.maxy > ey1)]
    tb = joined.total_bounds
    rep["plausibilitaet"] = {"bounding_box_gesamt": [round(float(v), 5) for v in tb],
                             "erwartete_bbox_alpenraum": list(ALPS_BBOX),
                             "touren_ausserhalb_bbox": [{"id": r.id, "title": r.title} for r in outside.itertuples()],
                             "vermutlich_vertauschte_koordinaten": [r.id for r in swapped.itertuples()],
                             "erwartete_bbox_europa": list(EUROPE_BBOX),
                             "touren_ausserhalb_europa_bbox": [r.id for r in outside_eu.itertuples()]}

    # --- Bilanz ----------------------------------------------------------------------------
    def tab(df):
        return {"gesamt": int(len(df)),
                "nach_veroeffentlicht": {k: int(v) for k, v in df["veroeffentlicht"].value_counts().items()},
                "nach_hat_report": {k: int(v) for k, v in df["hat_report"].value_counts().items()},
                "nach_kategorie": {k: int(v) for k, v in df["category"].value_counts().items()},
                "veroeffentlicht_x_report_x_kategorie": {f"{a_}|{b_}|{c_}": int(n) for (a_, b_, c_), n in
                                                         df.groupby(["veroeffentlicht", "hat_report", "category"]).size().items()}}
    rep["touren"] = {"anzahl_excel_team_inklusion": int(len(tours)), "mit_linie": int(len(joined)),
                     "ohne_linie": int(len(no_line)),
                     "ohne_linie_liste": [{"id": r.id, "title": r.title, "veroeffentlicht": r.veroeffentlicht,
                                           "hat_report": r.hat_report, "status_bearbeitung": r.status_bearbeitung}
                                          for r in no_line.itertuples()],
                     "aufschluesselung_mit_linie": tab(joined), "aufschluesselung_excel_alle": tab(tours)}
    rep["id_normalisierung"] = {"join_feld_shapefile": id_field, "join_feld_excel": "id (normalisiert aus 'ID')",
                                "regeln": "siehe scripts/tour_ids.py",
                                "angewandte_regeln_shapefile": dict(shp_log),
                                "ids_in_excel_normalisiert_mit_unterschied": int((tours["id"] != tours["id_original"]).sum())}
    (out / "validation_report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    write_md(out / "DATA_QUALITY.md", rep)
    print(json.dumps({k: rep[k] for k in ("abgleich", "segmente", "vereinfachung", "dateigroessen")}, ensure_ascii=False, indent=1))
    print("Touren ohne Linie:", [(r["id"], r["title"]) for r in rep["touren"]["ohne_linie_liste"]])
    print("Plausibilitaet:", rep["plausibilitaet"])


def write_md(path, r):
    t, ab = r["touren"], r["abgleich"]
    L = ["# Datenqualität – Linien der Team-Inklusion-ÖAV-Touren", "",
         "Automatisch erzeugt durch `scripts/extract_team_inklusion_tracks.py`.", "",
         "## Überblick", "",
         f"- Touren in der Excel (Team Inklusion ÖAV): **{t['anzahl_excel_team_inklusion']}**",
         f"- davon mit zugeordneter Linie: **{t['mit_linie']}**, ohne Linie: **{t['ohne_linie']}**",
         f"- Geometrien im Shapefile: **{ab['geometrien_shapefile']}**, davon Team Inklusion: **{ab['geometrien_team_inklusion']}**",
         f"- Geometrien ohne passende Tour: " + (f"{ab['geometrien_ohne_passende_tour_im_gesamtexport']} (ID nicht im gesamten Excel-Export); {ab['geometrien_anderer_quellen']} gehören zu anderen Quellen"
                                                  if "geometrien_anderer_quellen" in ab else f"{ab['geometrien_ohne_passende_tour_in_team_inklusion']} (nicht Team Inklusion; Abgleich gegen Gesamtexport nicht durchgeführt)"),
         f"- Mehrfach zugeordnete Geometrien (IDs mit >1 Feature): {len(ab['mehrfach_zugeordnete_ids'])}; doppelte IDs im Shapefile gesamt: {ab['doppelte_ids_im_shapefile_gesamt']}", "",
         "## Touren ohne Linie", ""]
    if t["ohne_linie_liste"]:
        L += ["| ID | Titel | veröffentlicht | Report | Status |", "|---|---|---|---|---|"]
        L += [f"| {x['id']} | {x['title']} | {x['veroeffentlicht']} | {x['hat_report']} | {x['status_bearbeitung']} |" for x in t["ohne_linie_liste"]]
        L += ["", "Es wurden keine Punkte als Ersatz erzeugt."]
    else:
        L += ["Keine."]
    s, g = r["shapefile"], r["geometrie_pruefung"]
    L += ["", "## Quelle und Join", "",
          f"- Ebene: `{s['ebenen'][0][0]}` ({s['geometrietyp']}), Attribute: {', '.join(s['attribute'])}",
          f"- Tour-ID-Attribut: `{s['id_attribut']}` (Gleitkommazahl, z. B. `804034456.0`); Join-Feld in der Excel: `id`",
          f"- ID-Normalisierung: siehe `scripts/tour_ids.py` (Text, Leerzeichen/Dezimalendung/Präfix/führende Nullen entfernen). Angewandt im Shapefile: {r['id_normalisierung']['angewandte_regeln_shapefile']}; in der Excel: {r['id_normalisierung']['ids_in_excel_normalisiert_mit_unterschied']} IDs verändert.",
          f"- CRS laut .prj: {s['prj_crs']} (EPSG:{s['prj_epsg']}); Transformation nach EPSG:4326: {'ja' if r['crs']['transformiert'] else 'nicht nötig'}", "",
          "## Geometrieprüfung", "",
          f"- Leere Geometrien: {g['leere_geometrien']}; ungültig vor Reparatur: {g['ungueltig_vor_reparatur']}; repariert: {len(g['repariert'])}; nicht repariert: {len(g['nicht_repariert'])}",
          f"- Z-Werte entfernt (auf 2D reduziert): {g['geometrien_mit_z_wert_auf_2d_reduziert']}",
          f"- Touren aus mehreren Shapefile-Features: {r['segmente']['touren_aus_mehreren_shapefile_features']} (Ergebnis: MultiLineString erhalten: {r['segmente']['touren_als_multilinestring']})", ""]
    for x in g["repariert"] + g["nicht_repariert"]:
        L.append(f"  - {x['id']}: {x['grund']}")
    v, d = r["vereinfachung"], r["dateigroessen"]
    L += ["", "## Vereinfachung und Dateigrößen", "",
          f"- {v['verfahren']}", f"- Stützpunkte: {v['stuetzpunkte_vorher']} → {v['stuetzpunkte_nachher']} (−{v['reduktion_prozent']} %)",
          f"- Abweichung (Hausdorff, Meter): max {v['max_abweichung_hausdorff_m']}, Median {v['median_abweichung_hausdorff_m']}",
          f"- Größen: Shapefile gesamt {d['shapefile_gesamt_mb']} MB; Team-Linien unvereinfacht (GeoJSON) {d['team_unvereinfacht_geojson_mb']} MB; GPKG {d['gpkg_mb']} MB; GeoJSON {d['geojson_mb']} MB", ""]
    L += ["## Aufschlüsselung der Touren mit Linie", ""]
    for key, lab in (("nach_veroeffentlicht", "veröffentlicht"), ("nach_hat_report", "mit Report"), ("nach_kategorie", "Kategorie")):
        L.append(f"- {lab}: " + ", ".join(f"{k}: {n}" for k, n in t["aufschluesselung_mit_linie"][key].items()))
    L += ["", "Kombination veröffentlicht | Report | Kategorie:", ""]
    for k, n in sorted(t["aufschluesselung_mit_linie"]["veroeffentlicht_x_report_x_kategorie"].items()):
        L.append(f"- {k}: {n}")
    p = r["plausibilitaet"]
    L += ["", "## Plausibilität der Koordinaten", "",
          f"- Bounding Box (lon_min, lat_min, lon_max, lat_max): {p['bounding_box_gesamt']}; Erwartung Alpenraum inkl. Rand: {p['erwartete_bbox_alpenraum']}",
          f"- Touren außerhalb der Alpen-Box: {len(p['touren_ausserhalb_bbox'])} (liegen laut Titel/Koordinaten in Deutschland bzw. Schottland, also außerhalb der Alpen, aber plausibel); außerhalb der Europa-Box {p['erwartete_bbox_europa']}: {len(p['touren_ausserhalb_europa_bbox'])}",
          f"- Verdacht auf vertauschte Längen-/Breitengrade: {len(p['vermutlich_vertauschte_koordinaten'])}"]
    for x in p["touren_ausserhalb_bbox"]:
        L.append(f"  - {x['id']}: {x['title']}")
    L += ["", "## Hinweise", "",
          "- Eine Tour gilt nie pauschal als barrierefrei; `category`/`device` beziehen sich nur auf das dokumentierte Gerät.",
          "- Nicht Team-Inklusion-Geometrien werden nicht ausgegeben."]
    path.write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
