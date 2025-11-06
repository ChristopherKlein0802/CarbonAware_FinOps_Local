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

## 3. Kostenmodell (Period-Agnostisch)
\[
\text{Kosten}_{\text{EUR}} = \text{Preis}_{\text{USD/h}} \times \text{Laufzeit}_{\text{h}} \times \text{Wechselkurs}_{\text{EUR/USD}}
\]

**Flexible Analysezeiträume**: Das System unterstützt variable Zeitfenster für die Kostenanalyse:
- **1 Tag** (24h): Für tägliche Tracking und schnelle Anomalieerkennung
- **7 Tage**: Für wöchentliche Trends und Workload-Pattern-Analyse
- **30 Tage**: Für monatliche Budgetplanung und Langzeittrends

**Datenquellen**:
- Preise: AWS Pricing API (On-Demand, `eu-central-1`)
- Laufzeit: CloudTrail (vgl. Abschnitt 4)
- Wechselkurs: Europäische Zentralbank, im Prototyp als Konstante gepflegt

**Period-Aligned Cost Validation**: Cost Explorer Daten werden mit dem gleichen `period_days` Fenster abgerufen wie die CloudTrail Runtime-Berechnung, um Cache-Kontamination durch alte Instanzen zu vermeiden.

## 4. CloudTrail-basierte Laufzeitbestimmung
1. Sammeln der Events `RunInstances`, `StartInstances`, `StopInstances`, `TerminateInstances`.
2. Sortieren nach Zeitstempel und Paaren von Start/Stop-Ereignissen.
3. Summieren der Differenzen für den Betrachtungszeitraum.
4. Ergebnisse werden in `RuntimeTracker.process_instance_enhanced` gespeichert und für Kosten- und CO₂-Berechnungen genutzt.

## 5. Dual Calculation Methods (v2.0.0)

Das System implementiert zwei parallele Berechnungsmethoden für CO₂-Emissionen und Kosten, um Methodenvalidierung und akademische Rigorosität zu gewährleisten:

### 5.1 24h-Pattern Based Method (Hourly-Precise)
\[
\text{CO₂}_{\text{total}} = \sum_{i=1}^{24} \left( \text{Power}_i \times \text{GridIntensity}_i \times \text{Runtime}_i \right) \times \text{period\_days}
\]

**Anwendung**: Instanzen mit vollständigen 24-Stunden-Daten
- Verwendet stündliche Carbon Intensity Patterns von ElectricityMaps
- Skaliert 24h-Muster auf den Analysezeitraum (1d, 7d, oder 30d)
- Genauer für Always-On oder vorhersagbare Workloads
- Erfordert: Vollständige 24h Runtime-, CPU- und Carbon-Daten

**Datenqualität**: `data_quality="measured"` wenn ≥18h Coverage, sonst `"partial"`

### 5.2 Average Runtime Based Method
\[
\text{CO₂}_{\text{total}} = \text{Power}_{\text{avg}} \times \text{GridIntensity}_{\text{avg}} \times \text{Runtime}_{\text{total}}
\]

**Anwendung**: Alle Instanzen (Fallback bei unvollständigen 24h-Daten)
- Verwendet Period-Average Carbon Intensity
- Multipliziert mit tatsächlichen Runtime-Stunden über Analysezeitraum
- Konservativere Schätzung für variable Workloads
- Funktioniert mit jedem Runtime-Fenster

**Datenqualität**: `data_quality="average"` (immer verfügbar als Fallback)

### 5.3 Methodenvergleich und Auswahl

Das Dashboard zeigt beide Methoden zur Validierung:
- **Primary Display**: Average Runtime Based (konservativ, alle Instanzen)
- **Comparison View**: Infrastructure Details Seite zeigt Dual Comparison
- **Business Case**: Nutzt Average-Based als Baseline (sicherste Schätzung)

**Aggregation**:
```
total_co2_hourly = sum(instances with method="hourly")
total_co2_average = sum(all instances with method="average")
```

Die Differenz zwischen beiden Methoden dient als Methodenvalidierung und Unsicherheitsabschätzung.

## 6. Stündliche Kosten-/CO₂-Zeitreihe im Dashboard
- Der `DataProcessor` erzeugt für die letzten 48 Stunden eine Serie aus AWS-Cost-Explorer-Kosten (`€/h`) und ElectricityMaps-Intensitäten (`g CO₂/kWh`).
- Das stündliche CO₂-Äquivalent basiert auf dem gemessenen Monatswert (`total_co2_kg / 730 h`) und wird mit dem Verhältnis der jeweiligen Netzdichte zum Durchschnitt der verfügbaren Stunden gewichtet.
- Bei fehlender Intensität wird der Basiswert (durchschnittliche Emission pro Stunde) angezeigt; es werden keine synthetischen Peaks erzeugt.
- Die Methode liefert relative Verläufe für die Interpretierbarkeit im Dashboard und ersetzt keine vollständige Monatsverlaufsmessung.

## 7. Unsicherheiten und Annahmen
| Parameter | Unsicherheit | Quelle/Begründung |
|-----------|-------------|-------------------|
| ElectricityMaps Netzintensität | ±5 % | Anbieterangabe und Literatur [16], [17] |
| Boavizta Leistungsmodelle | ±10 % | Modellierung basierend auf Messreihen |
| CloudWatch CPU-Daten | ±5 % | Stichprobenbasierte Messung |
| AWS Cost Explorer | ±2 % | Rundungen und zeitliche Verzögerung |
| Business-Szenarien (Einsparungen) | ±15 % | Literaturwerte [7], [8], [15] |

Die kombinierte Unsicherheit für CO₂- und Kostenschätzungen liegt konservativ bei etwa ±12 % (Root-Sum-of-Squares).

## 8. Literaturbezug
- Barroso, L. A.; Hölzle, U. (2007): *The Case for Energy-Proportional Computing*.
- International Energy Agency (2022): *Global Energy & CO₂ Status Report*.
- Green Software Foundation (2023): *Software Carbon Intensity Specification*.
- McKinsey & Company (2024): *Cloud cost optimization: A $1 trillion opportunity*.
- Gartner (2024): *Market Guide for Cloud Financial Management Tools*.

Alle Quellen sind vollständig in `docs/references.md` nachgewiesen.
