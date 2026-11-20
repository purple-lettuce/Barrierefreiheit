import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import check_web_data  # noqa: E402
import web_rules  # noqa: E402


class WebData(unittest.TestCase):
    def test_zaehlungen_und_whitelist(self):
        fehler, _ = check_web_data.pruefe(ROOT / "web" / "data")
        self.assertEqual(fehler, [])


class Stufen(unittest.TestCase):
    def test_vollstaendig(self):
        self.assertEqual(web_rules.stufe("rollstuhl_r1", 0, "ja", "nein")[0], "vollständig")

    def test_teilweise(self):
        self.assertEqual(web_rules.stufe("rollstuhl_r3", 2, "nein", "ja")[0], "teilweise")

    def test_luecken(self):
        self.assertEqual(web_rules.stufe("rollstuhl_r3", 1, "ja", "nein")[0], "nicht eingestuft")
        self.assertEqual(web_rules.stufe("rollstuhl_r3", 0, "nein", "nein")[0], "nicht eingestuft")
        self.assertEqual(web_rules.stufe("rollstuhl_r3", 3, "ja", "ja")[0], "nicht eingestuft")

    def test_offen_und_handbike(self):
        self.assertEqual(web_rules.stufe("rollstuhl_r3", None, None, None)[0], "Bewertung offen")
        self.assertEqual(web_rules.stufe("handbike", 0, "ja", "nein")[0], "nicht eingestuft")

    def test_strichart(self):
        self.assertEqual(web_rules.hilfsperson_stil("nein", "nein"), "nein")
        self.assertEqual(web_rules.hilfsperson_stil("nein", "ja"), "ja")
        self.assertEqual(web_rules.hilfsperson_stil(None, None), "offen")


if __name__ == "__main__":
    unittest.main()