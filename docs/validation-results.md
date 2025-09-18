# Validation Results: Carbon-Aware FinOps Prototype

## 1. Integration Test Overview
| Date | Command | Artefacts | Notes |
|------|---------|-----------|-------|
| 2025-09-18 | `make test-integration` | `artifacts/integration/20250918T145619/` | Live run with ElectricityMaps + AWS APIs |

Required credentials: `AWS_PROFILE=carbon-finops-sandbox`, `ELECTRICITYMAP_API_KEY`.

## 2. Key Metrics from Artefacts
| Metric | Value | Source |
|--------|-------|--------|
| Instances processed | 4 | `metadata.json` |
| Carbon intensity (g CO₂/kWh) | 78.0 | `dashboard_data.json → carbon_intensity.value` |
| Total monthly cost (EUR) | 0.74 | `dashboard_data.json → total_cost_eur` |
| Total monthly CO₂ (kg) | 0.004 | `dashboard_data.json → total_co2_kg` |
| Runtime data availability | 4/4 instances with CloudTrail runtime | `dashboard_data.json → instances[*].runtime_hours` |

## 3. Interpretation
- CloudTrail runtime events were present for all four test instances, enabling measured runtime hours rather than estimates.
- ElectricityMaps returned a valid carbon intensity for `eu-central-1` (76 g CO₂/kWh) during the run.
- The small total cost reflects the limited runtime during the measurement window; values serve as proof of data flow rather than extrapolated SME scenarios.

## 4. Comparison with Literature Expectations
| Aspect | Literature reference | Observation |
|--------|----------------------|-------------|
| Runtime accuracy | Target ±5 % once sufficient CloudTrail data collected ([13]) | Runtime recorded, but no longitudinal evaluation yet |
| Cost optimisation potential | 15–25 % for office-hours scheduling ([7]) | Not assessed in this run; business-case logic remains literature-derived |
| Carbon reduction potential | 15–35 % through temporal shifting ([6], [15]) | Requires scenario execution; not part of this measurement |

## 5. Limitations
- Single data point; no longitudinal comparison.
- Hardware power models and cost estimates rely on literature-derived assumptions pending empirical calibration.
- Artefacts are stored locally; to support peer review, include them (or anonymised extracts) in the thesis appendix.

## 6. Next Steps
1. Schedule repeated integration runs (e.g., daily for one week) to observe carbon/cost variance.
2. Capture scenario-based experiments (e.g., deliberate shutdowns) to quantify optimisation effects.
3. Link artefacts in the written thesis and document processing scripts for external replication.

## 7. References
Literature citations correspond to the numbering in `docs/references.md`.
