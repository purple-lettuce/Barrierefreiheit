# Qualität: Barrierefreiheit und Tests (AP-13, AP-14)

Stand: 2026-11-20, Demo-Version.

## Automatisch geprüft
- Datenprüfung und Stufenlogik: `python -m unittest discover -s tests` (6 Tests, bestanden).
- Zählungen im Browser (Edge, headless, Chromium): Karte und Liste zeigen 85 (nur Report), 256 (alle veröffentlicht), 444 (mit Entwürfen); Filter Handbike = 40; Layer aus = keine Linien; Quellenseite lädt Datenstand.
- Kontraste der Linienfarben zum OSM-Hintergrund `#F2EFE9` nachgerechnet: R1 4,77, R2 4,52, R3 4,79, Handbike 5,41, Grau 5,65, Hellgrau 3,01 (alle ≥ 3 : 1, WCAG 1.4.11). Entwürfe: Deckkraft 0,8 ergibt mindestens 3,3 : 1. Textfarben auf Weiß: Fließtext 17,4 : 1, Links 7,75 : 1.
- Ladegröße: Startdatei der Karte 0,49 MB, Details 0,25 MB; „Alle Touren" lädt 1,17 MB nach, Entwürfe 1,52 MB.

## Umgesetzt für WCAG 2.1 AA
- Skip-Link, Sprache `de`, Seitentitel, Hauptnavigation mit `aria-current`.
- Sichtbarer Fokus (Gelb mit schwarzem Rand) für alle bedienbaren Elemente.
- Alle Filter sind native Formularelemente mit Beschriftung. Die Anzahl wird per `aria-live` angesagt.
- Farbe ist nie das einzige Merkmal: Strichart und Text im Popup ergänzen sie. Die Liste nennt Gerät und Stufe als Text.
- Liste als Alternative zur Karte, Tabelle mit sortierbaren Spaltenköpfen (`aria-sort`), Links mit Hinweis „öffnet in neuem Tab".
- Reduzierte Bewegung wird respektiert, die Seite ist ab 390 px Breite nutzbar (Karte oben, Bedienung unten).

## Bekannte Einschränkungen
- Die Linien auf der Karte sind nicht per Tastatur anwählbar. Die Liste ersetzt das und ist von der Karte aus verlinkt.
- Der Karten-Popup und die Leaflet-Bedienelemente wurden nicht mit einem Screenreader getestet.

## Manuell noch zu erledigen (nicht automatisierbar)
- [ ] Stichprobe mit Screenreader (NVDA oder VoiceOver) auf Karte, Liste und Erklärseite.
- [ ] Tastaturdurchlauf aller Seiten durch eine Person.
- [ ] Test auf Firefox, Safari, einem Android- und einem iOS-Gerät.
- [ ] Rechtsprüfung, ob das österreichische Umsetzungsgesetz zum European Accessibility Act für die Seite gilt.
- [ ] Ladezeit auf mobilem Netz messen.