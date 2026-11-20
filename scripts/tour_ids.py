"""Gemeinsame ID-Normalisierung fuer Excel (Schritt 1) und Shapefile (Schritt 2).

Regeln (in dieser Reihenfolge):
  1. Wert als Text lesen; float-Werte aus dem Shapefile (z. B. 804034456.0) ganzzahlig formatieren.
  2. Leerzeichen (auch NBSP/Zero-Width) entfernen.
  3. Dezimalendung ".0"/",0" (beliebig viele Nullen) entfernen.
  4. Nichtnumerische Praefixe (z. B. "tour-", "id:", "#") entfernen.
  5. Fuehrende Nullen entfernen.
Jede angewandte Regel wird in einem Counter protokolliert.
"""
import math
import re
from collections import Counter

_SPACES = re.compile("[\\s" + chr(0xA0) + chr(0x200B) + chr(0xFEFF) + "]+")
_DECIMAL = re.compile(r"[.,]0+$")
_PREFIX = re.compile(r"^[^\d]+")


def normalize_id(value, log=None):
    """Gibt die normalisierte ID (Text) oder None zurueck; zaehlt angewandte Regeln in `log`."""
    log = log if log is not None else Counter()
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    if isinstance(value, float):
        if value.is_integer():
            s = str(int(value))
            log["float_zu_int"] += 1
        else:
            s = repr(value)
    else:
        s = str(value)
    for pattern, key in (
        (_SPACES, "leerzeichen_entfernt"),
        (_DECIMAL, "dezimalendung_entfernt"),
        (_PREFIX, "praefix_entfernt"),
    ):
        t = pattern.sub("", s)
        if t != s:
            log[key] += 1
        s = t
    t = s.lstrip("0")
    if t != s:
        log["fuehrende_nullen_entfernt"] += 1
    return t or None
