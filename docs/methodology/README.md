# 🔬 Research Methodology Documentation

This directory contains documentation about the research methodology, data collection, and calculation approaches used in this Bachelor thesis project.

## 📁 Contents

- [**calculations.md**](calculations.md) - Scientific formulas and calculation methodology
- [**cloudtrail-methodology.md**](cloudtrail-methodology.md) - Precision runtime tracking using AWS CloudTrail
- [**cost-explorer-analysis.md**](cost-explorer-analysis.md) - Cost data collection and analysis approach

## 🎯 Purpose

The methodology documentation explains:

- **Scientific Foundation:** Academic sources and formulas (IEA, Barroso & Hölzle, McKinsey)
- **Data Collection:** How runtime, carbon intensity, and cost data are collected
- **Calculation Logic:** Power consumption models, CO2 emissions formulas
- **Validation Approach:** How results are validated against literature

## 🧪 Key Methodologies

### Carbon Intensity Tracking
- **Source:** ElectricityMaps API (real-time grid data)
- **Validation:** Cross-referenced with national grid reports

### Runtime Tracking
- **Source:** AWS CloudTrail (start/stop events)
- **Precision:** Minute-level accuracy for EC2 instances

### Power Consumption Model
- **Model:** Linear scaling between idle (30%) and peak (100%)
- **Source:** Barroso & Hölzle (2007), SPECpower benchmarks

## 🔗 Related Documentation

- [Research & Literature (docs/research/)](../research/) - Academic sources and references
- [Domain Calculations (src/domain/calculations.py)](../../src/domain/calculations.py) - Implementation code
- [Test Coverage (docs/development/test-coverage-report.md)](../development/test-coverage-report.md) - Validation tests

---

**For thesis reviewers:** Start with [calculations.md](calculations.md) for the scientific foundation.
