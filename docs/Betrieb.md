# Hosting, Domain, Rechtliches (AP-15, AP-16)

Status: **blockiert durch D6** (Verantwortliche/r tbd).

## Technik
- Die Website ist statisch (`web/`). Jedes Static Hosting genügt (z. B. GitHub Pages, Webspace). Es gibt keinen Server-Code.
- Die Seite braucht HTTPS. Die OSM-Kacheln erwarten einen Referer, deshalb keine `Referrer-Policy: no-referrer` setzen.
- OSM-Kachelnutzung: Der Tile-Server von OSM ist für kleine Nutzung gedacht (Richtlinie: https://operations.osmfoundation.org/policies/tiles/). Für den regulären Betrieb mit vielen Zugriffen einen eigenen Kachel-Anbieter wählen (D5 ist nur als Prototyp gedacht).
- Keine Tracker, keine Cookies, keine Drittanbieter-Skripte. Leaflet liegt lokal in `web/vendor/leaflet/`.

## Vor der Veröffentlichung
- [ ] D6 klären: Hosting, Domain, Verantwortliche/r.
- [ ] `web/impressum.html` und `web/datenschutz.html` ausfüllen (alle „tbd" entfernen) und rechtlich prüfen lassen.
- [ ] Lizenz der Tourdaten auf `web/quellen.html` ergänzen.
- [ ] Definition der Schlüsselstelle auf `web/erklaerung.html` aus dem Leitfaden übernehmen.
- [ ] Entscheiden, ob die Entwürfe in der öffentlichen Version zuschaltbar bleiben (nur für Demo gedacht).
- [ ] Leaflet-Lizenztext liegt bei (`vendor/leaflet/LICENSE`).