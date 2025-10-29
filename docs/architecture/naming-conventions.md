# Naming Conventions - Flexible Time Windows

**Version:** 2.0.0
**Last Updated:** October 2025

## Overview

This document defines the naming conventions for period-based calculations in the Carbon-Aware FinOps Dashboard. These conventions ensure consistency across the codebase and enable flexible time window analysis.

## Core Principles

1. **Period-Agnostic**: Names should work for any time period (1d, 7d, 30d)
2. **Method-Explicit**: Clearly distinguish between calculation methods
3. **Backward Compatible**: Maintain deprecated fields during migration
4. **Self-Documenting**: Names should be self-explanatory

## Terminology

### Main Terms

#### `period_days`
- **Usage**: Primary term for time window duration
- **Type**: `int`
- **Values**: `1`, `7`, `30`
- **Scope**: Parameters, fields, configuration

**Examples:**
```python
period_days: int = 30
analysis_period_days: int = 30
```

**Avoid:**
- `window_days` - less common term
- `lookback_days` - implies historical only
- `days` - too generic

### Calculation Methods

#### Hourly-Precise Method
- **Field Suffix**: `_hourly`
- **Method Name**: `"hourly"`
- **Description**: Calculates CO₂ for each of the last 24 hours individually, then scales to period

**Field Examples:**
```python
co2_kg_hourly: Optional[float] = None
cost_eur_hourly: Optional[float] = None
total_co2_hourly: float = 0.0
total_cost_hourly: float = 0.0
```

**Avoid:**
- `_24h` - not period-agnostic
- `_precise` - redundant with "hourly"
- `_projected` - unclear method
- `_daily` - confusing with 1-day period

#### Average-Based Method
- **Field Suffix**: `_average`
- **Method Name**: `"average"`
- **Description**: Uses total runtime from period with average CPU and current carbon intensity

**Field Examples:**
```python
co2_kg_average: Optional[float] = None
cost_eur_average: Optional[float] = None
total_co2_average: float = 0.0
total_cost_average: float = 0.0
```

**Avoid:**
- `_monthly` - not period-agnostic
- `_30d` - not period-agnostic
- `_actual` - ambiguous meaning
- `_runtime` - unclear method

## Function Naming

### General Guidelines

1. Use generic terms, not period-specific
2. Include `period_days` parameter explicitly
3. Document period behavior in docstring

### Examples

#### ✅ CORRECT

```python
def get_costs(region: str, period_days: int = 30) -> Optional[AWSCostData]:
    """Get cost data for specified period."""
    pass

def enrich_instance(
    instance: Dict,
    carbon_intensity: float,
    period_days: int = 30
) -> Optional[EC2Instance]:
    """Enrich instance with period-based calculations."""
    pass

def calculate_co2_emissions(
    power_watts: float,
    carbon_intensity: float,
    runtime_hours: float
) -> float:
    """Calculate CO₂ emissions (period-agnostic)."""
    pass
```

#### ❌ INCORRECT

```python
def get_monthly_costs(region: str) -> Optional[AWSCostData]:
    """❌ 'monthly' is period-specific"""
    pass

def get_30d_costs(region: str) -> Optional[AWSCostData]:
    """❌ '30d' is hardcoded"""
    pass

def calculate_monthly_co2(instance: Dict) -> float:
    """❌ 'monthly' not flexible"""
    pass
```

## Field Naming Patterns

### Instance-Level Fields

#### Pattern: `{metric}_{unit}_{method}`

```python
# CO₂ Emissions
co2_kg_hourly: Optional[float]      # Hourly-Precise method
co2_kg_average: Optional[float]     # Average-Based method

# Costs
cost_eur_hourly: Optional[float]    # Hourly-Precise method
cost_eur_average: Optional[float]   # Average-Based method

# Period metadata
period_days: int = 30
```

### Aggregate-Level Fields

#### Pattern: `total_{metric}_{method}`

```python
# Aggregated CO₂
total_co2_hourly: float             # Sum of hourly-precise
total_co2_average: float            # Sum of average-based

# Aggregated Costs
total_cost_hourly: float            # Sum of hourly-precise
total_cost_average: float           # Sum of average-based

# Period metadata
analysis_period_days: int = 30
```

### Metadata Fields

```python
# Calculation method tracking
hourly_precise_count: int = 0       # Instances using hourly method
fallback_count: int = 0             # Instances using average method

# Data quality
data_completeness_24h: Optional[int]  # Hours of data available
coverage_hours: int                   # Valid data hours
```

## UI Labeling

### Dynamic Labels

Use period-aware labels that adapt to the selected time window:

```python
period_days = dashboard_data.analysis_period_days
period_label = f"{period_days}d" if period_days < 30 else "monthly"

# Examples:
# period_days=1  → "1d" or "daily"
# period_days=7  → "7d" or "weekly"
# period_days=30 → "monthly"
```

### Metric Labels

```python
# Cost labels
f"💰 {period_label.title()} Costs"
# → "1d Costs", "7d Costs", "Monthly Costs"

# CO₂ labels
f"🌍 {period_label.title()} Carbon"
# → "1d Carbon", "7d Carbon", "Monthly Carbon"

# Runtime labels
f"Runtime ({period_label})"
# → "Runtime (1d)", "Runtime (7d)", "Runtime (monthly)"
```

### Comparison Labels

```python
# Method comparison
"Hourly-Precise"           # Not "24h Projected"
"Average-Based"            # Not "30d Actual"

# Chart titles
f"CO₂ Emissions - {period_label}"
f"Cost Analysis - {period_label}"
```

## Cache Keys

### Pattern: `{data_type}_{period}d_{region}`

```python
# Cost Explorer cache
f"costs_{period_days}d_{region.replace('-', '_')}"
# Examples:
# - "costs_1d_eu_central_1"
# - "costs_7d_eu_central_1"
# - "costs_30d_eu_central_1"

# CloudTrail cache
f"cloudtrail_{instance_id}_{period_days}d"

# Carbon intensity (always 24h, but period-aware for projections)
f"carbon_intensity_24h_{region}"
```

## Configuration Keys

```python
# ✅ CORRECT
period_days: int = 30
default_period_days: int = 30
analysis_period_days: int = 30

# ❌ AVOID
monthly_period: bool = True          # Not flexible
default_lookback: int = 30           # Unclear purpose
window_size: int = 30                # Ambiguous unit
```

## Code Comments

### Calculation Method Comments

```python
# ✅ CORRECT
# Hourly-Precise: Scale 24h data to period
co2_kg_hourly = daily_co2_kg * period_days

# Average-Based: Use full period runtime
co2_kg_average = calculate_co2_emissions(
    power_watts, carbon_intensity, runtime_hours
)

# ❌ AVOID
# 24h projected (not period-agnostic)
# 30d actual (hardcoded period)
# Monthly calculation (period-specific)
```

## Log Messages

### Examples

```python
# ✅ CORRECT
logger.info(f"📊 Starting infrastructure analysis with {period_days}-day period")
logger.info(f"✅ Cost Explorer: ${cost:.2f} over {period_days}d")
logger.info(f"Hourly-Precise: {co2_hourly:.3f} kg ({period_days}d)")

# ❌ AVOID
logger.info("Starting monthly analysis")  # Not flexible
logger.info("24h projection complete")    # Method-specific
```

## Migration Notes

When updating existing code:

1. **Replace period-specific terms**: `monthly` → `period_days`
2. **Add method suffixes**: `co2_kg` → `co2_kg_average`
3. **Update function names**: `get_monthly_costs` → `get_costs`
4. **Make labels dynamic**: `"Monthly Cost"` → `f"{period_label} Cost"`

## Consistency Checklist

Before committing code, verify:

- [ ] No hardcoded "monthly", "30d", "24h" in variable names
- [ ] All period-based functions accept `period_days` parameter
- [ ] Calculation method clearly indicated (`_hourly` or `_average`)
- [ ] UI labels use dynamic `period_label` variable
- [ ] Cache keys include period: `_{period_days}d_`
- [ ] Log messages include `{period_days}` in output
- [ ] Comments use "Hourly-Precise" and "Average-Based" terminology

## Examples from Codebase

### Good Examples

```python
# src/domain/models.py
@dataclass
class EC2Instance:
    period_days: int = 30
    co2_kg_hourly: Optional[float] = None
    co2_kg_average: Optional[float] = None

# src/infrastructure/gateways/aws.py
def get_costs(self, region: str, period_days: int = 30):
    cache_key = f"costs_{period_days}d_{region}"
    logger.info(f"Fetching costs for {period_days}d period")

# src/presentation/components/metrics.py
period_label = f"{period_days}d" if period_days < 30 else "monthly"
st.metric(f"{period_label.title()} Costs", f"€{cost:.2f}")
```

## Related Documentation

- [Field Deprecation Guide](../migration/field-deprecation.md)
- [Domain Models](./domain-models.md)
- [Calculation Methodology](../methodology/calculations.md)

## Version History

- **v2.0.0** (2025-10): Initial naming conventions for flexible time windows
