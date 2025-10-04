# Carbon-Aware FinOps Tool – Bachelorarbeit

## Projektüberblick
- Integriertes Monitoring-System für Cloud-Kosten und CO₂-Emissionen mit Fokus auf deutsche KMU
- Kombination aus Echtzeit-Stromnetzmetriken, AWS-Laufzeitdaten und FinOps-Kennzahlen
- Forschungsprojekt im Rahmen eines Design-Science-Ansatzes mit offen dokumentierter Architektur und Evaluation
- Automatisierte Zeitreihen (48 h) aus AWS Cost Explorer & ElectricityMaps für Time Alignment Coverage (TAC) und interaktive Kosten/CO₂-Trade-offs im Dashboard

## Forschungsfrage und Teilfragen
„Wie lässt sich ein integriertes Monitoring-System entwickeln, das Kosten und CO₂-Emissionen von Cloud-Infrastrukturen simultan erfasst, und welche Vorteile bietet dieser Ansatz gegenüber bestehenden getrennten Lösungen?“

Zur Beantwortung werden folgende Teilfragen adressiert:
1. Welche Defizite weisen existierende Tools bei der Integration von Kosten- und Emissionsmetriken auf?
2. Wie lassen sich heterogene Datenquellen trotz unterschiedlicher Charakteristika robust integrieren?
3. Welche messbaren Vorteile bietet die Integration gegenüber getrennten Ansätzen?
4. Inwieweit lässt sich der entwickelte Ansatz auf verschiedene Unternehmensgrößen, Cloud-Anbieter und geografische Kontexte adaptieren?

## Motivation und Kontext
84 % der Unternehmen sehen Kostenkontrolle als größte Cloud-Herausforderung, während die CSRD ab 2024 detaillierte Emissionsreports inklusive Scope-3-Daten fordert. Deutsche KMU geraten damit doppelt unter Druck: Sie müssen Kosten senken und belastbare Emissionsdaten liefern, obwohl verfügbare Tools beide Dimensionen voneinander trennen. Der Prototyp schließt diese Lücke, indem er Kostentransparenz und Carbon Accounting gemeinsam adressiert und so eine belastbare Grundlage für Compliance-Reporting und FinOps-Entscheidungen schafft.

## Ziele und Beitrag
- Systematische Analyse bestehender Kosten- und Emissionslösungen samt Bewertungsframework
- Entwicklung eines integrierten Dashboards, das Echtzeitdaten, historische Laufzeiten und modellbasierte Emissionsberechnungen verknüpft
- Quantitative Evaluation über 30 Tage hinsichtlich Datenverfügbarkeit, Genauigkeit und Handlungsempfehlungen
- Dokumentation übertragbarer Integrationsmuster für KMU und Erweiterbarkeit auf weitere Regionen sowie Cloud-Anbieter

## Methodischer Ansatz (Design Science Research)
- **Problemidentifikation:** Literatur-Review und Marktanalyse definieren Integrationsdefizite getrennter Tools.
- **Anforderungsanalyse:** Ableitung funktionaler Anforderungen (z. B. No-Fallback-Policy, Unsicherheitsangaben, EU-spezifische Berichte).
- **Artefaktentwicklung:** Iterative Implementierung des Dashboards, inkl. API-Orchestrierung, Laufzeittracking und Business-Case-Modellen.
- **Evaluation:** Vergleich mit Baseline-Tools anhand verifizierter Metriken (CO₂/kg pro Instanz, Kostenabweichung, Datenlatenz).
- **Kommunikation:** Open-Source-Repository, reproduzierbare Makefile-Workflows und begleitende Dokumente in `docs/`.

## Systemarchitektur und Komponenten
- **Streamlit Frontend (`src/app.py`):** Navigierbares Dashboard mit Executive Summary, Carbon-Ansicht und Infrastrukturübersicht.
- **Datenorchestrierung (`src/core/processor.py`):** Aggregiert API-Daten, validiert Unsicherheiten und erstellt `DashboardData`-Payloads.
- **Domain-Services (`src/services/`):** `runtime.py` (CloudTrail & CloudWatch), `carbon.py` (ElectricityMaps & Time-Series), `business.py` (Validierung & Business Case).
- **Zeitreihen & TAC:** Die Services synchronisieren stündliche EC2-Kosten aus dem AWS Cost Explorer mit ElectricityMaps-Intensitäten (`TimeSeriesPoint`) und berechnen Time Alignment Coverage sowie Cost-MAPE.
- **Berechnungen (`src/core/calculator.py` & `src/utils/calculations.py`):** Emissions- und Kostenmodelle auf Basis Boavizta, ElectricityMaps und FinOps-Szenarien.
- **Infrastructure-Layer (`src/infrastructure/`):** `clients/` kapselt ElectricityMaps, Boavizta und AWS SDKs; `cache.py` und `time_series.py` liefern wiederverwendbare Persistenz-Utilities.
- **UI-Komponenten (`src/views/components/`):** Modulare, wiederverwendbare View-Komponenten (Grid Status, Metrics, Business Case, Validation, Time Series).
- **Infrastruktur (`terraform/`):** Referenzumgebung zur Reproduktion der Experimente mit AWS-Workloads im KMU-Skalierungsbereich.

- **Validierungsmetriken (`src/utils/validation.py`, `src/views/components/validation.py`):** Erfassen Laufzeit-, Preis- und Emissionsabdeckung je Instanz und stellen den Data-Precision-Score im Dashboard bereit.

```
CarbonAware_FinOps_Local/
├── src/
│   ├── infrastructure/   # Infrastruktur-Adapter (APIs, Cache, Zeitreihen)
│   │   ├── clients/      # ElectricityMaps, Boavizta, AWS-Adapter
│   │   ├── cache.py      # Zentrale Cache-Repository
│   │   └── time_series.py # Zeitreihen-Persistierung
│   ├── config/           # Pydantic-basierte Settings (`settings.py`)
│   ├── core/             # DataProcessor, Kalkulatoren, Tracker
│   ├── services/         # Runtime-, Carbon- und Business-Domain-Services
│   ├── models/           # Dataclasses für Dashboard-, Business- und AWS-Objekte
│   ├── utils/            # Validierungs-, Berechnungs- und UI-Hilfen
│   ├── views/            # Streamlit-Seiten (overview, carbon, infrastructure)
│   │   └── components/   # Wiederverwendbare UI-Komponenten
│   └── vendor/           # Externe Stub-Implementierungen (httpx)
├── docs/                 # Literaturarbeit, Methodik, Evaluationsprotokolle
├── tests/                # Unit-Tests für Kernlogik und Integrationspunkte
├── terraform/            # Infrastruktur-Templates für Evaluationsszenarien
├── Makefile              # Wiederholbare Befehle (Setup, Tests, Dashboard)
└── requirements.txt      # Abhängigkeiten (streamlit, boto3, pandas, plotly, etc.)
```

## Evaluationskonzept
- **Zeithorizont:** 30 Tage Beobachtung in einer kontrollierten AWS-Testumgebung.
- **Metriken:** Datenverfügbarkeit je API, TAC (Time Alignment Coverage), Cost-MAPE vs. AWS Billing, CO₂/kg je Instanz, Aggregationstreue gegenüber ElectricityMaps-Daten, Dashboard-Latenz sowie Data-Precision-Score.
- **Vergleichsbasis:** Manuell gepflegte Kostenreports und separate CO₂-Tracker (Baseline) vs. integrierte Darstellung im Dashboard.
- **Dokumentation:** Ergebnisse und Unsicherheiten werden in `docs/validation-results.md` sowie direkt im Dashboard ausgewiesen.
- **Aktueller Fokus:** Szenario-Integrationstests (z. B. geplante Start/Stop-Sequenzen), wiederholte CloudTrail-Analysen und der Aufbau eines belastbaren Messdatensatzes (siehe `docs/thesis-documentation.md`).

## Schnellstart
```bash
# Repository klonen
git clone <your-repo-url>
cd CarbonAware_FinOps_Local

# Virtuelle Umgebung einrichten
make setup

# (Optional) Tests vorbereiten – pytest installieren, falls nicht Bestandteil der Umgebung
# python3 -m pip install pytest

# Dashboard starten
make dashboard

# Browser öffnen (Standardport)
# http://localhost:8501

# Tests ausführen (optional, nach Installation von pytest)
# python3 -m pytest
```

## Aktueller Status & Offene Arbeiten
- Wiederholte CloudTrail-/Cost-Explorer-Abgleiche zur Reduktion des Validierungsfaktors sind geplant.
- Szenario-Integrationstests (Start/Stop, Carbon-aware Scheduling) werden vorbereitet, um Literaturannahmen empirisch zu belegen.
- Aufbau eines Messdatensatzes und Dokumentation der 48 h-Zeitreihen für die schriftliche Arbeit laufen (`docs/thesis-documentation.md`).

## Optionale AWS-Integration
```bash
# AWS SSO Profil vorbereiten
aws configure sso --profile your-profile-name
aws sso login --profile your-profile-name

# Beispielkonfiguration kopieren
cp .env.example .env
# ELECTRICITYMAP_API_KEY im neuen .env hinterlegen

# Testinfrastruktur bereitstellen (optional)
make deploy
```

## Dokumentation und Quellen
- Methodische Details, Marktanalyse und Evaluationspläne: `docs/thesis-documentation.md`
- Literatur- und Quellenverwaltung: `docs/references.md`
- Modularisierung und Integrationsmuster: `docs/literature-integration.md`

## Lizenz
Das Projekt entstand im Rahmen einer Bachelorarbeit. Die Nutzung richtet sich nach den Vorgaben der Hochschule; ergänzende Hinweise stehen in `LICENSE`.
