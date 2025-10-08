# 🏗️ System Architecture Documentation

This directory contains documentation about the system architecture, design decisions, and visual diagrams.

## 📁 Contents

### Core Documentation
- [**system-architecture.md**](system-architecture.md) - Complete system architecture overview

### Visual Diagrams (Mermaid)
- [**diagrams/clean-architecture-layers.md**](diagrams/clean-architecture-layers.md) - 4-Layer Clean Architecture with dependency flow
- [**diagrams/data-flow-diagram.md**](diagrams/data-flow-diagram.md) - Complete data pipeline from APIs to UI
- [**diagrams/api-integration-overview.md**](diagrams/api-integration-overview.md) - External API integrations (AWS, ElectricityMaps, Boavizta)

### Architecture Decisions
- [**decisions/000-initial-refactoring-phase1.md**](decisions/000-initial-refactoring-phase1.md) - Initial refactoring decisions
- [**decisions/001-naming-conventions-refactoring.md**](decisions/001-naming-conventions-refactoring.md) - Naming conventions and cleanup

## 🎯 Purpose

The architecture documentation explains:

- **System Structure:** How components are organized and interact
- **Design Principles:** Clean Architecture, SOLID, Domain-Driven Design
- **Dependency Flow:** Protocol-based dependency inversion
- **Layer Separation:** Domain, Application, Infrastructure, Presentation
- **Visual Models:** Mermaid diagrams for presentations
- **Design Decisions:** Architecture Decision Records (ADRs)

## 📊 Key Architectural Patterns

### 1. Clean Architecture (4 Layers)
- **Domain Layer:** Business logic, protocols, models
- **Application Layer:** Use cases, orchestrator
- **Infrastructure Layer:** External APIs, cache
- **Presentation Layer:** Streamlit UI

### 2. Protocol-Based Dependency Inversion
- Domain defines interfaces (protocols)
- Infrastructure implements protocols via duck typing
- Zero coupling from domain to infrastructure

### 3. Use Case Pattern
- Single-responsibility use cases
- Orchestrator delegates to use cases (thin coordinator)
- Easy to test and maintain

## 🔗 Related Documentation

- [Visual Diagrams (diagrams/)](diagrams/) - Mermaid architecture diagrams
- [Architecture Decisions (decisions/)](decisions/) - ADRs documenting key decisions
- [Quality Metrics (../quality/)](../quality/) - Test coverage and code quality

---

**For thesis reviewers:** Start with [system-architecture.md](system-architecture.md) for overview, then see [diagrams/](diagrams/) for visual representations.

**For presentations:** Use diagrams for visual aids during thesis defense.
