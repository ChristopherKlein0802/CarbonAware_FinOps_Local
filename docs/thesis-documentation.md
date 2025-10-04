# Dokumentation Bachelorarbeit: Carbon-Aware FinOps Integration

## 1. Forschungsgrundlage
- **Forschungsfrage:** Wie lässt sich ein integriertes Monitoring-System entwickeln, das Kosten und CO₂-Emissionen von Cloud-Infrastrukturen simultan erfasst, und welche Vorteile bietet dieser Ansatz gegenüber bestehenden getrennten Lösungen?
- **Motivation:** Der deutsche Mittelstand benötigt kosteneffiziente Werkzeuge, die FinOps- und Nachhaltigkeitsanforderungen gleichzeitig adressieren und CSRD-konforme Emissionsdaten bereitstellen [7], [10], [11].

## 2. Literaturüberblick
### 2.1 Carbon Footprint in der Cloud
Die Konzepte der energy proportional computing und serverseitigen Leistungsmodelle bilden die Grundlage für das verwendete lineare Leistungs-Scaling [1], [2]. Aktuelle Analysen zum Energiebedarf von Rechenzentren erweitern diese Basis [3]. Emissionsintensitäten orientieren sich an Standards internationaler Organisationen (IEA, EPA) sowie dem Software Carbon Intensity Framework der Green Software Foundation [4]–[6].

### 2.2 FinOps und Kostenoptimierung
FinOps-Studien beleuchten Effekte von Right-Sizing, Lastverschiebung und Transparenzmaßnahmen [7]–[9]. Marktanalysen unterstreichen den Bedarf integrierter Werkzeuge für Unternehmen mit begrenztem Budget.

### 2.3 Regionaler und regulatorischer Kontext
Die Cloud-Adaption und Digitalisierung im deutschen Mittelstand sind umfangreich dokumentiert [10], [11], [19]. EU-Initiativen wie „Fit for 55“ verschärfen die Berichtspflichten [12]. Energiemarktstudien (Agora Energiewende, Fraunhofer ISE, BDEW) liefern regionale Parameter für das Modell [16]–[18].

### 2.4 CloudTrail für Umweltmetriken
CloudTrail wird bislang primär für Compliance genutzt [13]. Die Arbeit untersucht die Übertragbarkeit auf präzise Laufzeitmessung und stützt sich auf Leitfäden zu nachhaltiger Softwareentwicklung [14], [15], [20].

## 3. Methodisches Vorgehen (Design Science Research)
1. **Problemidentifikation:** Analyse vorhandener FinOps- und Carbon-Tools anhand eines Bewertungsrasters zur Ermittlung integrativer Defizite.
2. **Datenintegration:** ElectricityMaps (Carbon-Intensität), Boavizta (Hardwaremodelle), AWS Cost Explorer/Pricing (Kosten), CloudTrail (Laufzeit) und CloudWatch (CPU-Auslastung) werden über den `DataProcessor` gebündelt.
3. **No-Fallback-Policy:** API-Ausfälle werden transparent ausgewiesen; es existieren keine synthetischen Ersatzwerte.
4. **Berechnungsmodelle:** CO₂ = Leistung (kW) × Intensität (g/kWh) × Laufzeit (h) / 1000 [4], [6]; Leistungswerte basieren auf dem 30/70-Modell für Serverlast [1], [2]; Business-Faktoren stützen sich auf konservative Literaturwerte (15–25 % Kosten, 15–35 % CO₂) [7], [8], [15].
5. **Unsicherheiten:** Jede Dashboard-Antwort enthält Metadaten zu Quellen, Messintervallen und Unsicherheiten (±5 % Carbon, ±10 % Power, ±2 % Kosten, ±15 % Szenarien).

## 4. Ethische und akademische Aspekte
- **Datenschutz:** Es werden ausschließlich Infrastrukturmetriken verarbeitet.
- **Transparenz:** Quellcode, Konfiguration und reproduzierbare Skripte (Makefile, requirements-frozen.txt) ermöglichen Peer Review.
- **Limitationen:** Vier-Instanzen-Testbett; Validierung produktiver Workloads steht aus.

## 5. Regionaler Fokus: Deutsches Stromnetz
- **Carbon-Intensitäten:** 250–550 g CO₂/kWh für Deutschland [16], [17].
- **Zeitliche Schwankungen:** Solar- und Windspitzen (11:00–15:00 Uhr bzw. 02:00–05:00 Uhr); hohe Intensitäten abends [16], [17].
- **Kosten:** BDEW-Analysen unterstützen die Wirtschaftlichkeitsbewertung [18].

## 6. Validierungsstand
- **Testumgebung:** Vier AWS-Instanzen (t3.micro bis t3.large).
- **Kosten & Emissionen:** Aktuell nur Literatur-basierte Einsparpotenziale; empirische Bestätigung benötigt reale CloudTrail- und Cost-Explorer-Daten.
- **Genauigkeit:** Ohne vollständige CloudTrail-Daten bleibt der Validierungsfaktor theoriegeleitet.
- **Neue Kennzahlen:** Das Dashboard speichert stündliche Snapshots aus AWS Cost Explorer und ElectricityMaps und berechnet daraus Time Alignment Coverage (TAC) sowie Cost-MAPE für die Validierung gegen den Cost Explorer.

## 7. Offene Arbeiten
1. Regelmäßige Auswertung realer CloudTrail-Events.
2. Aufbau eines Messdatensatzes mit dokumentierter Versuchsdurchführung.
3. Erweiterung automatisierter Integrationstests für End-to-End-Szenarien.

## 8. Quellen
Alle Zitate verweisen auf das Literaturverzeichnis `docs/references.md`.
