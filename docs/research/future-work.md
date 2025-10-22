# Future Work & Research Extensions

This document outlines potential extensions and improvements for the Carbon-Aware FinOps Dashboard, structured as future research directions for the Bachelor thesis.

## Overview

The current implementation provides a functional prototype with 24-hour precise CO2 calculations and dual-method comparison. This document describes enhancements that would further improve accuracy, usability, and research value.

## 1. Long-Term CO2 Calculation (30-Day Exact)

### Current State
- **24h precise calculation** with hourly granularity
- **Monthly projection:** `daily_co2 × 30`
- Documented as projection in UI

### Enhancement: Exact Monthly Totals

**Problem:** Monthly projection assumes daily pattern repeats for 30 days, which may not be accurate for variable workloads.

**Solution:** Store daily CO2 calculations and accumulate over 30 days.

#### Implementation Approach

**Daily Storage Pattern:**
```json
{
  "instance_id": "i-abc123",
  "daily_calculations": {
    "2025-10-18": {
      "co2_kg": 0.0654,
      "hours_running": 24,
      "data_quality": "high",
      "calculation_method": "hourly_24h_precise"
    },
    "2025-10-17": {
      "co2_kg": 0.0621,
      "hours_running": 24,
      "data_quality": "high",
      "calculation_method": "hourly_24h_precise"
    },
    ...
    // Keep last 30 days
  }
}
```

**Storage Location:** `.cache/co2_daily/{instance_id}_monthly.json`

**Monthly Total Calculation (after 30 days):**
```python
def calculate_exact_monthly_co2(instance_id: str) -> float:
    """
    Calculate exact monthly CO2 by summing daily calculations.

    Falls back to projection if <30 days of data available.
    """
    daily_data = load_daily_calculations(instance_id)

    if len(daily_data) >= 30:
        # Exact calculation
        return sum(day["co2_kg"] for day in daily_data.values())
    else:
        # Projection (current behavior)
        avg_daily = sum(day["co2_kg"] for day in daily_data.values()) / len(daily_data)
        return avg_daily * 30
```

#### Implementation Tasks

1. **Add daily storage mechanism** (1h)
   - Create `DailyCO2Storage` class
   - Save after each calculation
   - Automatic rotation (keep 30 days)

2. **Update calculation logic** (30min)
   - Check if 30 days available
   - Use sum vs. projection
   - Add indicator to UI

3. **Migration strategy** (30min)
   - Backward compatible
   - Gradually builds up to 30 days
   - Clear UI messaging during build-up

#### Timeline & Effort

**Effort:** 3-4 hours

**Timeline:**
- Day 1: 1 day of data
- Day 7: 7 days → projection based on 7-day average
- Day 30: **Full 30 days → exact monthly total**

#### Benefits

- 100% accuracy for monthly calculations (after 30-day build-up)
- Historical trend analysis (track CO2 over months)
- Workload pattern detection (identify variations)
- No projection assumptions needed

---

## 2. Improved Power Consumption Models

### Current State
- **Linear CPU scaling:** `Power = Base × (0.3 + 0.7 × CPU/100)`
- **Accuracy:** ~85-90% for CPU-intensive workloads
- **Limitations:** Ignores network, disk, memory

### Enhancement: Multi-Factor Power Models

**Approach:**
```python
Power = f(CPU, Network_IO, Disk_IO, Memory, Temperature)
```

#### Data Sources

1. **SPEC Power Benchmarks**
   - Industry-standard server measurements
   - Per-instance-type profiles

2. **Manufacturer Datasheets**
   - Dell, HP, AWS-published specs
   - Idle vs. peak power ranges

3. **In-Situ Measurements** (if available)
   - AWS Cost & Usage Reports (power estimates)
   - Third-party monitoring tools

#### Implementation

```python
def calculate_multifactor_power(
    instance_type: str,
    cpu_percent: float,
    network_mbps: float,
    disk_iops: float,
    memory_percent: float
) -> float:
    """
    Multi-factor power calculation.

    Coefficients derived from SPEC Power and manufacturer data.
    """
    base = get_base_power(instance_type)

    # Component contributions (example coefficients)
    cpu_power = base * 0.5 * (cpu_percent / 100)
    network_power = 0.1 * network_mbps / 1000  # W per Gbps
    disk_power = 0.01 * disk_iops / 1000       # W per 1000 IOPS
    memory_power = base * 0.1 * (memory_percent / 100)

    return base * 0.3 + cpu_power + network_power + disk_power + memory_power
```

#### Challenges

- **Data availability:** CloudWatch Network/Disk metrics need separate queries
- **Model complexity:** More parameters = harder to validate
- **Computation cost:** More API calls per instance

#### Effort

**Research:** 10-15 hours (literature review, data collection)
**Implementation:** 5-8 hours
**Validation:** 5-10 hours (compare with actual measurements)

**Total:** 20-30 hours

#### Benefits

- ~95% accuracy (vs. ~85% current)
- Workload-specific models (web server vs. database vs. compute)
- Better I/O-bound workload accuracy

---

## 3. Predictive Carbon-Aware Scheduling

### Current State
- **Reactive:** Calculates CO2 after the fact
- **Analysis:** Identifies when CO2 was high/low

### Enhancement: Proactive Workload Optimization

#### Use Case

**Scenario:** Batch job runs 12:00-14:00 daily
- Current carbon intensity: 420 g/kWh (high)
- Low-carbon window: 02:00-04:00 (230 g/kWh)
- **Potential savings:** 45% CO2 reduction

#### Features

1. **Pattern Analysis**
   ```python
   def analyze_carbon_patterns(history_30d: List[Dict]) -> Dict:
       """
       Identify recurring low-carbon windows.

       Returns:
           - best_hourly_slot: Hour with lowest average carbon
           - best_weekly_pattern: Day + hour combination
           - savings_potential: Estimated CO2 reduction
       """
   ```

2. **Scheduling Recommendations**
   ```
   Current Schedule: Mon-Fri 12:00-14:00
   Recommended: Mon-Fri 02:00-04:00

   Savings:
   - CO2: 45% reduction (420g → 230g avg)
   - Cost: Potentially lower (off-peak hours)
   ```

3. **Integration Points**
   - AWS Systems Manager (SSM)
   - Lambda scheduled events
   - EC2 Instance Scheduler

#### Implementation

**Phase 1: Analysis Dashboard** (3-4h)
- Show low-carbon windows
- Display potential savings
- Recommend shift times

**Phase 2: API Integration** (5-8h)
- SSM Document creation
- Lambda function triggers
- CloudWatch Events integration

**Phase 3: Automation** (10-15h)
- Auto-scheduling for tagged instances
- Dry-run mode
- Rollback capability

**Total Effort:** 18-27 hours

#### Benefits

- Actionable insights (not just reporting)
- CO2 reduction without infrastructure changes
- Cost savings (off-peak hours often cheaper)
- Competitive advantage (ESG reporting)

---

## 4. Historical Carbon Intensity Storage (Long-Term)

### Current State
- **ElectricityMaps:** 24-48h history only
- **No long-term storage**

### Enhancement: Self-Hosted Carbon History

#### Approach

**Hourly Collection:**
```python
# Cron job: Run every hour
0 * * * * python collect_carbon_snapshot.py
```

**Storage:**
```json
// .cache/carbon_collection/eu-central-1_longterm.json
[
  {
    "hour_key": "2025-10-18T10:00:00+00:00",
    "carbonIntensity": 380,
    "source": "electricitymap",
    "collected_at": "2025-10-18T10:05:00+00:00"
  },
  ...
  // Keep 90 days = 2160 entries (~200 KB)
]
```

#### Implementation

**Enable Feature:**
```bash
# .env
ENABLE_HOURLY_CARBON_COLLECTION=true
```

**Code Changes:**
1. Uncomment `store_hourly_snapshot()` call in fetch workflow
2. Extend retention from 24h to 720h (30 days) or 2160h (90 days)
3. Add background job (systemd timer or cron)

**Effort:** 2-3 hours (feature already 90% implemented!)

#### Benefits

- Independent from API limits
- 30-90 day history available
- Enables exact monthly CO2 calculation
- Pattern analysis over longer periods

---

## 5. Multi-Region Support

### Current State
- **Single region:** eu-central-1 (hardcoded)
- **Single carbon zone:** DE (Germany)

### Enhancement: Multi-Region Dashboard

#### Features

1. **Region Selector**
   ```python
   regions = ["eu-central-1", "us-east-1", "ap-southeast-1"]
   selected_region = st.selectbox("Select Region", regions)
   ```

2. **Carbon Zone Mapping**
   ```python
   REGION_TO_ZONE = {
       "eu-central-1": "DE",
       "us-east-1": "US-NY",
       "ap-southeast-1": "SG"
   }
   ```

3. **Aggregated View**
   - Total CO2 across all regions
   - Regional comparison
   - Migration recommendations (high-carbon → low-carbon region)

#### Implementation

**Phase 1: Data Model** (2-3h)
- Add region parameter to all functions
- Update cache keys to include region

**Phase 2: UI Updates** (2-3h)
- Region selector
- Multi-region aggregation
- Comparison charts

**Phase 3: Testing** (1-2h)
- Multiple regions with test data
- Cache isolation verification

**Total Effort:** 5-8 hours

#### Benefits

- Global infrastructure visibility
- Regional CO2 comparison
- Migration planning (move workloads to low-carbon regions)

---

## 6. Real-Time Alerting & Notifications

### Current State
- **Passive reporting:** User must check dashboard
- **No alerts** for high-carbon periods

### Enhancement: Proactive Notifications

#### Alert Types

1. **High Carbon Alert**
   ```
   High Carbon Intensity Alert

   Current: 520 g/kWh (↑ 40% above baseline)
   Running instances: 12
   Estimated excess CO2: 2.3 kg/day

   Recommendation: Consider stopping non-critical workloads
   ```

2. **Low Carbon Opportunity**
   ```
   Low Carbon Window Detected

   Current: 180 g/kWh (↓ 50% below average)
   Duration: Expected 2-4 hours

   Recommendation: Good time for batch jobs
   ```

3. **Budget Alert**
   ```
   CO2 Budget Alert

   Monthly CO2: 45.2 kg (90% of 50 kg budget)
   Days remaining: 5

   Recommendation: Review instance usage
   ```

#### Delivery Channels

- Email (AWS SES)
- Slack webhook
- SMS (AWS SNS)
- Dashboard notification banner

#### Implementation

**Effort:** 8-12 hours

**Components:**
- Alert rule engine
- Notification service
- User preferences (threshold configuration)

#### Benefits

- Proactive carbon management
- Prevent budget overruns
- Opportunity detection (low-carbon windows)

---

## Priority Ranking

For **Bachelor Thesis Context:**

| Priority | Enhancement | Effort | Impact | Timeline |
|----------|-------------|--------|--------|----------|
| **1** | Long-Term CO2 Calculation (30d exact) | 3-4h | High | Ready to implement |
| **2** | Historical Carbon Storage | 2-3h | High | 90% complete |
| **3** | Multi-Region Support | 5-8h | Medium | Post-thesis |
| 4 | Predictive Scheduling | 18-27h | High | Future research |
| 5 | Improved Power Models | 20-30h | Medium | Future research |
| 6 | Real-Time Alerting | 8-12h | Medium | Product feature |

**Recommendation for Thesis:**
- Document #1 and #2 as "readily implementable"
- Describe #3-#6 as "future research directions"
- Focus thesis on the **24h precise calculation** (already implemented)

---

## Related Documentation

- [24h Precise Calculation](../methodology/co2_calculation_24h_precise.md) - Current implementation
- [Thesis Documentation](thesis-documentation.md) - Research context
- [Validation Results](validation-results.md) - Current accuracy metrics
- [Known Issues](../quality/known-issues.md) - Current limitations
