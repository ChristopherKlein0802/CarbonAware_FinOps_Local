# Systemarchitektur: Carbon-Aware FinOps Dashboard

## 1. Einordnung
- **Forschungsfrage:** Wie lässt sich ein integriertes Monitoring-System entwickeln, das Kosten und CO₂-Emissionen von Cloud-Infrastrukturen simultan erfasst, und welche Vorteile bietet dieser Ansatz gegenüber bestehenden getrennten Lösungen?
- **Projektziel:** Referenzarchitektur für deutsche KMU (ca. 20–100 AWS-Instanzen) mit klarer Trennung von Datenakquise, Verarbeitung und Visualisierung.
- **Methodik:** Design-Science-Ansatz mit iterativen Build-Evaluate-Zyklen und nachvollziehbarer Dokumentation.

## 2. Projektstruktur
```
CarbonAware_FinOps_Local/
├── src/
│   ├── app.py               # Streamlit-Einstieg und Seitenrouting
│   ├── infrastructure/      # Infrastruktur-Layer
│   │   ├── clients/         # API-Adapter: ElectricityMaps, AWS, Boavizta
│   │   ├── cache.py         # Zentrale Cache-Repository
│   │   └── time_series.py   # Zeitreihen-Persistierung
│   ├── config/              # Pydantic-Settings und Konfiguration
│   ├── services/            # Domain-Services (Runtime, Carbon, Business)
│   ├── core/                # DataProcessor, Tracker, Kalkulatoren
│   ├── models/              # Dataclasses für Dashboard-, Business- und AWS-Objekte
│   ├── utils/               # Validierungs-, Berechnungs- und UI-Hilfen
│   ├── views/               # Streamlit-Seiten (overview, carbon, infrastructure)
│   │   └── components/      # Wiederverwendbare UI-Komponenten
│   └── vendor/              # Externe Stub-Implementierungen
├── docs/                    # Methodik, Architektur, Evaluation, Literatur
├── tests/                   # Unit- und Integrationstests
├── terraform/               # Reproduzierbare AWS-Testumgebung
├── Makefile                 # Automatisierte Workflows (Setup, Tests, Dashboard)
└── requirements*.txt        # Abhängigkeitsmanagement
```

## 3. Schichtenmodell
- **Präsentation (`src/app.py`, `src/views/`)**
  - Streamlit-basierte Oberfläche mit Executive Summary, Carbon-Analyse und Infrastrukturdetail.
  - Modulare UI-Komponenten in `src/views/components/` (Grid Status, Metrics, Business Case, Validation, Time Series).
  - Einheitliche UI-Hilfen über `src/utils/ui.py` und CSS-Assets.
- **Domain-Services (`src/services/`)**
  - `RuntimeService`: EC2-Discovery, CloudTrail-basierte Laufzeitberechnung, CPU-Enrichment via CloudWatch.
  - `CarbonDataService`: ElectricityMaps-Integration, Zeitreihen-Aggregation, TAC (Time Alignment Coverage)-Berechnung.
  - `BusinessInsightsService`: Business-Case-Modelle, Kosten-Validierung gegen AWS Cost Explorer.
  - Factory-Pattern in `services/__init__.py` für Dependency Injection.
- **Verarbeitung (`src/core/`)**
  - `DataProcessor`: Orchestriert Domain-Services, konsolidiert Messwerte und erstellt `DashboardData`.
  - `BusinessCaseCalculator`: Wirtschaftlichkeits- und Emissionslogik.
  - `RuntimeTracker`: Legacy-Komponente (größtenteils zu `RuntimeService` migriert).
- **Integration (`src/infrastructure/`)**
  - `clients/` kapselt ElectricityMaps-, Boavizta- und AWS-spezifische Adapter.
  - `InfrastructureGateway`: Aggregiert alle API-Clients in einer einheitlichen Schnittstelle.
  - `cache.py` & `time_series.py` stellen wiederverwendbare Infrastruktur-Bausteine bereit.
- **Domänenmodell (`src/models/`)**
  - Typisierte Dataclasses für EC2-Instanzen, Carbon-Metriken, Business Cases und Dashboard-Responses.
  - Enthalten Metadaten zu Datenquellen, Unsicherheiten und Aktualität.
  - Vollständige Type Hints (z.B. `CarbonIntensity` statt `Any`).
- **Konfiguration (`src/config/`)**
  - `settings.py`: Zentralisierte Pydantic-Settings mit Umgebungsvariablen-Support.
  - Finanzielle Konstanten (z.B. `EUR_USD_RATE`) jetzt konfigurierbar via `.env`.
- **Querschnitt (`src/utils/`)**
  - `calculations.py`: Mathematische Kernfunktionen (z. B. Leistungsmodell, Rundungslogik).
  - `validation.py` und `errors.py`: Gemeinsame Validierungs- und Fehlermeldungsstrukturen.
  - `ui.py`: UI-Hilfsfunktionen (Grid-Status-Berechnung, Trade-off-Kalkulation).


## 4. Datenfluss
```mermaid
graph TD
    A[Streamlit UI] -->|User Request| B[DataProcessor]
    B --> C[RuntimeTracker]
    B --> D[CO2 Calculations (utils)]
    B --> E[BusinessCaseCalculator]
    B --> F[Infrastructure Gateway]
    F --> G[ElectricityMaps]
    F --> H[Boavizta]
    F --> I[AWS Services]
    C --> I
    D --> J[DashboardData]
    E --> J
    B --> J
    J --> A
```

## 5. API-Layer und Datenmodelle
- **InfrastructureGateway (`src/infrastructure/clients/__init__.py`):** Aggregiert ElectricityMaps-, Boavizta- und AWS-Adapter und stellt eine einheitliche Schnittstelle für die Domain bereit.
- **AWS-Billing-Client (`src/infrastructure/clients/aws.py`):** Spezialisiert auf Cost Explorer & Pricing, inklusive Cache-Schicht.
- **AWS-Runtime-Gateway (`src/infrastructure/clients/aws_runtime.py`):** Umhüllt EC2-, CloudTrail- und CloudWatch-Aufrufe für Laufzeit- und Leistungsdaten.
- **ElectricityMaps (`src/infrastructure/clients/electricity.py`):** Liefert aktuelle Intensitäten sowie 24h-Historien inklusive Self-Collection.
- **Boavizta (`src/infrastructure/clients/boavizta.py`):** Berechnet Leistungsprofile für AWS-Instanzen.

| Methode | Quelle | Zweck | Rückgabe |
|---------|--------|-------|----------|
| `get_current_carbon_intensity(zone)` | ElectricityMaps | Echtzeit-Netzintensität | `Optional[CarbonIntensity]` |
| `get_carbon_intensity_24h(zone)` | ElectricityMaps | Trendanalyse auf 24h-Basis | `Optional[List[CarbonPoint]]` |
| `get_power_profile(instance_type)` | Boavizta | Leistungsmodell (min/avg/max) | `Optional[PowerProfile]` |
| `get_monthly_costs()` | AWS Cost Explorer | Validierung der Ausgaben | `Optional[AWSCostData]` |
| `get_hourly_costs(hours)` | AWS Cost Explorer | Stündliche EC2-Kosten (48 h) | `Optional[List[dict]]` |
| `get_instance_pricing(instance_type, region)` | AWS Pricing | On-Demand-Preis pro Instanz | `Optional[InstancePrice]` |

**Genutzte Dataclasses (`src/models/`):** `CarbonIntensity`, `PowerProfile`, `AWSCostData`, `DashboardData` (inkl. `APIHealthStatus` & `TimeSeriesPoint`) dokumentieren Quellen, Zeitstempel und Unsicherheiten.

## 6. Cache-Mechanismen
| Datenquelle | Modul | Cache-TTL (`CacheTTL`) | Begründung |
|-------------|-------|------------------------|------------|
| ElectricityMaps (aktuell) | `src/infrastructure/clients/electricity.py` | 60 Minuten (`CARBON_DATA`) | Netzintensität ändert sich stündlich.
| ElectricityMaps (24h) | `src/infrastructure/clients/electricity.py` | 2 Stunden (`CARBON_24H`) | Historische Daten können länger gecacht werden.
| Boavizta Hardwareprofile | `src/infrastructure/clients/boavizta.py` | 7 Tage (`POWER_DATA`) | Instanzmodelle ändern sich selten.
| AWS Pricing | `src/infrastructure/clients/aws.py` | 7 Tage (`PRICING_DATA`) | Listenpreise werden selten angepasst.
| AWS Cost Explorer | `src/infrastructure/clients/aws.py` | 6 Stunden (`COST_DATA`) | Abrechnungsdaten werden täglich aktualisiert.
| AWS CloudWatch | `src/infrastructure/clients/aws_runtime.py` | 3 Stunden (`CPU_UTILIZATION`) | Balance aus Aktualität und API-Kosten.
| AWS CloudTrail | `src/services/runtime.py` | 24 Stunden (`CLOUDTRAIL_EVENTS`) | Events sind unveränderlich, tägliche Synchronisation genügt.
| Cost/Carbon Time Series | `src/core/processor.py` | 48 Stunden (lokale JSON-Snapshots) | Grundlage für TAC und Trade-off-Visualisierung.

Die Cache-Funktionen (`src/infrastructure/cache.py`) verwalten Pfade, TTLs und Bereinigung; `FileCacheRepository.clean_old` verhindert überalterte Artefakte. Dadurch sinkt das API-Aufkommen um >80 % und die Betriebskosten bleiben im KMU-Rahmen.

## 7. Qualitätsmechanismen
- **No-Fallback-Policy:** Jeder API-Ausfall wird sichtbar gemacht (`None`/Warnungen statt synthetischer Werte).
- **Unsicherheitsmetadaten:** `DashboardData` speichert Intervallangaben (z. B. ±15 % für Carbon-Szenarien).
- **Validierung:** `BusinessCaseCalculator.calculate_cloudtrail_enhanced_accuracy` gleicht berechnete Kosten mit AWS-Kosten ab.
- **Tests:** Unit-Tests für Kalkulationen und Tracker (`tests/unit/`), Integrationstest-Skript für End-to-End-Durchläufe (`tests/integration/`).

## 8. Anschluss an die Thesis
- **Design-Science-Artefakt:** Architektur dient als Artefakt im Sinne von Hevner et al. mit dokumentiertem Nutzenbeitrag für KMU.
- **Evaluationsgrundlage:** Struktur ermöglicht Messung der Forschungskennzahlen (Kostenabweichung, CO₂-Einsparungspotenziale, Datenverfügbarkeit).
- **Reproduzierbarkeit:** Makefile-Workflows und Requirements-Dateien sichern Wiederholbarkeit der Experimente.

## 9. Weiterführende Dokumente
- `docs/user-guide.md` – detaillierte Schritte zur Inbetriebnahme.
- `docs/calculations.md` – verwendete Formeln und Unsicherheiten.
- `docs/cloudtrail-methodology.md` – präzise Laufzeiterfassung.
- `docs/validation-results.md` – Ergebnisse der Integrationsläufe.
