# Carbon-Aware FinOps Tool – Bachelorarbeit

## Forschungsfrage
„Wie kann ein integriertes Carbon-aware FinOps Tool durch die Kombination von Echtzeit-Stromnetz-Daten sowohl Kosten als auch CO₂-Emissionen optimieren – im Vergleich zu separaten Tools?“

## Problemstellung
Deutsche kleine und mittlere Unternehmen (KMU) nutzen Cloud-Infrastrukturen zunehmend intensiv, jedoch adressieren verfügbare Werkzeuge meist nur entweder Kosten- oder CO₂-Transparenz [7], [8], [10]. Regionale Netzcharakteristika und präzise Laufzeittelemetrie fehlen häufig, wodurch EU-Compliance-Anforderungen und Budgetgrenzen deutscher KMU nur unzureichend berücksichtigt werden [11], [12], [19].

## Beitrag des Prototyps
Der Prototyp implementiert einen integrierten Monitoring- und Optimierungs-Workflow mit:
- ElectricityMaps für die deutsche Netz-Carbon-Intensität (2-Stunden-Cache) [4], [16], [17].
- Boavizta-Hardwaremodellen zur nutzungsabhängigen Energieeinschätzung [1], [2], [6].
- AWS Cost Explorer, Pricing, CloudTrail und CloudWatch für Kostenvalidierung, Preisdaten, Laufzeitaudits und CPU-Metriken [7], [13].

Damit werden insgesamt sechs spezialisierte Services orchestriert, um Kosten-, Laufzeit- und Emissionsdaten konsistent zu vereinen.

Die Integration dient als reproduzierbare Referenzimplementierung für carbon-aware FinOps im KMU-Skalierungsbereich (ca. 20–100 Instanzen) mit wissenschaftlicher Nachvollziehbarkeit.

## Systemüberblick
Das Streamlit-Dashboard (`src/app.py`) bildet die Präsentationsschicht und orchestriert Datenerhebung über den `DataProcessor` (`src/core/processor.py`). Dieser koordiniert API-Clients, Laufzeit-Tracking und Business-Case-Berechnungen. Dataclasses modellieren die Messwerte (`src/models`), während Utilities Caching, Logging, Validierung und Berechnungen kapseln. Terraform-Artefakte (`terraform/`) stellen eine repräsentative AWS-Testumgebung bereit.

```
CarbonAware_FinOps_Local/
├── src/
│   ├── api/              # External API clients (ElectricityMaps, AWS, Boavizta)
│   ├── core/             # Data processing, runtime tracking, optimisation logic
│   ├── models/           # Dataclasses for dashboard payloads
│   ├── utils/            # Shared utilities (caching, calculations, logging)
│   └── views/            # Streamlit view components
├── docs/                 # Methodology, validation and market analyses
├── tests/                # Unit tests for calculators, processor, tracker
├── terraform/            # AWS test environment templates
├── Makefile              # Reproducible workflow commands
├── requirements.txt      # Baseline dependencies
└── requirements-frozen.txt # Locked environment for reproducibility
```

## Wissenschaftliche Methodik
- **No-Fallback-Policy:** API-Ausfälle werden sichtbar gemacht, anstatt durch synthetische Daten kaschiert zu werden.
- **CO₂-Berechnung:** Monatswerte basieren auf etablierten Leistungs- und Intensitätsmodellen (IEA, GSF) [4], [6]; die Leistungs-Skalierung nutzt das 30/70-Modell für Serverlast [1], [2].
- **Kosten- und Business-Case-Modellierung:** Szenariofaktoren stützen sich auf konservative Werte aus jüngeren FinOps-Studien [7], [8], [9].
- **Unsicherheiten:** Jede Dashboard-Antwort weist explizite Unsicherheiten und Datenquellen aus.

## Schnellstart
```bash
# 1. Repository klonen
git clone <your-repo-url>
cd CarbonAware_FinOps_Local

# 2. Virtuelle Umgebung einrichten
make setup

# 3. Dashboard starten
make dashboard

# 4. Browser öffnen
# http://localhost:8501
```

## Optional AWS Integration
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

## Dokumentation
Ausführliche Hintergründe zu Methodik, Validierung und Marktanalyse finden sich in `docs/thesis-documentation.md`, `docs/literature-integration.md` und weiteren Dokumenten. Das vollständige Literaturverzeichnis steht in `docs/references.md`.

## Lizenz
Das Projekt entstand im Rahmen einer Bachelorarbeit. Die Nutzung ist an die Richtlinien der jeweiligen Hochschule gebunden; ergänzende Hinweise stehen in `LICENSE`.

## Quellen
Alle Quellenangaben sind in `docs/references.md` aufgeführt; Zitationen folgen dem dortigen Nummerierungsschema.
