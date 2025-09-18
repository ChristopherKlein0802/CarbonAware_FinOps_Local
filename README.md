# Carbon-Aware FinOps Tool – Bachelor Thesis

## Research Question
"Wie kann ein integriertes Carbon-aware FinOps Tool durch die Kombination von Echtzeit-Stromnetz-Daten sowohl Kosten als auch CO2-Emissionen optimieren – im Vergleich zu separaten Tools?"

## Problem Context
Small and medium sized enterprises (SMEs) in Germany increasingly rely on cloud infrastructures, yet available optimisation tools address either financial visibility or environmental reporting in isolation [7], [8], [10]. Current offerings rarely incorporate regional grid characteristics or high fidelity runtime telemetry, which limits their suitability for EU climate compliance and SME budget constraints [11], [12], [19].

## Proposed Contribution
The prototype implements a unified monitoring and optimisation workflow that combines:
- ElectricityMaps based German grid carbon intensity data with two hour caching [4], [16], [17].
- Boavizta hardware power models for utilisation sensitive energy estimates [1], [2], [6].
- AWS Cost Explorer, Pricing, CloudTrail and CloudWatch interfaces for billing validation, pricing data, runtime audits, and CPU metrics [7], [13].

This integration aims to provide a reproducible reference implementation for carbon-aware FinOps in SME-scale environments (20–100 instances) while maintaining academic transparency.

## System Overview
The Streamlit dashboard (`src/app.py`) acts as presentation layer and orchestrates data acquisition through the `DataProcessor` controller (`src/core/processor.py`). The processor coordinates API clients, runtime tracking, and business case calculations. Dataclasses model the resulting measurements (`src/models`). Auxiliary utilities cover caching, logging, validation, and scientific calculations. Infrastructure-as-code artefacts inside `terraform/` provision a representative AWS testbed.

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

## Scientific Methodology
- **No-Fallback Policy:** API failures surface to the dashboard instead of being masked by synthetic data to maintain traceability.
- **Carbon Calculations:** Monthly emissions derive from standard power-intensity runtime models endorsed by the IEA and GSF [4], [6]. Power scaling adopts the literature-backed 30/70 idle-to-load approximation for servers [1], [2].
- **Cost and Business Cases:** Scenario factors use conservative ranges reported in recent FinOps and cloud cost optimisation studies [7], [8], [9].
- **Uncertainty Reporting:** Each dashboard response contains explicit uncertainty annotations describing data provenance and estimated accuracy bands.

## Quick Start
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

## Documentation
Detailed background on methodology, validation procedure, and market positioning is available in `docs/thesis-documentation.md`, `docs/literature-integration.md`, and related documents. A consolidated bibliography is maintained in `docs/references.md`.

## Licence
Das Projekt wurde im Rahmen einer Bachelorarbeit erstellt. Die Nutzung unterliegt den Richtlinien der jeweiligen Hochschule. Bitte beachten Sie ergänzende Hinweise in `LICENSE`.

## References
Alle Quellenangaben befinden sich in `docs/references.md`. Inline-Zitate verwenden das dort definierte Nummerierungsschema.
