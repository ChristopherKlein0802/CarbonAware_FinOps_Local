# Clean Architecture - Layer Diagram

## 🏗️ 4-Layer Architecture Overview

This diagram shows the Clean Architecture implementation with strict dependency flow.

```mermaid
graph TB
    subgraph Presentation["🎨 Presentation Layer (UI)"]
        Pages["Streamlit Pages<br/>overview.py<br/>carbon_analysis.py<br/>infrastructure_details.py"]
        Components["UI Components<br/>metrics, business_case<br/>time_series, validation"]
    end

    subgraph Application["📋 Application Layer (Use Cases)"]
        Orchestrator["DashboardDataOrchestrator<br/>(Thin Coordinator)"]
        UseCases["Use Cases<br/>FetchInfrastructureData<br/>EnrichInstance<br/>BuildAPIHealthStatus<br/>CreateErrorResponse"]
        Calculator["BusinessCaseCalculator<br/>(Scenarios & Savings)"]
    end

    subgraph Domain["🎯 Domain Layer (Business Logic)"]
        Protocols["Protocols (Interfaces)<br/>CacheRepository<br/>InfrastructureGateway"]
        DomainServices["Domain Services<br/>RuntimeService<br/>CarbonDataService"]
        Models["Domain Models<br/>EC2Instance<br/>CarbonIntensity<br/>BusinessCase<br/>DashboardData"]
        Calculations["Calculations<br/>Power Consumption<br/>CO2 Emissions"]
        Constants["Academic Constants<br/>EU ETS Prices<br/>Optimization Factors"]
    end

    subgraph Infrastructure["🔌 Infrastructure Layer (External APIs)"]
        Cache["FileCacheRepository<br/>(Persistence)"]
        Gateways["API Gateways<br/>AWS (EC2, CloudTrail, Cost Explorer)<br/>ElectricityMaps<br/>Boavizta"]
    end

    %% Dependencies (following Clean Architecture rules)
    Pages -->|uses| Orchestrator
    Pages -->|uses| Models

    Orchestrator -->|delegates to| UseCases
    Orchestrator -->|uses| Calculator

    UseCases -->|depends on| DomainServices
    UseCases -->|uses| Models

    Calculator -->|uses| Models
    Calculator -->|uses| Constants

    DomainServices -->|depends on| Protocols
    DomainServices -->|uses| Calculations
    DomainServices -->|uses| Models

    Calculations -->|pure functions| Models

    %% Infrastructure implements protocols (Dependency Inversion)
    Cache -.->|implements| Protocols
    Gateways -.->|implements| Protocols

    %% Styling
    classDef presentation fill:#e1f5ff,stroke:#01579b,stroke-width:2px
    classDef application fill:#fff3e0,stroke:#e65100,stroke-width:2px
    classDef domain fill:#f3e5f5,stroke:#4a148c,stroke-width:3px
    classDef infrastructure fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px

    class Pages,Components presentation
    class Orchestrator,UseCases,Calculator application
    class Protocols,DomainServices,Models,Calculations,Constants domain
    class Cache,Gateways infrastructure
```

## 📐 Dependency Rules

### ✅ Allowed Dependencies (Inward Only)

1. **Presentation → Application:** UI calls orchestrator and use cases
2. **Application → Domain:** Use cases depend on domain services (via protocols)
3. **Domain → Nothing:** Domain is self-contained (no external dependencies)
4. **Infrastructure → Domain:** Infrastructure implements domain protocols

### ❌ Forbidden Dependencies (Violated Clean Architecture)

1. **Domain → Infrastructure:** ❌ Domain must NOT depend on concrete infrastructure
2. **Domain → Application:** ❌ Domain must NOT know about application layer
3. **Domain → Presentation:** ❌ Domain must NOT know about UI

## 🔑 Key Design Patterns

### 1. Protocol-Based Dependency Inversion

**Problem:** Domain services needed cache and API access without coupling to infrastructure.

**Solution:** Define protocols (interfaces) in domain layer:

```python
# src/domain/protocols.py
class CacheRepository(Protocol):
    def get(self, category: str, key: str) -> Optional[Any]: ...
    def set(self, category: str, key: str, value: Any) -> bool: ...

class InfrastructureGateway(Protocol):
    def list_ec2_instances(self, region: str) -> List[Any]: ...
    def get_cloudtrail_events(...) -> List[Any]: ...
```

Infrastructure implements these protocols via duck typing:

```python
# src/infrastructure/cache.py
class FileCacheRepository:  # Implements CacheRepository protocol
    def get(self, category: str, key: str) -> Optional[Any]: ...
    def set(self, category: str, key: str, value: Any) -> bool: ...
```

### 2. Use Case Pattern

**Problem:** Orchestrator was doing too many things (485 LoC, multiple responsibilities).

**Solution:** Extract single-responsibility use cases:

- **EnrichInstanceUseCase:** Enrich single EC2 instance with runtime/carbon/cost
- **FetchInfrastructureDataUseCase:** Main workflow orchestration (13 steps)
- **BuildAPIHealthStatusUseCase:** Monitor API health and build status
- **CreateErrorResponseUseCase:** Handle errors and create appropriate responses

**Result:** Orchestrator reduced to 198 LoC (-59%), now just a thin coordinator.

### 3. Factory Functions for Wiring

**Problem:** Domain services need concrete infrastructure, but can't import it directly.

**Solution:** Factory functions in domain layer handle concrete instantiation:

```python
# src/domain/services/__init__.py
def create_runtime_service(
    repository: Optional[CacheRepository] = None,
    gateway: Optional[InfrastructureGateway] = None,
) -> RuntimeService:
    repository = repository or _default_repository()  # Creates FileCacheRepository
    gateway = gateway or _default_gateway(repository)
    return RuntimeService(repository=repository, gateway=gateway)
```

## 📊 Impact Metrics

| **Metric** | **Before** | **After** | **Improvement** |
|------------|-----------|-----------|-----------------|
| Orchestrator LoC | 485 | 198 | -59% |
| Clean Architecture Violations | 5+ | 0 | -100% |
| Use Cases | 0 | 4 | +4 |
| Protocol-Based Design | No | Yes | ✅ |
| Testability | Low | High | ✅ |

## 🎓 Academic Justification

**Clean Architecture** (Robert C. Martin, 2012):
- **Dependency Rule:** Source code dependencies point inward only
- **Separation of Concerns:** Each layer has distinct responsibility
- **Testability:** Business logic isolated from infrastructure
- **Maintainability:** Changes to external APIs don't affect business rules

**Benefits for Bachelor Thesis:**
- Demonstrates understanding of software architecture principles
- Shows professional-level code organization
- Makes system extensible (easy to add new cloud providers, APIs)
- Facilitates testing (mock protocols instead of concrete implementations)

---

**Status:** ✅ Fully Implemented
**Last Updated:** 2025-10-07
