# Carbon-Aware FinOps Tool – Bachelor Thesis

[![Tests](https://img.shields.io/badge/tests-79%2F79%20passing-brightgreen)]()
[![Architecture](https://img.shields.io/badge/architecture-Clean%20Architecture-blue)]()
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)]()

## Project Overview

Integrated monitoring system for cloud costs and CO₂ emissions, focused on German SMEs. Combines real-time power grid metrics, AWS runtime data, and FinOps principles using a Design Science Research approach.

**Key Features:**
- 🌍 **Real-time Carbon Tracking**: ElectricityMaps integration for German power grid
- 💰 **Cost & Carbon Integration**: Combined tracking instead of separate tools
- 📊 **Business Case Calculator**: Savings estimation based on McKinsey/MIT research
- 🏛️ **CSRD-Ready**: Scope 2/3 reporting for German compliance
- ⚡ **CloudTrail Precision**: Minute-level runtime tracking for accurate calculations
- 📅 **Flexible Time Windows**: Analyze 1-day, 7-day, or 30-day periods (NEW in v2.0.0)
- 🔄 **Dual Calculation Methods**: Compare Hourly-Precise vs. Average-Based CO₂ calculations (NEW in v2.0.0)

## What's New in v2.0.0 - Flexible Time Windows

The latest release introduces **flexible time window analysis**, allowing you to analyze your infrastructure over different periods:

### 🎯 Key Improvements

**Period Selection**
- Choose from 1-day, 7-day, or 30-day analysis periods
- Dynamic labels throughout UI adapt to selected period
- Period-specific caching prevents data contamination

**Dual Calculation Methods**
- **Hourly-Precise**: Scales 24h ElectricityMaps data to selected period
- **Average-Based**: Uses full period CloudTrail runtime
- Side-by-side comparison reveals workload patterns

**Enhanced UI**
- Period selector in sidebar
- Dynamic metric labels ("7-day Costs" vs "Monthly Costs")
- Comparison section shows method differences
- All charts and tables adapt to selected period

**Technical Improvements**
- **Period-aligned Cost Explorer queries**: Prevents data contamination from old instances
- **Cache invalidation on period change**: Ensures data consistency across time windows
- **Dynamic UI label system**: Central `get_period_label()` utility for consistency
- **Cost Explorer direct storage**: Stores actual EUR value instead of back-calculation
- **Backward-compatible field access**: Graceful fallbacks during migration period

### 📖 Documentation

- [Migration Guide](docs/migration/field-deprecation.md) - Update existing code
- [Naming Conventions](docs/architecture/naming-conventions.md) - New field names
- [CHANGELOG](CHANGELOG.md) - Full release notes

### ⚠️ Breaking Changes (with Backward Compatibility)

Deprecated fields remain functional but will be removed in v3.0.0:
- `monthly_co2_kg` → `co2_kg_average`
- `monthly_cost_eur` → `cost_eur_average`

See [Migration Guide](docs/migration/field-deprecation.md) for details.

---

## Research Question

"How can an integrated monitoring system be developed that simultaneously tracks costs and CO₂ emissions of cloud infrastructures, and what advantages does this approach offer compared to existing separate solutions?"

## Motivation

84% of companies see cost control as the biggest cloud challenge, while CSRD (from 2024) requires detailed emission reports. German SMEs need to reduce costs and provide reliable emission data, but available tools separate these two dimensions.

## System Architecture

The system follows Clean Architecture principles with clear layer separation:

**Domain Layer** (`src/domain/`)
- Business logic and calculations (CO₂ emissions, power consumption)
- Domain services (runtime, carbon data)
- Protocols for external dependencies

**Application Layer** (`src/application/`)
- Orchestrator for dashboard data
- Business case calculator
- Use cases for specific workflows

**Infrastructure Layer** (`src/infrastructure/`)
- API gateways (AWS, ElectricityMaps, Boavizta)
- Cache repository

**Presentation Layer** (`src/presentation/`)
- Streamlit dashboard with two pages
- Reusable UI components

## Quick Start

```bash
# Clone and setup
git clone <your-repo-url>
cd CarbonAware_FinOps_Local
make setup

# Start dashboard
make dashboard
# Browser: http://localhost:8501

# Run tests
make test
```

## AWS Integration (Optional)

```bash
# Configure AWS SSO
aws configure sso --profile your-profile-name
aws sso login --profile your-profile-name

# Create .env file
cp .env.example .env
# Add ELECTRICITYMAP_API_KEY to .env
```

## Test Coverage
**79/79 Tests passing (100% success rate)**
- 27 Domain Calculations Tests (Power, CO₂, Barroso & Hölzle validation)
- 29 Business Case Calculator Tests (McKinsey/MIT scenarios)
- 12 Core Calculator Tests (CloudTrail accuracy, validation factors)
- 7 Orchestrator Tests (Use case delegation, error handling)
- 4 Constants Tests (Academic values validation)

**Test Quality:**
- ✅ Academic literature references in test docstrings
- ✅ Edge case coverage (None, zero, negative values)
- ✅ Integration tests for full data pipeline
- ✅ Execution time: <3 seconds (fast feedback loop)

Details: [docs/quality/test-coverage-report.md](docs/quality/test-coverage-report.md)

## Documentation

**Main documentation:** [docs/README.md](docs/README.md)

### For thesis reviewers:
- [Thesis Documentation](docs/research/thesis-documentation.md) - Research question, methodology, results
- [Quick Reference](docs/thesis/quick-reference.md) - Defense preparation
- [Test Coverage Report](docs/quality/test-coverage-report.md) - 79 tests, 100% pass rate

### For developers:
- [System Architecture](docs/architecture/system-architecture.md) - Clean Architecture overview
- [Calculation Methodology](docs/methodology/calculations.md) - CO₂ and cost formulas
- [Developer Handbook](docs/user/developer-handbook.md) - Setup and extension guide
- [Naming Conventions](docs/architecture/naming-conventions.md) - Period-based field naming (v2.0.0)
- [Migration Guide](docs/migration/field-deprecation.md) - Upgrade from v1.x to v2.0.0

## Technology Stack

- Python 3.11+
- Streamlit (Dashboard)
- AWS SDK (boto3)
- Pytest (Testing)
- Terraform (Infrastructure)

## Contact & License

**Author:** Christopher Klein
**University:** TH Köln- Technische Informatik
**Supervisor:** Andreas Behrend, Ferenc Domröse

Bachelor Thesis Project 2025. All rights reserved.
