# Changelog

All notable changes to the Carbon-Aware FinOps Dashboard will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-10-28

### Added - Flexible Time Windows Feature

#### Core Features
- **Period Selection Dropdown** in sidebar with 3 options:
  - Last 24 hours (1 day)
  - Last 7 days (1 week)
  - Last 30 days (1 month, default)
- **Dual Calculation Methods** displayed side-by-side:
  - Hourly-Precise: 24h data scaled to selected period
  - Average-Based: Full period runtime with average CPU
- **Dynamic Labels** throughout UI that adapt to selected period
- **Period-Aware Metrics** across all components

#### Domain Layer
- New field names in `EC2Instance`:
  - `period_days` (replaces hardcoded 30-day assumption)
  - `co2_kg_hourly` and `cost_eur_hourly` (Hourly-Precise method)
  - `co2_kg_average` and `cost_eur_average` (Average-Based method)
- New field names in `DashboardData`:
  - `analysis_period_days` (global period setting)
  - `total_co2_hourly` and `total_cost_hourly` (aggregates)
  - `total_co2_average` and `total_cost_average` (aggregates)
  - `hourly_precise_count` and `fallback_count` (method tracking)
- Updated calculation method names:
  - `"hourly_24h_precise"` → `"hourly"`
  - `"monthly_average"` → `"average"`

#### Infrastructure Layer
- `get_costs()` function replaces `get_monthly_costs()`:
  - Accepts `period_days` parameter (1, 7, or 30)
  - Auto-selects granularity: HOURLY (≤14 days) or DAILY (>14 days)
  - Period-specific cache keys: `costs_{period_days}d_{region}`
- CloudTrail queries now use dynamic date ranges based on selected period
- Cost Explorer validation now uses period-aligned time windows

#### Application Layer
- `FetchInfrastructureDataUseCase` propagates `period_days` through entire data flow
- `EnrichInstanceUseCase` accepts `period_days` parameter
- RuntimeService scales 24h carbon data to selected period
- BusinessCaseCalculator uses average-based totals as baseline

#### UI Layer
- **Sidebar**: Period selection with cache invalidation on change
- **Overview Page**: Dynamic metric labels (`"7-day Costs"` vs `"Monthly Costs"`)
- **Infrastructure Details Page**:
  - Dynamic table column headers (`"Runtime (7d)"`, `"CO₂ (7d avg)"`)
  - Comparison section shows both methods with difference analysis
  - Period-aware projections in hourly analysis charts
- **All Components**: Backward-compatible field access with fallbacks

#### Documentation
- Migration guide for deprecated fields ([docs/migration/field-deprecation.md](docs/migration/field-deprecation.md))
- Naming conventions documentation ([docs/architecture/naming-conventions.md](docs/architecture/naming-conventions.md))
- Updated code comments and docstrings

### Changed

#### Breaking Changes (with Backward Compatibility)
- Function signature: `get_monthly_costs()` → `get_costs(region, period_days=30)`
- Method names: `"hourly_24h_precise"` → `"hourly"`, `"monthly_average"` → `"average"`
- Field names: See migration guide for complete mapping

#### Non-Breaking Changes
- All UI labels now adapt dynamically to selected period
- Cache keys now include period to prevent cross-contamination
- Logging messages include period information for better debugging
- Cost Explorer validation uses period-aligned time windows

### Deprecated

The following fields are deprecated and will be removed in v3.0.0:

#### EC2Instance Fields
- `monthly_co2_kg` → Use `co2_kg_average`
- `monthly_cost_eur` → Use `cost_eur_average`
- `monthly_co2_kg_projected` → Use `co2_kg_hourly`
- `monthly_cost_projected_eur` → Use `cost_eur_hourly`
- `monthly_co2_kg_30d` → Use `co2_kg_average`

#### DashboardData Fields
- `total_cost_eur` → Use `total_cost_average`
- `total_co2_kg` → Use `total_co2_average`
- `total_co2_projected_kg` → Use `total_co2_hourly`
- `total_cost_projected_eur` → Use `total_cost_hourly`
- `total_co2_30d_kg` → Use `total_co2_average`
- `total_cost_30d_eur` → Use `total_cost_average`

See [Field Deprecation Guide](docs/migration/field-deprecation.md) for migration instructions.

### Fixed
- Cost Explorer contamination from old instances resolved by flexible time windows
- Cache invalidation now occurs when period changes
- Cost Explorer granularity selection optimized for period length

### Technical Details

#### Performance Optimizations
- Period-specific cache keys prevent stale data across different time windows
- Cache reuse within same period and TTL window
- Auto-granularity selection reduces API call overhead

#### Architectural Improvements
- Clean separation between Hourly-Precise and Average-Based methods
- Period-agnostic function signatures throughout codebase
- Backward compatibility maintained via field aliasing

#### Testing
- All existing tests updated to use new field names
- New tests for period selection and cache invalidation
- Backward compatibility verified with fallback tests

### Migration Guide

For existing code using deprecated fields:

```python
# Old code (still works, but deprecated)
cost = instance.monthly_cost_eur
co2 = instance.monthly_co2_kg

# New code (recommended)
cost = instance.cost_eur_average
co2 = instance.co2_kg_average

# Migration with fallback (safest)
cost = getattr(instance, "cost_eur_average", instance.monthly_cost_eur)
co2 = getattr(instance, "co2_kg_average", instance.monthly_co2_kg)
```

See full migration guide: [docs/migration/field-deprecation.md](docs/migration/field-deprecation.md)

### Known Issues
- None

### Security
- No security changes in this release

---

## [1.0.0] - 2025-09-01

### Added
- Initial release of Carbon-Aware FinOps Dashboard
- AWS EC2 instance monitoring with CloudTrail runtime tracking
- ElectricityMaps integration for German grid carbon intensity
- Boavizta API for hardware power models
- AWS Cost Explorer integration for cost validation
- Dual-axis cost and carbon visualization
- Business case calculator with optimization scenarios
- CSRD Scope 2/3 compliance reporting
- Academic disclaimers and methodology documentation

### Features
- Real-time carbon intensity tracking
- CloudTrail-based runtime precision (±5% accuracy target)
- CPU-aware power consumption modeling
- Instance-level cost and carbon breakdown
- Hourly CO₂ emissions analysis (24h window)
- System health monitoring
- API status tracking
- Academic prototype disclaimers

### Technical Stack
- Python 3.13+
- Streamlit for UI
- Boto3 for AWS integration
- Plotly for visualizations
- Clean Architecture with domain-driven design
- Comprehensive test coverage

---

## Version Numbering

- **Major version (X.0.0)**: Breaking changes or significant new features
- **Minor version (0.X.0)**: New features, backward compatible
- **Patch version (0.0.X)**: Bug fixes, no new features

## Categories

- **Added**: New features
- **Changed**: Changes in existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security improvements
