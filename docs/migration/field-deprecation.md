# Field Deprecation Guide

**Version:** 2.0.0 (Flexible Time Windows Feature)
**Date:** October 2025
**Status:** Active Migration Period

## Overview

This guide documents the deprecation of fixed 30-day field names in favor of flexible, period-based naming conventions. The new naming scheme supports dynamic time windows (1d, 7d, 30d) while maintaining backward compatibility.

## Deprecation Timeline

- **v2.0.0** (Current): New field names introduced, deprecated fields maintained
- **v2.1.0** (Planned): Deprecation warnings in logs
- **v3.0.0** (Future): Deprecated fields removed

## Migration Path

### EC2Instance Model

#### Deprecated Fields (DO NOT USE in new code)

```python
# ❌ DEPRECATED - Will be removed in v3.0.0
monthly_co2_kg: Optional[float] = None
monthly_cost_eur: Optional[float] = None
monthly_co2_kg_projected: Optional[float] = None
monthly_cost_projected_eur: Optional[float] = None
monthly_co2_kg_30d: Optional[float] = None
```

#### New Fields (USE in all new code)

```python
# ✅ NEW - Flexible period-based naming
period_days: int = 30

# Hourly-Precise Method (24h data scaled to period)
co2_kg_hourly: Optional[float] = None
cost_eur_hourly: Optional[float] = None

# Average-Based Method (period runtime basis)
co2_kg_average: Optional[float] = None
cost_eur_average: Optional[float] = None
```

### DashboardData Model

#### Deprecated Fields

```python
# ❌ DEPRECATED - Will be removed in v3.0.0
total_cost_eur: float = 0.0
total_co2_kg: float = 0.0
total_co2_projected_kg: float = 0.0
total_cost_projected_eur: float = 0.0
total_co2_30d_kg: float = 0.0
total_cost_30d_eur: float = 0.0
```

#### New Fields

```python
# ✅ NEW - Period-aware aggregations
analysis_period_days: int = 30

# Hourly-Precise Method
total_co2_hourly: float = 0.0
total_cost_hourly: float = 0.0

# Average-Based Method
total_co2_average: float = 0.0
total_cost_average: float = 0.0

# Metadata
hourly_precise_count: int = 0
fallback_count: int = 0
```

## Code Migration Examples

### Example 1: Accessing Instance Costs

**Before (Deprecated):**
```python
cost = instance.monthly_cost_eur
co2 = instance.monthly_co2_kg
```

**After (Recommended):**
```python
# Use average-based as primary metric (most conservative)
cost = instance.cost_eur_average
co2 = instance.co2_kg_average

# Or access hourly-precise for comparison
cost_hourly = instance.cost_eur_hourly
co2_hourly = instance.co2_kg_hourly
```

**Migration with Backward Compatibility:**
```python
# Graceful fallback for existing code
cost = getattr(instance, "cost_eur_average", instance.monthly_cost_eur)
co2 = getattr(instance, "co2_kg_average", instance.monthly_co2_kg)
```

### Example 2: Aggregating Totals

**Before (Deprecated):**
```python
total_cost = sum(i.monthly_cost_eur for i in instances if i.monthly_cost_eur)
total_co2 = sum(i.monthly_co2_kg for i in instances if i.monthly_co2_kg)
```

**After (Recommended):**
```python
# Use average-based totals
total_cost = sum(i.cost_eur_average for i in instances if i.cost_eur_average)
total_co2 = sum(i.co2_kg_average for i in instances if i.co2_kg_average)

# Or access hourly-precise totals
total_cost_hourly = sum(i.cost_eur_hourly for i in instances if i.cost_eur_hourly)
total_co2_hourly = sum(i.co2_kg_hourly for i in instances if i.co2_kg_hourly)
```

**Migration with Backward Compatibility:**
```python
total_cost = sum(
    getattr(i, "cost_eur_average", i.monthly_cost_eur) or 0
    for i in instances
)
```

### Example 3: Using Dashboard Aggregates

**Before (Deprecated):**
```python
total = dashboard_data.total_cost_eur
co2 = dashboard_data.total_co2_kg
```

**After (Recommended):**
```python
# Access period-aware aggregates
period_days = dashboard_data.analysis_period_days
total = dashboard_data.total_cost_average
co2 = dashboard_data.total_co2_average

# Compare with hourly-precise
total_hourly = dashboard_data.total_cost_hourly
co2_hourly = dashboard_data.total_co2_hourly
```

### Example 4: UI Labels

**Before (Deprecated):**
```python
st.metric("Monthly Cost", f"€{cost:.2f}")
st.metric("Monthly CO₂", f"{co2:.2f} kg")
```

**After (Recommended):**
```python
period_days = dashboard_data.analysis_period_days
period_label = f"{period_days}d" if period_days < 30 else "monthly"

st.metric(f"{period_label.title()} Cost", f"€{cost:.2f}")
st.metric(f"{period_label.title()} CO₂", f"{co2:.2f} kg")
```

## Calculation Method Names

### Deprecated Method Names

```python
# ❌ DEPRECATED
co2_calculation_method = "hourly_24h_precise"  # Old name
co2_calculation_method = "monthly_average"      # Old name
```

### New Method Names

```python
# ✅ NEW
co2_calculation_method = "hourly"   # Hourly-Precise method
co2_calculation_method = "average"  # Average-Based method
```

### Migration Example

**Before:**
```python
if instance.co2_calculation_method == "hourly_24h_precise":
    # Use hourly data
    pass
elif instance.co2_calculation_method == "monthly_average":
    # Use average data
    pass
```

**After:**
```python
if instance.co2_calculation_method == "hourly":
    # Use hourly-precise data
    pass
elif instance.co2_calculation_method == "average":
    # Use average-based data
    pass
```

## Function Signatures

### Deprecated Signatures

```python
# ❌ DEPRECATED
def get_monthly_costs(region: str) -> Optional[AWSCostData]:
    pass

def enrich_instance(instance, carbon_intensity: float) -> EC2Instance:
    pass
```

### New Signatures

```python
# ✅ NEW
def get_costs(region: str, period_days: int = 30) -> Optional[AWSCostData]:
    pass

def enrich_instance(
    instance,
    carbon_intensity: float,
    period_days: int = 30
) -> EC2Instance:
    pass
```

## Testing Recommendations

### Unit Tests

Update your tests to use new field names:

```python
def test_instance_cost_calculation():
    instance = create_test_instance()

    # ✅ Use new fields
    assert instance.cost_eur_average > 0
    assert instance.co2_kg_average > 0

    # Also test period awareness
    assert instance.period_days == 7  # or whatever you set
```

### Integration Tests

Test both methods side-by-side:

```python
def test_dual_calculation_methods():
    dashboard = fetch_dashboard_data(period_days=7)

    # Both methods should produce values
    assert dashboard.total_cost_hourly > 0
    assert dashboard.total_cost_average > 0

    # Values should be within reasonable range of each other
    diff_pct = abs(
        (dashboard.total_cost_hourly - dashboard.total_cost_average)
        / dashboard.total_cost_average
    )
    assert diff_pct < 0.5  # Max 50% difference
```

## Backward Compatibility Strategy

All deprecated fields are populated by the domain service with values from the new fields:

```python
# In RuntimeService.enrich_instance()
monthly_co2_kg=co2_kg_average,           # Backward compat
monthly_cost_eur=cost_eur_average,       # Backward compat
co2_kg_average=co2_kg_average,           # New field
cost_eur_average=cost_eur_average,       # New field
```

This ensures that existing code continues to work while allowing gradual migration.

## Breaking Changes in v3.0.0

When deprecated fields are removed in v3.0.0, the following will break:

1. Direct access to `monthly_*` fields
2. Direct access to `total_cost_eur` without checking for new fields
3. Hardcoded "monthly" labels in UI
4. Function calls using old signatures

## Support

For questions about migration:
- Check the [Naming Conventions](../architecture/naming-conventions.md) document
- Review the [CHANGELOG](../../CHANGELOG.md) for version-specific changes
- See example implementations in `src/presentation/pages/infrastructure_details.py`

## Version History

- **v2.0.0** (2025-10): Flexible time windows feature, field deprecation begins
- **v1.0.0** (2025-09): Initial implementation with fixed 30-day periods
