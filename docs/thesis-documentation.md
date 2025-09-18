# Bachelor Thesis Documentation: Carbon-Aware FinOps Integration

## 1. Research Foundation
- **Research question:** Wie kann ein integriertes Carbon-aware FinOps Tool durch die Kombination von Echtzeit-Stromnetz-Daten sowohl Kosten als auch CO2-Emissionen optimieren – im Vergleich zu separaten Tools?
- **Motivation:** Der deutsche Mittelstand benötigt kostengünstige Lösungen, die FinOps und Nachhaltigkeitsanforderungen kombinieren [7], [10], [11].

## 2. Literature Review
### 2.1 Cloud Carbon Footprint
Energy-proportional computing und serverseitige Leistungsmodelle bilden die Grundlage für das angewandte lineare Power-Scaling [1], [2], ergänzt durch aktuelle Abschätzungen des globalen Energiebedarfs von Rechenzentren [3]. Emissionsintensitäten folgen internationalen Standards der IEA und EPA sowie dem Software Carbon Intensity Framework der Green Software Foundation [4]–[6].

### 2.2 FinOps und Kostenoptimierung
FinOps-Studien beschreiben die betriebswirtschaftlichen Effekte von Right-Sizing, Scheduling und Transparenzmaßnahmen [7]–[9]. Marktberichte unterstreichen die Bedeutung integrierter Steuerungstools für Unternehmen mit begrenzten Budgets.

### 2.3 Regionaler und regulatorischer Kontext
Cloud-Adoption und Digitalisierungsdruck im deutschen Mittelstand sind gut dokumentiert [10], [11], [19]. Der EU Green Deal und Fit-for-55 verschärfen die Berichtspflichten für Emissionen [12]. Energiemarktstudien für Deutschland (Agora Energiewende, Fraunhofer ISE, BDEW) liefern die erforderlichen regionalen Parameter [16]–[18].

### 2.4 CloudTrail als Quelle für Umweltmetriken
CloudTrail dient bislang vor allem Compliance- und Sicherheitszwecken [13]. Die Arbeit untersucht dessen Eignung zur präzisen Laufzeitmessung und stützt sich auf Leitfäden zu nachhaltiger Softwareentwicklung [14], [15], [20].

## 3. Methodological Approach
1. **Datenintegration:** Kombination aus ElectricityMaps (Carbon-Intensität), Boavizta (Hardwaremodelle), AWS Cost Explorer/Pricing (Kosten), CloudTrail (Laufzeit) und CloudWatch (CPU-Auslastung).
2. **No-Fallback-Policy:** Fehlende API-Daten werden nicht geschätzt. Das Dashboard kennzeichnet Ausfälle transparent. Dies wahrt Nachvollziehbarkeit bei begrenzter Datenlage.
3. **Berechnungsmodelle:** Emissionen folgen dem Standard CO₂ = Leistung (kW) × Intensität (g/kWh) × Laufzeit (h) / 1000 [4], [6]. Leistungswerte resultieren aus dem 30/70-Modell für Idle- und Lastanteile [1], [2]. Kosten- und Einsparpotenziale orientieren sich an konservativen Literaturwerten (15–25 % Kosten, 15–35 % CO₂) [7], [8], [15].
4. **Unsicherheiten:** Jede Dashboard-Antwort trägt Metadaten zu Datenquellen und zu erwartenden Fehlerintervallen. Für Primär-APIs gelten ±5 % (Carbon), ±10 % (Power), ±2 % (Kosten), für Szenarioannahmen ±15 %.

## 4. Ethical and Academic Considerations
- **Datenschutz:** Es werden ausschließlich Infrastrukturmetriken verarbeitet; personenbezogene Daten fallen nicht an.
- **Transparenz:** Der Quellcode, Konfigurationsdateien und reproduzierbare Skripte (Makefile, requirements-frozen.txt) ermöglichen Peer Review und Replikation.
- **Limitationen:** Der aktuelle Prototyp basiert auf einem Vier-Instanzen-Testbett und illustriert Machbarkeit. Validierung mit produktiven Workloads steht aus.

## 5. Regional Focus: German Electricity Grid
- **Carbon-Intensitäten:** 250–550 g CO₂/kWh für Deutschland laut Agora Energiewende und Fraunhofer ISE [16], [17].
- **Zeitliche Schwankungen:** Solar- und Windspitzen definieren Zeitfenster für Lastverlagerungen (11:00–15:00 Uhr bzw. 02:00–05:00 Uhr). Hohe Intensitäten treten häufig zwischen 18:00 und 21:00 Uhr auf [16], [17].
- **Kostenrahmen:** BDEW-Analysen informieren die Wirtschaftlichkeitsbewertung [18].

## 6. Validation Summary
- **Testumgebung:** Vier EC2-Instanzen (t3.micro bis t3.large) zur Reproduktion typischer SME-Workloads.
- **Kosten und Emissionen:** Aktuelle Ergebnisse zeigen rund 20 % theoretisches Einsparpotenzial bei Kosten sowie 15–22 % bei Emissionen unter Literaturannahmen. Empirische Bestätigung erfordert reale CloudTrail- und Cost-Explorer-Daten.
- **Genauigkeit:** Ohne aktive CloudTrail-Integration liefert der Prototyp derzeit keine Laufzeitwerte; der Validierungsfaktor basiert damit noch auf Literaturannahmen.

## 7. Outstanding Work
1. Aktivierung und Auswertung realer CloudTrail-Events zur Bestimmung von Laufzeiten.
2. Ergänzung eines Datensatzes mit realen Messwerten inklusive Versuchsbeschreibung.
3. Aufbau automatisierter Integrationstests zur Absicherung end-to-end orientierter Szenarien.

## 8. References
Die vollständigen Literaturangaben befinden sich in `docs/references.md`. Alle Zitate referenzieren das dort verwendete Nummerierungsschema.
