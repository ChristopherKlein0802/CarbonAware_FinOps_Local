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
- **Zeitreihen & TAC:** `DataProcessor` synchronisiert stündliche EC2-Kosten aus dem AWS Cost Explorer mit ElectricityMaps-Intensitäten (`TimeSeriesPoint`) als Grundlage für Time Alignment Coverage und Cost-MAPE.
- **Laufzeittracking (`src/core/tracker.py`):** Nutzt CloudTrail-Events und CloudWatch-Metriken für präzise Betriebsstunden.
- **Berechnungen (`src/core/calculator.py` & `src/utils/calculations.py`):** Emissions- und Kostenmodelle auf Basis Boavizta, ElectricityMaps und FinOps-Szenarien.
- **API-Clients (`src/api/`):** Kapseln Zugriffe auf ElectricityMaps, AWS Cost Explorer, AWS Pricing, CloudWatch und optionale Datenquellen.
- **Infrastruktur (`terraform/`):** Referenzumgebung zur Reproduktion der Experimente mit AWS-Workloads im KMU-Skalierungsbereich.

```
CarbonAware_FinOps_Local/
├── src/
│   ├── api/              # Externe Schnittstellen zu ElectricityMaps, AWS, Boavizta
│   ├── core/             # DataProcessor, Tracker, Business- und Carbon-Kalkulatoren
│   ├── models/           # Dataclasses für Dashboard-, Business- und AWS-Objekte
│   ├── utils/            # Cache-, Validierungs- und Berechnungshilfen
│   └── views/            # Streamlit-Komponenten und Layout-Logik
├── docs/                 # Literaturarbeit, Methodik, Evaluationsprotokolle
├── tests/                # Unit-Tests für Kernlogik und Integrationspunkte
├── terraform/            # Infrastruktur-Templates für Evaluationsszenarien
├── Makefile              # Wiederholbare Befehle (Setup, Tests, Dashboard)
├── requirements.txt      # Abhängigkeitsbasis für die Entwicklungsumgebung
└── requirements-frozen.txt # Reproduzierbare Referenzumgebung
```

## Evaluationskonzept
- **Zeithorizont:** 30 Tage Beobachtung in einer kontrollierten AWS-Testumgebung.
- **Metriken:** Datenverfügbarkeit je API, TAC (Time Alignment Coverage), Cost-MAPE vs. AWS Billing, CO₂/kg je Instanz, Aggregationstreue gegenüber ElectricityMaps-Daten, Dashboard-Latenz.
- **Vergleichsbasis:** Manuell gepflegte Kostenreports und separate CO₂-Tracker (Baseline) vs. integrierte Darstellung im Dashboard.
- **Dokumentation:** Ergebnisse und Unsicherheiten werden in `docs/evaluation/` sowie direkt im Dashboard ausgewiesen.

## Schnellstart
```bash
# Repository klonen
git clone <your-repo-url>
cd CarbonAware_FinOps_Local

# Virtuelle Umgebung einrichten
make setup

# Dashboard starten
make dashboard

# Browser öffnen (Standardport)
# http://localhost:8501
```

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
