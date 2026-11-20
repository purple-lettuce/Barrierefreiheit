# Aktualisierungsablauf (AP-17)

Verantwortliche Person: **tbd (D7)**. Meldeweg für neue Touren laut Checkliste VIII: barrierefreiewege@jugend.alpenverein.at.

1. Rohdaten aus alpenvereinaktiv beziehen (Excel-Export und Shapefile, siehe `README.md`).
2. `python scripts/build_team_inklusion_excel.py ...` und `python scripts/extract_team_inklusion_tracks.py ...` (Befehle im README).
3. `data/bewertung.csv` ergänzen: neue Touren mit Report erhalten eine Zeile (Status `offen`), vom Team Inklusion gelieferte Werte eintragen (Status `erfasst`).
4. `python scripts/build_web_export.py` – erzeugt `web/data/` und startet die Datenprüfung.
5. Bei Fehlermeldung der Prüfung: Ursache klären. Haben sich die Zählungen bewusst geändert, die Erwartungswerte in `scripts/check_web_data.py` anpassen.
6. `python -m unittest discover -s tests`.
7. Lokal ansehen: `python -m http.server 8765 --directory web`, dann http://localhost:8765.
8. Ordner `web/` auf das Hosting kopieren (AP-15).