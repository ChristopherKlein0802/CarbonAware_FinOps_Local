# Berechnungsgrundlagen

Dieses Dokument beschreibt die Formeln und Annahmen, die in der Bachelorarbeit sowie im Prototypen zur Bestimmung von Kosten- und Emissionskennzahlen verwendet werden.

## 1. CO₂-Berechnung
**Formel (IEA/GHG-Standard):**
\[
\text{CO₂}_{\text{kg}} = \frac{\text{Leistung}_{\text{kW}} \times \text{Netzintensität}_{\text{g/kWh}} \times \text{Laufzeit}_{\text{h}}}{1000}
\]

- Leistung: aus Boavizta-Modellen bzw. 30/70-Leistungsmodell
- Netzintensität: ElectricityMaps (Region DE, Echtzeit oder 24h-Historie)
- Laufzeit: CloudTrail-Audit-Events
- Ergebnis: Kilogramm CO₂ pro Betrachtungszeitraum

**Beispiel:**
\(0{,}1\,\text{kW} \times 350\,\text{g/kWh} \times 720\,\text{h} / 1000 = 25{,}2\,\text{kg CO₂}\)

## 2. Leistungsmodell
**Energy-Proportional Computing (Barroso & Hölzle, 2007):**
\[
\text{Effektive Leistung} = \text{Basisleistung} \times (0{,}3 + 0{,}7 \times \text{CPU}_{\%})
\]

- 30 % Grundlast deckt konstante Verbraucher (Mainboard, Speicher, Kühlung) ab
- 70 % variabler Anteil folgt der CPU-Auslastung
- CPU-Auslastung in Prozent basiert auf CloudWatch-Metriken (Standardperioden)

## 3. Kostenmodell
\[
\text{Monatliche Kosten}_{\text{EUR}} = \text{Preis}_{\text{USD/h}} \times \text{Laufzeit}_{\text{h}} \times \text{Wechselkurs}_{\text{EUR/USD}}
\]

- Preise: AWS Pricing API (On-Demand, `eu-central-1`)
- Laufzeit: CloudTrail (vgl. Abschnitt 4)
- Wechselkurs: Europäische Zentralbank, im Prototyp als Konstante gepflegt

## 4. CloudTrail-basierte Laufzeitbestimmung
1. Sammeln der Events `RunInstances`, `StartInstances`, `StopInstances`, `TerminateInstances`.
2. Sortieren nach Zeitstempel und Paaren von Start/Stop-Ereignissen.
3. Summieren der Differenzen für den Betrachtungszeitraum.
4. Ergebnisse werden in `RuntimeTracker.process_instance_enhanced` gespeichert und für Kosten- und CO₂-Berechnungen genutzt.

## 5. Unsicherheiten und Annahmen
| Parameter | Unsicherheit | Quelle/Begründung |
|-----------|-------------|-------------------|
| ElectricityMaps Netzintensität | ±5 % | Anbieterangabe und Literatur [16], [17] |
| Boavizta Leistungsmodelle | ±10 % | Modellierung basierend auf Messreihen |
| CloudWatch CPU-Daten | ±5 % | Stichprobenbasierte Messung |
| AWS Cost Explorer | ±2 % | Rundungen und zeitliche Verzögerung |
| Business-Szenarien (Einsparungen) | ±15 % | Literaturwerte [7], [8], [15] |

Die kombinierte Unsicherheit für CO₂- und Kostenschätzungen liegt konservativ bei etwa ±12 % (Root-Sum-of-Squares).

## 6. Literaturbezug
- Barroso, L. A.; Hölzle, U. (2007): *The Case for Energy-Proportional Computing*.
- International Energy Agency (2022): *Global Energy & CO₂ Status Report*.
- Green Software Foundation (2023): *Software Carbon Intensity Specification*.
- McKinsey & Company (2024): *Cloud cost optimization: A $1 trillion opportunity*.
- Gartner (2024): *Market Guide for Cloud Financial Management Tools*.

Alle Quellen sind vollständig in `docs/references.md` nachgewiesen.
