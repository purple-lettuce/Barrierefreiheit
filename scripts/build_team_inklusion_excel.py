"""Schritt 1: Excel-Uebersicht aller Team-Inklusion-OeAV-Touren (Quelle 806030126).

Aufruf:
  python scripts/build_team_inklusion_excel.py --routes av_routes_261020.xlsx \
      --reference "Auswertung_Barrierefreiheitslayer_Team_Inklusion_OEAV 1.xlsx" --out output
"""
import argparse
import html
import json
import re
import sys
from collections import Counter
from pathlib import Path

import openpyxl
import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tour_ids import normalize_id  # noqa: E402

SOURCE_ID = "806030126"
SOURCE_NAME = "Team Inklusion ÖAV"
# Erwartungswerte aus dem Auftrag (Stand 2026-11-20); dienen nur dem Abgleich, nicht als Filter
EXPECTED = {"gesamt": 703, "veroeffentlicht": 268, "nicht_veroeffentlicht": 435,
            "mit_report": 86, "ohne_report": 182}
EXPECTED_CAT = {"handbike": 40, "rollstuhl_r3": 32, "rollstuhl_unklar": 10,
                "rollstuhl_r1": 2, "rollstuhl_r2": 1, "sonstiges": 1}
CAT_LABEL = {
    "rollstuhl_r1": "Rollstuhl R1 / ohne Zusatzantrieb",
    "rollstuhl_r2": "Rollstuhl R2 / leichte Antriebshilfe",
    "rollstuhl_r3": "Rollstuhl R3 / starkes Zuggerät",
    "rollstuhl_unklar": "Rollstuhl, Gerät nicht bestimmbar",
    "handbike": "Handbike",
    "sonstiges": "Sonstiges Hilfsmittel",
    "nicht_klassifiziert": "Nicht klassifiziert (kein Report)",
}
GRUNDKLASSE = {"Wanderung": "Rollstuhl", "Radtour": "Handbike", "Radfahren": "Handbike",
               "Fernradweg": "Handbike", "Langlauf": "sonstiges Hilfsmittel"}

# Textfelder in Prioritaetsreihenfolge (DE). Ausruestung ist die verlaesslichste Quelle.
TEXT_FIELDS = [("Ausrüstung DE", "Ausrüstung"), ("Tipp des Autors DE", "Autorentipp"),
               ("Beschreibung DE", "Beschreibung"), ("Kurzbeschreibung DE", "Kurzbeschreibung"),
               ("Sicherheitshinweise DE", "Sicherheitshinweise"), ("Wegbeschreibung DE", "Wegbeschreibung")]

EXTRA_COLS = {  # Spalte im Export -> Ausgabespalte (nur Felder, die im Datensatz stehen)
    "Strecke berechnet (m)": "strecke_m",
    "Höhe aufsteigend berechnet": "aufstieg_hm",
    "Höhe absteigend berechnet": "abstieg_hm",
    "Dauer berechnet": "dauer_min",
    "Höchster Punkt berechnet": "hoechster_punkt_m",
    "Tiefster Punkt berechnet": "tiefster_punkt_m",
    "Kondition": "kondition_av",
    "Erlebniswert": "erlebniswert_av",
    "Landschaft": "landschaft_av",
    "Gefahrenpotential": "gefahrenpotential_av",
    "Rundtour": "rundtour",
    "Streckentour": "streckentour",
    "Etappentour": "etappentour",
    "kinderwagengerecht": "kinderwagengerecht_av",
    "barrierefrei": "flag_barrierefrei_av",
    "RouteTourIsInCountry": "land",
    "RouteTourIsInProvince": "region",
}
RE_TAG = re.compile(r"<[^>]+>")
RE_MAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
RE_URL = re.compile(r"https?://\S+|www\.\S+")
RE_PHONE = re.compile(r"(?:(?:tel(?:efon)?|handy|mobil|fon)\.?\s*:?\s*|(?<!\w)\+|(?<!\d)00)\d[\d /()-]{6,}\d", re.I)


def clean_text(v, limit=None):
    """HTML entfernen, Entities aufloesen, E-Mail/Telefon schwaerzen, kuerzen."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    s = RE_TAG.sub(" ", str(v).replace("<br>", " ").replace("<br/>", " "))
    s = html.unescape(s)
    s = RE_MAIL.sub("[E-Mail entfernt]", s)
    s = RE_PHONE.sub("[Telefon entfernt]", s)
    s = re.sub(r"\s+", " ", s).strip()
    if limit and len(s) > limit:
        s = s[:limit].rsplit(" ", 1)[0] + " …"
    return s


# ---------------------------------------------------------------- Klassifikation
RX = {
    "r3": re.compile(r"swiss[\s-]?tra(?:c|ck)k?|starke[sn]?\s+(?:rollstuhl-?)?zugger|zugger(?:ä|a)t\s+mit\s+starkem\s+antrieb", re.I),
    "zug": re.compile(r"zugger(?:ä|a)t|zugzugger|vorspann", re.I),
    "r2": re.compile(r"smoov|e-?\s?motion|leichte[nr]?\s+(?:antrieb|zugger)|(?:elektrische|elektrisch\w*)\s+antriebshilfe", re.I),
    "r2_weak": re.compile(r"begleit(?:person|ung)|schiebehilfe", re.I),
    "r1_enum": re.compile(r"(?:m(?:ö|o)glich|machbar|geeignet)\s+(?:mit|f(?:ü|u)r)\s+(?:einen?\s+)?(?:manuellen?\s+)?rollstuhl\s*,", re.I),
    "r1": re.compile(r"ohne\s+(?:extra\s+|zus(?:ä|a)tzlich\w*\s+|zusatz-?)?antrieb|ohne\s+zusatzantrieb|manuelle[rn]?\s+rollstuhl|handrollstuhl|aktivrollstuhl|free-?\s?wheel[^.]{0,80}nicht\s+(?:notwendig|erforderlich|n(?:ö|o)tig)|hilfsmittel[^.]{0,60}nicht\s+(?:notwendig|erforderlich|n(?:ö|o)tig)", re.I),
    "freewheel": re.compile(r"free-?\s?wheel", re.I),
}
RX_HANDBIKE = re.compile(
    r"praschberger\s+adaptiv\s?bike|adaptiv\s?handbike|adaptiv\s?bike|speedbike[\w\s]*|handbike|hand\s?cycle|handcycle|"
    r"rollstuhl[\s-]?bike|liegerad|tandem", re.I)
RX_SONST = re.compile(r"langlauf\s?schlitten|schlitten|sitzski|monoski|mobilit(?:ä|a)ts\s?hilfe", re.I)


def find_hit(texts, rx):
    """Erster Treffer ueber die Textfelder in Prioritaetsreihenfolge -> (feld, match-text)."""
    for label, txt in texts:
        m = rx.search(txt)
        if m:
            return label, m.group(0)
    return None, None


def classify(activity, texts):
    """texts: Liste (feldname, bereinigter Text). Rueckgabe: category, device, basis, confidence."""
    base = GRUNDKLASSE.get(activity)
    if base == "Handbike":
        f, g = find_hit(texts, RX_HANDBIKE)
        if g:
            dev = re.sub(r"\s+", " ", g).strip()
            return "handbike", dev[0].upper() + dev[1:], f"Aktivität {activity} → Handbike; Gerät aus Text ({f}): {g}", "eindeutig"
        return "handbike", "Handbike", f"Aktivität {activity} → Handbike; kein konkretes Modell genannt", "abgeleitet"
    if base == "sonstiges hilfsmittel":
        f, g = find_hit(texts, RX_SONST)
        if g:
            return "sonstiges", g[0].upper() + g[1:], f"Aktivität Langlauf; Gerät aus Text ({f}): {g}", "eindeutig"
        return "sonstiges", "", "Aktivität Langlauf; kein Gerät genannt", "unklar"
    if base == "Rollstuhl":
        # Feldweise: das erste Feld (Ausrüstung → Autorentipp → ...) mit Gerätenennung entscheidet.
        for k, (label, txt) in enumerate(texts):
            primary = k < 2  # Ausrüstung / Autorentipp: gezielte Geräteaussagen
            conf_ok = "eindeutig" if k == 0 else "abgeleitet"
            fw = bool(RX["freewheel"].search(txt))
            def hit(key):
                m = RX[key].search(txt)
                return m.group(0) if m else None
            if hit("r3"):
                return "rollstuhl_r3", "Swiss-Trac bzw. starkes Zuggerät", f"Textnennung ({label}): {hit('r3')}", conf_ok
            if hit("r1_enum"):
                return ("rollstuhl_r1", "Rollstuhl (Geräteliste, Rollstuhl ohne Antrieb genannt)",
                        f"Geräteliste beginnt mit einfachem Rollstuhl ({label}): {hit('r1_enum')}", "abgeleitet")
            if hit("zug"):
                return "rollstuhl_r3", "Zuggerät (Typ nicht genannt)", f"Zuggerät genannt ({label}): {hit('zug')}; Stärke nicht belegt", "abgeleitet"
            if hit("r2"):
                return "rollstuhl_r2", hit("r2"), f"Textnennung ({label}): {hit('r2')}", conf_ok
            if primary and hit("r2_weak"):
                return "rollstuhl_r2", "Begleitperson", f"Textnennung ({label}): {hit('r2_weak')}", conf_ok
            if hit("r1"):
                dev = "Rollstuhl ohne Zusatzantrieb" + (", FreeWheel genannt" if fw else "")
                return "rollstuhl_r1", dev, f"Textnennung ({label}): {hit('r1')}", conf_ok
        return "rollstuhl_unklar", "", "Aktivität Wanderung mit Report, aber keine belastbare Gerätenennung", "unklar"
    return "sonstiges", "", f"Aktivität '{activity}' nicht in Grundklassen-Zuordnung; nicht bestimmbar", "unklar"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--routes", required=True)
    ap.add_argument("--reference", default=None)
    ap.add_argument("--out", default="output")
    ap.add_argument("--source-id", default=SOURCE_ID)
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)

    # --- Einlesen (streamend; alles als Text) ---------------------------------
    wb = openpyxl.load_workbook(a.routes, read_only=True)
    ws = wb.worksheets[0]
    rows = ws.iter_rows(values_only=True)
    hdr = list(next(rows))
    names = [f"{h}__{i}" if hdr.count(h) > 1 else h for i, h in enumerate(hdr)]
    ix = {n: i for i, n in enumerate(names)}
    need = ["ID", "Quelle ID", "Quelle", "Aktivität", "Titel DE", "Report zur Barrierefeiheit",
            "Veröffentlicht am", "Bearbeitungsstand Status"]
    for n in need:
        assert n in ix, f"Spalte fehlt: {n}"
    src_log = Counter()
    n_total = 0
    sel = []
    for r in rows:
        n_total += 1
        sid = normalize_id(r[ix["Quelle ID"]], src_log)
        if sid == a.source_id:
            sel.append(r)
    wb.close()
    df = pd.DataFrame(sel, columns=names).astype(object).where(lambda d: d.notna(), None).copy()
    print(f"Zeilen im Export: {n_total}; Team Inklusion: {len(df)}")

    # Touren mit Status "Gelöscht" werden nicht benötigt und entfernt (Vorgabe des Auftraggebers)
    is_del = df["Bearbeitungsstand Status"] == "Gelöscht"
    has_d = df["Veröffentlicht am"].map(lambda v: isinstance(v, str) and v.strip() != "")
    has_r = df["Report zur Barrierefeiheit"].map(lambda v: isinstance(v, str) and v.strip() != "")
    deleted_stats = {"gesamt": int(is_del.sum()), "mit_datum": int((is_del & has_d).sum()),
                     "mit_report": int((is_del & has_r).sum()),
                     "mit_datum_und_report": int((is_del & has_d & has_r).sum()),
                     "ohne_datum_ohne_report": int((is_del & ~has_d & ~has_r).sum())}
    df = df[~is_del].copy()
    print(f"Gelöscht entfernt: {deleted_stats}; verbleibend: {len(df)}")

    # --- ID-Handling ----------------------------------------------------------
    id_log = Counter()
    df["id_original"] = df["ID"].map(lambda v: None if v is None else str(v))
    df["id"] = df["ID"].map(lambda v: normalize_id(v, id_log))
    missing_ids = int(df["id"].isna().sum())
    dup_ids = sorted(df.loc[df["id"].notna() & df["id"].duplicated(keep=False), "id"].unique())

    # --- Flags ---------------------------------------------------------------
    pub_date = df["Veröffentlicht am"].map(lambda v: None if v is None or str(v).strip() == "" else str(v).strip())
    df["hat_veroeffentlichungsdatum"] = pub_date.map(lambda v: "Ja" if isinstance(v, str) and v else "Nein")
    df["veroeffentlicht"] = df["hat_veroeffentlichungsdatum"]  # Ersatzregel, siehe Qualitaet
    rep_raw = df["Report zur Barrierefeiheit"].map(lambda v: None if v is None or str(v).strip() == "" else str(v).strip())
    df["hat_report"] = rep_raw.map(lambda v: "Ja" if isinstance(v, str) and v else "Nein")

    def parse_report(v):
        if not isinstance(v, str) or not v:
            return {}
        try:
            return json.loads(v)
        except ValueError:
            return {}
    rep = rep_raw.map(parse_report)
    unparsable_reports = int(((rep_raw.notna()) & (rep.map(len) == 0)).sum())
    for k, col in (("accessibleWithWalkingDisability", "report_gehbehinderung"),
                   ("accessibleWithHearingImpairment", "report_hoerbeeintraechtigung"),
                   ("accessibleWithVisualImpairment", "report_sehbeeintraechtigung"),
                   ("accessibleWithCognitiveDisability", "report_kognitive_beeintraechtigung")):
        df[col] = rep.map(lambda d, k=k: ("Ja" if d[k] else "Nein") if k in d else "")

    # --- Klassifikation --------------------------------------------------------
    cats, devs, basis, conf, lvl, gk = [], [], [], [], [], []
    for _, row in df.iterrows():
        act = row["Aktivität"]
        gk.append(GRUNDKLASSE.get(act, "") if row["hat_report"] == "Ja" or True else "")
        if row["hat_report"] != "Ja":
            cats.append("nicht_klassifiziert"); devs.append(""); conf.append("")
            basis.append("kein Report zur Barrierefreiheit; keine Einstufung"); lvl.append("nicht eingestuft")
            continue
        texts = [(lab, clean_text(row[col])) for col, lab in TEXT_FIELDS]
        c, d, b, cf = classify(act, texts)
        cats.append(c); devs.append(d); basis.append(b); conf.append(cf)
        lvl.append(f"nur bezogen auf dokumentiertes Gerät: {d}" if d else "Gerät nicht bestimmbar; keine Einstufung")
    df["category"] = cats
    df["category_label"] = [CAT_LABEL[c] for c in cats]
    df["device"] = devs
    df["classification_basis"] = basis
    df["classification_confidence"] = conf
    df["accessibility_level"] = lvl
    df["grundklasse_aus_aktivitaet"] = gk

    # --- Ausgabespalten ----------------------------------------------------------
    o = pd.DataFrame({
        "id": df["id"], "id_original": df["id_original"], "title": df["Titel DE"].map(clean_text),
        "activity": df["Aktivität"], "published_at": pub_date, "source": df["Quelle"],
        "source_id": df["Quelle ID"].map(lambda v: normalize_id(v)), "url": "",
        "status_bearbeitung": df["Bearbeitungsstand Status"],
        "hat_veroeffentlichungsdatum": df["hat_veroeffentlichungsdatum"],
        "veroeffentlicht": df["veroeffentlicht"], "hat_report": df["hat_report"],
        "grundklasse_aus_aktivitaet": df["grundklasse_aus_aktivitaet"],
        "category": df["category"], "category_label": df["category_label"], "device": df["device"],
        "accessibility_level": df["accessibility_level"],
        "classification_confidence": df["classification_confidence"],
        "classification_basis": df["classification_basis"],
        "equipment": df["Ausrüstung DE"].map(lambda v: clean_text(v, 400)),
    })
    for c in ("report_gehbehinderung", "report_hoerbeeintraechtigung", "report_sehbeeintraechtigung",
              "report_kognitive_beeintraechtigung"):
        o[c] = df[c]
    for src, dst in EXTRA_COLS.items():
        o[dst] = df[src]
    for dst in ("strecke_m",):
        o[dst] = pd.to_numeric(o[dst], errors="coerce").round(0)
    for dst in ("aufstieg_hm", "abstieg_hm", "dauer_min", "hoechster_punkt_m", "tiefster_punkt_m",
                "kondition_av", "erlebniswert_av", "landschaft_av", "gefahrenpotential_av"):
        o[dst] = pd.to_numeric(o[dst], errors="coerce")
    o["kurzbeschreibung"] = df["Kurzbeschreibung DE"].map(lambda v: clean_text(v, 300))
    o = o.sort_values(["veroeffentlicht", "id"], ascending=[False, True]).reset_index(drop=True)

    # --- Referenzvergleich (pro Tour, per ID) -----------------------------------
    cmp_rows = []
    if a.reference and Path(a.reference).exists():
        ref = pd.read_excel(a.reference, sheet_name="Touren im Layer", dtype=str)
        ref["id"] = ref["ID"].map(lambda v: normalize_id(v))
        refmap = {"Handbike": "handbike", "Rollstuhl R3 / starkes Zuggerät": "rollstuhl_r3",
                  "Rollstuhl / Gerät nicht bestimmbar": "rollstuhl_unklar",
                  "Rollstuhl R1 / ohne Zusatzantrieb": "rollstuhl_r1",
                  "Rollstuhl R2 / leichte Antriebshilfe": "rollstuhl_r2", "Sonstiges Hilfsmittel": "sonstiges"}
        ref["ref_cat"] = ref["Kategorie"].map(refmap)
        m = o.merge(ref[["id", "ref_cat", "Gerät/Hilfsmittel"]], on="id", how="outer", indicator=True)
        diff = m[(m["_merge"] != "both") | (m["category"] != m["ref_cat"])]
        diff = diff[~((diff["_merge"] == "left_only") & (diff["category"] == "nicht_klassifiziert"))]
        for _, r in diff.iterrows():
            cmp_rows.append([r["id"], r["title"], r["activity"], r["category"], r["ref_cat"], r["_merge"], r["classification_basis"]])

    write_workbook(o, out / "team_inklusion_touren_alle.xlsx", dict(
        n_total=n_total, src_log=src_log, id_log=id_log, missing_ids=missing_ids, dup_ids=dup_ids,
        unparsable_reports=unparsable_reports, deleted=deleted_stats, cmp_rows=cmp_rows, ref_used=bool(a.reference), args=a))
    print("fertig")


def autosize(ws, widths=None, maxw=60):
    for i, col in enumerate(ws.columns, 1):
        w = max((len(str(c.value)) for c in list(col)[:300] if c.value is not None), default=8)
        ws.column_dimensions[get_column_letter(i)].width = min(max(w + 2, 10), maxw)


def put_table(ws, rows, header=True):
    for r in rows:
        ws.append(r)
    if header:
        for c in ws[1]:
            c.font = Font(bold=True, color="FFFFFF"); c.fill = PatternFill("solid", fgColor="2F5D50")
    autosize(ws)
    ws.freeze_panes = "A2"


def write_workbook(o, path, info):
    wb = openpyxl.Workbook()
    ws = wb.active; ws.title = "Alle Touren"
    ws.append(list(o.columns))
    for rec in o.itertuples(index=False):
        ws.append([None if (isinstance(v, float) and pd.isna(v)) or v == "" else v for v in rec])
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF"); c.fill = PatternFill("solid", fgColor="2F5D50")
        c.alignment = Alignment(wrap_text=True, vertical="top")
    autosize(ws, maxw=50)
    ws.freeze_panes = "C2"
    ws.auto_filter.ref = ws.dimensions
    # IDs als Text beibehalten
    for col in ("id", "id_original", "source_id"):
        j = list(o.columns).index(col) + 1
        for row in ws.iter_rows(min_row=2, min_col=j, max_col=j):
            row[0].number_format = "@"

    pub = o[o.veroeffentlicht == "Ja"]; unp = o[o.veroeffentlicht == "Nein"]
    rep = o[o.hat_report == "Ja"]
    n = dict(gesamt=len(o), veroeffentlicht=len(pub), nicht_veroeffentlicht=len(unp),
             mit_report=int(((o.veroeffentlicht == "Ja") & (o.hat_report == "Ja")).sum()),
             ohne_report=int(((o.veroeffentlicht == "Ja") & (o.hat_report == "Nein")).sum()))
    fb = wb.create_sheet("Filterbilanz")
    rows = [["Filterstufe", "Anzahl"],
            ["Alle Touren Team Inklusion ÖAV (Quellen-ID 806030126)", n["gesamt"]],
            ["davon veröffentlicht", n["veroeffentlicht"]],
            ["davon nicht veröffentlicht", n["nicht_veroeffentlicht"]],
            ["veröffentlicht mit Report zur Barrierefreiheit", n["mit_report"]],
            ["veröffentlicht ohne Report", n["ohne_report"]],
            ["Report vorhanden, aber nicht veröffentlicht", int(((o.veroeffentlicht == "Nein") & (o.hat_report == "Ja")).sum())],
            ["Report vorhanden gesamt", len(rep)],
            [], ["Kategorie (alle Touren)", "Anzahl", "davon veröffentlicht"]]
    for c in list(CAT_LABEL):
        rows.append([f"{c}  ({CAT_LABEL[c]})", int((o.category == c).sum()), int(((o.category == c) & (o.veroeffentlicht == "Ja")).sum())])
    rows += [[], ["Kategorie (veröffentlicht + Report)", "Anzahl"]]
    vr = o[(o.veroeffentlicht == "Ja") & (o.hat_report == "Ja")]
    for c, k in vr.category.value_counts().items():
        rows.append([f"{c}  ({CAT_LABEL[c]})", int(k)])
    rows += [[], ["Gerät (Touren mit Report, alle)", "Anzahl"]]
    for d, k in rep.device.replace("", "(nicht bestimmbar)").value_counts().items():
        rows.append([d, int(k)])
    rows += [[], ["Konfidenz (Touren mit Report)", "Anzahl"]]
    for d, k in rep.classification_confidence.value_counts().items():
        rows.append([d, int(k)])
    rows += [[], ["Aktivität (alle Touren)", "Anzahl"]]
    for d, k in o.activity.value_counts().items():
        rows.append([d, int(k)])
    put_table(fb, rows); fb.freeze_panes = "A2"

    ab = wb.create_sheet("Abweichungen")
    DEL_REASON = {
        "gesamt": lambda d: f"{d['gesamt']} Touren mit Status 'Gelöscht' wurden auf Vorgabe entfernt",
        "veroeffentlicht": lambda d: f"{d['mit_datum']} gelöschte Touren hatten ein Veröffentlichungsdatum und wurden entfernt",
        "nicht_veroeffentlicht": lambda d: f"{d['gesamt'] - d['mit_datum']} gelöschte Touren ohne Datum wurden entfernt",
        "mit_report": lambda d: f"{d['mit_datum_und_report']} gelöschte Tour(en) mit Datum und Report entfernt",
        "ohne_report": lambda d: f"{d['mit_datum'] - d['mit_datum_und_report']} gelöschte Touren mit Datum, ohne Report entfernt",
    }
    exp_vs = [["Kennzahl", "erwartet", "gefunden", "Abweichung", "Begründung"]]
    for k, label in (("gesamt", "Touren gesamt"), ("veroeffentlicht", "veröffentlicht"),
                     ("nicht_veroeffentlicht", "nicht veröffentlicht"),
                     ("mit_report", "veröffentlicht mit Report"), ("ohne_report", "veröffentlicht ohne Report")):
        ok = n[k] == EXPECTED[k]
        exp_vs.append([label, EXPECTED[k], n[k], n[k] - EXPECTED[k], "keine Abweichung" if ok else DEL_REASON[k](info["deleted"])])
    vc = vr.category.value_counts()
    for c, e in EXPECTED_CAT.items():
        g = int(vc.get(c, 0))
        exp_vs.append([f"Kategorie {c} (86 veröff. Touren mit Report)", e, g, g - e,
                       "keine Abweichung" if g == e else f"Differenz durch entfernte gelöschte Tour(en) mit Report ({info['deleted']['mit_report']}); Einzelvergleich siehe unten"])
    exp_vs.append([])
    exp_vs.append(["Einzelvergleich mit Referenz-Excel (pro ID); nur abweichende Touren", "", "", "", ""])
    exp_vs.append(["id", "title", "activity", "category_neu", "category_referenz / Status", "merge", "classification_basis"])
    if not info["ref_used"]:
        exp_vs.append(["Referenzdatei nicht angegeben"])
    for r in info["cmp_rows"]:
        exp_vs.append(r)
    put_table(ab, exp_vs, header=True); ab.freeze_panes = None

    q = wb.create_sheet("Qualität")
    st = o.status_bearbeitung.fillna("(leer)")
    xt = pd.crosstab(st, o.hat_veroeffentlichungsdatum)
    rows = [["Prüfpunkt", "Wert"],
            ["Zeilen im Exportblatt (ohne Kopfzeile)", info["n_total"]],
            ["Zeilen Team Inklusion nach Entfernen gelöschter Touren", len(o)],
            ["Entfernt: Touren mit Status 'Gelöscht' (Gesamt / mit Datum / mit Report)", f"{info['deleted']['gesamt']} / {info['deleted']['mit_datum']} / {info['deleted']['mit_report']}"],
            ["Fehlende IDs", info["missing_ids"]],
            ["Doppelte IDs", len(info["dup_ids"])],
            ["IDs doppelt (Liste)", ", ".join(info["dup_ids"])],
            ["Normalisierung Tour-IDs (Regel: Anzahl)", "; ".join(f"{k}: {v}" for k, v in info["id_log"].items()) or "keine Änderung nötig (alle IDs bereits reine Ziffernfolgen ohne führende Nullen)"],
            ["Normalisierung Quellen-ID im Gesamtexport", "; ".join(f"{k}: {v}" for k, v in info["src_log"].items()) or "keine Änderung nötig"],
            ["Berichte mit nicht lesbarem JSON", info["unparsable_reports"]],
            [],
            ["Statusregel veröffentlicht", "Ersatzregel: 'Veröffentlicht am' enthält ein Datum → veröffentlicht."],
            ["Begründung", f"Das Feld 'Bearbeitungsstand Status' ist nicht verlässlich: nur {int((o.status_bearbeitung == 'Veröffentlicht').sum())} Touren haben Status 'Veröffentlicht', {len(pub)} haben ein Veröffentlichungsdatum (siehe Kreuztabelle)."],
            [], ["Status × Veröffentlichungsdatum", "Nein (kein Datum)", "Ja (Datum)"]]
    for s_, r_ in xt.iterrows():
        rows.append([s_, int(r_.get("Nein", 0)), int(r_.get("Ja", 0))])
    rows += [[], ["Unklare Klassifikationen (Touren mit Report, confidence = unklar)", "Anzahl"],
             ["", int((o.classification_confidence == "unklar").sum())],
             ["id", "title", "activity", "category", "classification_basis"]]
    for r_ in o[o.classification_confidence == "unklar"].itertuples():
        rows.append([r_.id, r_.title, r_.activity, r_.category, r_.classification_basis])
    rows += [[], ["Touren mit Report, aber Gehbehinderung = Nein", ""],
             ["", ", ".join(o[(o.hat_report == "Ja") & (o.report_gehbehinderung == "Nein")].id)],
             [], ["Aktivität ohne Grundklasse (Report vorhanden)", ""],
             ["", ", ".join(f"{r.id} ({r.activity})" for r in o[(o.hat_report == "Ja") & (o.grundklasse_aus_aktivitaet == "")].itertuples())],
             [], ["Verwendete Spalten (Export)", ", ".join(["ID", "Quelle ID", "Quelle", "Aktivität", "Titel DE", "Report zur Barrierefeiheit (Spaltenname im Export mit Tippfehler 'Barrierefeiheit')", "Veröffentlicht am", "Bearbeitungsstand Status", "Ausrüstung DE", "Tipp des Autors DE", "Beschreibung DE", "Kurzbeschreibung DE", "Sicherheitshinweise DE", "Wegbeschreibung DE"] + list(EXTRA_COLS))],
             ["Nicht übernommen (Datenschutz)", "Autor Vorname/Nachname/ID, Freitext Autor, Bemerkung Intern, Erbauer/Unterhalt, Autorentipp-Volltext, E-Mail/Telefon aus Texten geschwärzt"],
             ["url", "leer: 'OA Tourenlink' ist für alle Touren leer; ein Link ohne Slug lässt sich offline nicht verlässlich ableiten."],
             ["accessibility_level", "Annahme: gerätebezogene Kurzaussage ('nur bezogen auf dokumentiertes Gerät: …'), keine pauschale Barrierefreiheit."],
             ["flag_barrierefrei_av", "Selbstangabe im Export (Merkmal 'barrierefrei'), kein Nachweis; nicht als Einstufung verwenden."],
             ["kondition_av / erlebniswert_av / landschaft_av", "Roh-Bewertungen aus dem Export (Skala/0-Bedeutung unbekannt); 'Technik' (Schwierigkeit) ist für alle Touren leer."],
             ["Klassifikation", "Regelbasiert aus DE-Texten (Ausrüstung → Autorentipp → Beschreibung → Kurzbeschreibung → Sicherheit → Wegbeschreibung); Priorität R3 > Zuggerät generisch (R3, abgeleitet) > R2 > R1."],
             ["Report-Inhalt", "Der Report enthält im Export nur vier Ja/Nein-Merkmale (Geh-, Hör-, Seh-, kognitive Beeinträchtigung) als JSON; keine Schwierigkeits-/Wegbeschaffenheitsfelder."]]
    put_table(q, rows); q.freeze_panes = None
    for r in q.iter_rows():
        for c in r:
            c.alignment = Alignment(wrap_text=True, vertical="top")
    q.column_dimensions["A"].width = 55; q.column_dimensions["B"].width = 90
    wb.save(path)


if __name__ == "__main__":
    main()



