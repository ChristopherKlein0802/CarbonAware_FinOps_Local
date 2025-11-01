# Bachelor Thesis Documentation: Carbon-Aware FinOps Integration

## 1. Research Foundation

**Research Question:** How can an integrated monitoring system be developed that simultaneously tracks costs and CO₂ emissions of cloud infrastructures, and what advantages does this approach offer compared to existing separate solutions?

**Motivation:** German SMEs need cost-effective tools that address both FinOps and sustainability requirements while providing CSRD-compliant emission data [7], [10], [11].

## 2. Literature Review

### 2.1 Carbon Footprint in the Cloud
The concepts of energy proportional computing and server-side performance models form the foundation for the linear power scaling used in this work [1], [2]. Current analyses of data center energy consumption extend this basis [3]. Emission intensities follow standards from international organizations (IEA, EPA) and the Software Carbon Intensity Framework from the Green Software Foundation [4]–[6].

### 2.2 FinOps and Cost Optimization
FinOps studies examine the effects of right-sizing, load shifting, and transparency measures [7]–[9]. Market analyses highlight the need for integrated tools for organizations with limited budgets.

### 2.3 Regional and Regulatory Context
Cloud adoption and digitalization in the German SME sector are extensively documented [10], [11], [19]. EU initiatives like "Fit for 55" tighten reporting requirements [12]. Energy market studies (Agora Energiewende, Fraunhofer ISE, BDEW) provide regional parameters for the model [16]–[18].

### 2.4 CloudTrail for Environmental Metrics
CloudTrail is primarily used for compliance [13]. This work examines its applicability for precise runtime measurement and builds on guidelines for sustainable software development [14], [15], [20].

## 3. Methodology (Design Science Research)

1. **Problem Identification:** Analysis of existing FinOps and carbon tools using an evaluation matrix to identify integration gaps.

2. **Data Integration:** ElectricityMaps (carbon intensity), Boavizta (hardware models), AWS Cost Explorer/Pricing (costs), CloudTrail (runtime), and CloudWatch (CPU utilization) are combined through the data orchestrator.

3. **No-Fallback Policy:** API failures are transparently reported; no synthetic replacement values are used.

4. **Calculation Models:**
   - CO₂ = Power (kW) × Intensity (g/kWh) × Runtime (h) / 1000 [4], [6]
   - Power values based on the 30/70 model for server load [1], [2]
   - Business factors use conservative literature values (15–25% costs, 15–35% CO₂) [7], [8], [15]

5. **Uncertainties:** Dashboard responses include metadata on sources, measurement intervals, and uncertainties (±5% carbon, ±10% power, ±2% costs, ±15% scenarios).

## 4. Ethical and Academic Considerations

- **Privacy:** Only infrastructure metrics are processed, no personal data.
- **Transparency:** Source code, configuration, and reproducible scripts (Makefile, requirements-frozen.txt) enable peer review.
- **Limitations:** Four-instance test environment; validation with production workloads remains future work.

## 5. Regional Focus: German Power Grid

- **Carbon Intensities:** 250–550 g CO₂/kWh for Germany [16], [17]
- **Temporal Variations:** Solar and wind peaks (11:00–15:00 and 02:00–05:00); higher intensities in evenings [16], [17]
- **Costs:** BDEW analyses support economic evaluation [18]

## 6. Validation Status

- **Test Environment:** Four AWS m6a.large instances (non-burstable) with varying CPU utilization levels to validate the power consumption model:
  - `cpu-40pct`: Low-intensity baseline workload (40% CPU, 24/7)
  - `cpu-60pct`: Medium-intensity workload (60% CPU, 24/7)
  - `cpu-80pct`: High-intensity compute workload (80% CPU, 24/7)
  - `cpu-variable`: Fluctuating workload pattern (30-70% CPU alternating, 24/7)
- **Focus:** Validating the correlation between CPU utilization, power consumption, and CO₂ emissions across different grid carbon intensities
- **Costs & Emissions:** Currently literature-based savings potentials; empirical confirmation requires production CloudTrail and Cost Explorer data
- **Accuracy:** Without complete CloudTrail data, the validation factor remains theory-based
- **Note:** Instances run continuously (24/7) to ensure consistent measurement data. Scheduling optimization potentials (office-hours, carbon-aware timing) are demonstrated conceptually based on the collected metrics

**Validation Metrics:**
- **CloudTrail Coverage:** Measures data quality through percentage of instances with complete runtime data (target: ≥90%)
- **Validation Factor:** Compares calculated costs (CloudTrail + Pricing API) with AWS Cost Explorer for plausibility check

## 7. Future Work

1. Regular evaluation of production CloudTrail events
2. Build measurement dataset with documented experiments
3. Expand automated integration tests for end-to-end scenarios

## 8. References

All citations refer to the bibliography in `docs/research/references.md`.
