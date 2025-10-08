# Literaturintegration: Carbon-Aware FinOps

## 1. Überblick
Das Dokument bündelt die wichtigsten Literaturstränge und ordnet sie den Implementierungsentscheidungen des Prototyps zu. Die Quellenangaben verweisen auf `docs/references.md`.

## 2. Cloud-Kostenoptimierung
- **AWS Well-Architected Framework:** Empfiehlt Right-Sizing, Workload-Scheduling und präzises Monitoring. Daraus leitet sich die Erfassung von AWS Pricing, Cost Explorer, CloudTrail und CloudWatch ab [7], [8], [13].
- **Branchenstudien (McKinsey, Deloitte):** Quantifizieren Einsparpotenziale von 15–25 % und betonen organisatorische Voraussetzungen für FinOps. Die Business-Case-Berechnungen nutzen konservative Faktoren aus diesen Studien [7], [9].
- **Gartner Marktanalysen:** Identifizieren eine fragmentierte Werkzeuglandschaft und begründen das integrierte Vorgehen für KMU [8].

## 3. Carbon Accounting und Energiemodelle
- **Energy-Proportional Computing:** Liefert das 30/70-Leistungsmodell, das in `calculate_simple_power_consumption` umgesetzt ist [1], [2], [3].
- **Emissionsstandards (IEA, EPA, GSF):** Dienen als Grundlage für die Umrechnung von Leistungsaufnahme und Netzintensität in CO₂-Äquivalente [4]–[6].
- **Carbon-aware Scheduling (MIT, Microsoft, Google):** Belegt den Nutzen zeitlicher Lastverschiebung und motiviert entsprechende Dashboardszenarien [14], [15], [20].

## 4. Regionaler und regulatorischer Kontext
- **Energiemarktberichte (Agora Energiewende, Fraunhofer ISE, BDEW):** Beschreiben die deutsche Netzcharakteristik und unterstützen die Lokalisierung der ElectricityMaps-Daten [16]–[18].
- **EU-Politik und KMU-Digitalisierung:** Dokumente wie „Fit for 55“ sowie Studien zur Digitalisierungsreife liefern den regulatorischen Rahmen und begründen den KMU-Fokus [11], [12], [19].

## 5. Monitoring und Laufzeitmessung
- **AWS CloudTrail:** Begründet den Audit-Ansatz für Laufzeiten, weist aber auf Konfigurations- und Aufbewahrungsanforderungen hin [13].
- **Standards zur Infrastrukturüberwachung:** Ergänzende Leitlinien (z. B. NIST-nahe Ansätze) stützen die Kombination von CloudTrail und CloudWatch zur Verifikation [20].

## 6. Ableitung für den Prototyp
- Die Verknüpfung von fünf APIs setzt die Literaturforderung nach integrierten, aktuellen Daten für Kosten und Carbon um.
- Dokumentierte Unsicherheitsintervalle spiegeln wissenschaftliche Vorsicht wider, solange empirische Validierung aussteht.
- Architektur und Dokumentation verbinden akademische Nachvollziehbarkeit mit praxisnaher KMU-Ausrichtung.

## 7. Quellen
Vollständige Angaben siehe `docs/references.md`.
