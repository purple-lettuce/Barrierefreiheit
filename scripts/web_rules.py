"""Regeln fuer die Website (AP-01): Kategorien, Farben, Stufen nach Leitfaden (Entscheidung D1).

Siehe docs/Regelkarte.md und output/Abweichung_Leitfaden_Checkliste.md.
"""

# Whitelist der Kategorien (AP-05) mit Farbe (Roadmap Abschnitt 3)
KATEGORIEN = {
    "rollstuhl_r1": {"label": "R1 – ohne Antrieb", "farbe": "#00785A"},
    "rollstuhl_r2": {"label": "R2 – leichte Antriebshilfe", "farbe": "#0072B2"},
    "rollstuhl_r3": {"label": "R3 – starke Antriebshilfe", "farbe": "#B34700"},
    "handbike": {"label": "Handbike", "farbe": "#9C3D7E"},
    "rollstuhl_unklar": {"label": "Gerät unklar", "farbe": "#5E5E5E"},
    "sonstiges": {"label": "Sonstiges", "farbe": "#5E5E5E"},
    "nicht_klassifiziert": {"label": "Nicht klassifiziert", "farbe": "#E0A800"},
}

JA_NEIN = {"ja", "nein"}

STUFE_VOLLSTAENDIG = "vollständig"
STUFE_TEILWEISE = "teilweise"
STUFE_OFFEN = "Bewertung offen"
STUFE_NICHT_EINGESTUFT = "nicht eingestuft"


def hilfsperson_stil(hilfsperson, geuebt):
    """'ja' = gestrichelt (Hilfsperson und/oder nur fuer Geuebte), 'nein' = durchgezogen, 'offen' = Angabe fehlt."""
    if hilfsperson == "ja" or geuebt == "ja":
        return "ja"
    if hilfsperson == "nein" and geuebt == "nein":
        return "nein"
    return "offen"


def stufe(category, schluesselstellen, wc, hilfsperson):
    """Stufe nach Leitfaden. Rueckgabe: (Stufe, Begruendung).

    vollstaendig: keine Schluesselstelle und mind. 1 barrierefreies WC.
    teilweise:    hoechstens 2 Schluesselstellen und aktive Hilfsperson erforderlich.
    Alle anderen Faelle sind im Leitfaden nicht geregelt -> "nicht eingestuft".
    """
    if category == "handbike":
        return STUFE_NICHT_EINGESTUFT, "Für Handbike gibt es keine Stufenkriterien (offen, siehe Regelkarte)."
    if category == "nicht_klassifiziert":
        return STUFE_NICHT_EINGESTUFT, "Kein Report zur Barrierefreiheit."
    if schluesselstellen is None or wc not in JA_NEIN or hilfsperson not in JA_NEIN:
        return STUFE_OFFEN, "Schlüsselstellen, WC und Hilfsperson sind noch nicht erfasst."
    if schluesselstellen == 0 and wc == "ja":
        return STUFE_VOLLSTAENDIG, "Keine Schlüsselstelle und barrierefreies WC vorhanden."
    if schluesselstellen <= 2 and hilfsperson == "ja":
        return STUFE_TEILWEISE, "Höchstens 2 Schlüsselstellen, aktive Hilfsperson erforderlich."
    return STUFE_NICHT_EINGESTUFT, "Kriterien von vollständig und teilweise nicht erfüllt (Lücke im Leitfaden)."