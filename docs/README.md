# Dokumentation - Carbon-Aware FinOps Dashboard

Diese Dokumentation ist in sechs Hauptkategorien organisiert:

## Architecture
Technische Architektur-Dokumentation mit visuellen Diagrammen:
- [system-architecture.md](architecture/system-architecture.md) - Vollständige Systemarchitektur (Clean Architecture, Layer-Trennung)
- [diagrams/](architecture/diagrams/) - Mermaid-Diagramme (Data Flow, API Integration)
- [decisions/](architecture/decisions/) - Architecture Decision Records (ADRs)

**Zielgruppe:** Software-Architekten, technische Reviewer, Entwickler

## Methodology
Wissenschaftliche Methodik und Berechnungsgrundlagen:
- [calculations.md](methodology/calculations.md) - CO₂-Emissions- und Kostenberechnungen
- [cloudtrail-methodology.md](methodology/cloudtrail-methodology.md) - CloudTrail-basierte Laufzeitberechnung
- [cost-explorer-analysis.md](methodology/cost-explorer-analysis.md) - AWS Cost Explorer Integration

**Zielgruppe:** Wissenschaftliche Reviewer, Methodologie-Experten

## Research
Forschungsdokumentation für die Bachelor-Thesis:
- [thesis-documentation.md](research/thesis-documentation.md) - Haupt-Thesis-Dokumentation
- [market-analysis.md](research/market-analysis.md) - Marktanalyse bestehender Tools
- [literature-integration.md](research/literature-integration.md) - Literaturintegration und akademische Quellen
- [validation-results.md](research/validation-results.md) - Evaluationsergebnisse und Validierung
- [references.md](research/references.md) - Vollständiges Literaturverzeichnis

**Zielgruppe:** Thesis-Komitee, akademische Reviewer

## User
Anleitungen für Endbenutzer und Entwickler:
- [user-guide.md](user/user-guide.md) - Benutzerhandbuch für das Dashboard
- [developer-handbook.md](user/developer-handbook.md) - Entwickler-Handbuch für Erweiterung und Wartung
- [integration-testing-plan.md](user/integration-testing-plan.md) - Integrationstests-Anleitung

**Zielgruppe:** End-User, Entwickler, QA Engineers

## Thesis
Thesis-spezifische Materialien für Verteidigung und Einreichung:
- [quick-reference.md](thesis/quick-reference.md) - Defense Preparation Cheat Sheet

**Zielgruppe:** Thesis-Verteidigung, Komitee-Vorbereitung

## Quality
Qualitätsmetriken und Test-Dokumentation:
- [test-coverage-report.md](quality/test-coverage-report.md) - Test Coverage Analysis (79 passing tests)

**Zielgruppe:** QA Engineers, technische Reviewer

## Quick Navigation

| Rolle | Start hier | Beschreibung |
|-------|------------|--------------|
| Thesis-Reviewer | [research/thesis-documentation.md](research/thesis-documentation.md) | Vollständige Thesis-Dokumentation |
| Defense Vorbereitung | [thesis/quick-reference.md](thesis/quick-reference.md) | Cheat Sheet für Verteidigung |
| Architektur-Review | [architecture/system-architecture.md](architecture/system-architecture.md) | Clean Architecture Überblick |
| Visuelle Diagramme | [architecture/diagrams/](architecture/diagrams/) | Mermaid-Diagramme |
| Wissenschaftliche Methodik | [methodology/calculations.md](methodology/calculations.md) | Berechnungsgrundlagen |
| Dashboard-Nutzung | [user/user-guide.md](user/user-guide.md) | Benutzerhandbuch |
| Entwickler | [user/developer-handbook.md](user/developer-handbook.md) | Entwickler-Handbuch |
| QA/Testing | [quality/test-coverage-report.md](quality/test-coverage-report.md) | Test Coverage Report |

## Dokumentations-Standards

Alle Dokumente folgen den folgenden Konventionen:
- Markdown-Format für bessere Lesbarkeit und Version Control
- Strukturierte Sections mit klaren Überschriften
- Code-Beispiele mit Syntax-Highlighting
- Diagramme wo sinnvoll (Mermaid für visuelle Architektur)
- Cross-References zu verwandten Dokumenten
- Academic Citations in wissenschaftlichen Dokumenten

## Verwandte Ressourcen

### Externe Dokumentation
- [AWS Documentation](https://docs.aws.amazon.com/) - CloudTrail, Cost Explorer, EC2 APIs
- [Boavizta API](https://doc.api.boavizta.org/) - Hardware power consumption models
- [ElectricityMaps API](https://static.electricitymaps.com/api/docs/index.html) - Real-time grid carbon intensity

### Code-Dokumentation
- [src/domain/protocols.py](../src/domain/protocols.py) - Clean Architecture interfaces
- [src/domain/calculations.py](../src/domain/calculations.py) - Core calculation logic
- [tests/unit/](../tests/unit/) - Unit tests

## Wartung

Letzte umfassende Reorganisation: Oktober 2025
