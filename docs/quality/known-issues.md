# Known Issues & Current Limitations

This document tracks known limitations, issues, and workarounds for the Carbon-Aware FinOps Dashboard prototype.

## Purpose

As an academic prototype, this system has documented limitations that are acceptable for research purposes but would need addressing in a production deployment.

---

## 1. Current Limitations

### 1.1 AWS Integration

- **CloudTrail delay:** Events have ~15-minute delay in availability
- **Cost Explorer updates:** Data updates daily, not real-time
- **Multi-region support:** Limited to eu-central-1 implementation
- **SSO token refresh:** Requires manual re-authentication
- **Permission requirements:** Needs AWSCostExplorerReadOnlyAccess policy

**Impact:** Real-time cost tracking not possible, runtime calculations have minor lag

---

### 1.2 Carbon Intensity Data

- **Granularity:** ElectricityMaps API has hourly granularity, not minute-level
- **Historical data:** Limited to 48 hours via API
- **No fallback:** API outages result in no data (no-fallback-policy by design)
- **Time alignment:** Coverage depends on data availability from external API
- **Region coverage:** Only supports regions covered by ElectricityMaps

**Impact:** Cannot calculate emissions for periods older than 48h without self-collection

---

### 1.3 Calculations

- **Power model:** Uses simplified linear scaling (30% idle, 70% variable)
- **CPU-only:** Doesn't account for memory, disk, network I/O
- **Grid average:** Carbon intensity assumes grid average, not marginal emissions
- **Operational only:** No embodied emissions in calculations
- **Projection assumption:** Monthly projections assume 30-day pattern repetition

**Impact:** Power consumption accuracy ~85-90%, best for CPU-intensive workloads

---

### 1.4 Dashboard Performance

- **Cold cache:** Initial load can take 10-15 seconds with empty cache
- **Large fleets:** Instance counts >50 may slow down processing
- **Full refresh:** Streamlit refresh triggers full re-computation
- **No background workers:** No incremental updates or async processing
- **Memory usage:** All instance data held in memory during processing

**Impact:** User experience degrades with large infrastructure

---

### 1.5 Testing

- **Live credentials:** Integration tests require active AWS credentials
- **Edge case coverage:** Some scenarios not covered (API rate limiting, partial data)
- **Mock limitations:** Test data may not reflect all real-world scenarios
- **No load testing:** Performance under high load not validated
- **Single-region tests:** Multi-region scenarios not tested

**Impact:** Some edge cases may cause unexpected behavior in production

---

## 2. Known Bugs

**None currently identified** (but likely exist in edge cases)

**Reporting:** Please report bugs via GitHub issues or thesis feedback channels

---

## 3. Workarounds

### SSO Token Expired

**Problem:** Dashboard fails with authentication error

**Solution:**
```bash
aws sso login --profile your-profile
```

Then restart dashboard.

---

### Missing Cost Data

**Problem:** Cost Explorer shows no data

**Solution:**
1. Verify IAM permissions include `AWSCostExplorerReadOnlyAccess`
2. Enable Cost Explorer in AWS Console (Billing → Cost Explorer → Enable)
3. Wait 24h for first data to appear

---

### Slow Dashboard Load

**Problem:** Dashboard takes >30 seconds to load

**Solution:**
1. Use cache (default behavior): `make dashboard`
2. Check `.cache/` directory exists and is writable
3. Reduce instance count for testing (<20 instances recommended)

---

### ElectricityMaps API Quota Exceeded

**Problem:** Carbon intensity data unavailable

**Solution:**
1. Check API key validity in `.env` file
2. Verify API quota not exceeded (free tier: 50 requests/day)
3. Increase cache TTL to reduce API calls

---

### CloudTrail Events Missing

**Problem:** Runtime hours show as "Not available"

**Solution:**
1. Verify CloudTrail is enabled in AWS account
2. Check trail logs region-specific instances
3. Ensure trail retention ≥30 days
4. Wait 15 minutes after instance state changes

---

## 4. Academic Prototype Limitations

These limitations are acceptable for the thesis scope:

- **Small-scale validation:** Tested with 4 AWS instances (t3.micro to t3.large)
- **Single-region focus:** eu-central-1 only, German grid carbon intensity
- **Single cloud provider:** AWS only (Azure, GCP not supported)
- **No production hardening:** No high-availability, no failover, no scaling
- **Development environment:** Optimized for local development, not deployment
- **No security audit:** Security best practices not fully implemented
- **Limited error handling:** Some edge cases may result in crashes
- **No monitoring:** No application performance monitoring (APM) integration

**Thesis Context:** These limitations are documented and acceptable for demonstrating the integrated FinOps + Carbon monitoring concept.

---

## 5. Design Decisions (Not Bugs)

These are intentional design choices:

### No-Fallback Policy

**Decision:** System shows `None` or warnings when API data unavailable

**Rationale:** Maintains scientific integrity by not generating synthetic data

**Impact:** Dashboard may show incomplete data during API outages

---

### 30-Day CloudTrail Lookback

**Decision:** Runtime calculations use 30-day window, not longer

**Rationale:** Balance between accuracy and API cost/performance

**Impact:** Monthly costs based on last 30 days, not calendar month

---

### Single-Value CPU Average

**Decision:** CPU utilization uses 24h average, not real-time

**Rationale:** Aligns with CloudWatch data availability and cache strategy

**Impact:** Short-term CPU spikes may not be reflected in power calculations

---

## 6. Related Documentation

- [Future Work](../research/future-work.md) - Planned improvements and research extensions
- [Test Coverage Report](test-coverage-report.md) - Test quality and coverage metrics
- [Validation Results](../research/validation-results.md) - Accuracy assessment and limitations
- [24h Precise Calculation](../methodology/co2_calculation_24h_precise.md) - Methodology limitations
- [System Architecture](../architecture/system-architecture.md) - Architectural constraints

---

**Last Updated:** 2025-10-19
**Maintained By:** Bachelor Thesis Project Team
