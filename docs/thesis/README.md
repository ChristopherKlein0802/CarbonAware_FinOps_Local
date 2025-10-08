# Thesis Defense Preparation

Notes and materials for the bachelor thesis defense.

## Contents

- [**quick-reference.md**](quick-reference.md) - Key points and Q&A for defense

## Defense Preparation

### What to prepare:
- Review the [quick-reference.md](quick-reference.md) document
- Test the dashboard (make sure it runs: `make dashboard`)
- Check AWS SSO login works
- Have the architecture diagram ready
- Know the test coverage numbers

### Main talking points:
1. **Problem**: Cloud carbon emissions are hard to track, FinOps teams need better tools
2. **Solution**: Dashboard that combines AWS runtime data, Boavizta power models, and ElectricityMaps grid intensity
3. **Implementation**: Clean Architecture pattern with 79 unit tests
4. **Results**: Minute-level tracking, business case calculations based on McKinsey/MIT research

## Summary for committee

This bachelor thesis project develops a monitoring system that tracks both costs and carbon emissions for cloud infrastructure. The system uses AWS CloudTrail for precise runtime tracking, Boavizta API for power consumption models, and ElectricityMaps for German grid carbon intensity data.

The implementation uses Clean Architecture with four layers (Domain, Application, Infrastructure, Presentation) and includes 79 unit tests covering the core calculation logic. Business case modeling is based on published research from McKinsey and MIT.

## Project metrics

- **Code:** ~5,500 lines Python source code
- **Tests:** 79 unit tests, 100% pass rate
- **Documentation:** ~3,300 lines markdown
- **Architecture:** 4-layer Clean Architecture
- **APIs integrated:** AWS (CloudTrail, Cost Explorer, Pricing), Boavizta, ElectricityMaps

## Related docs

- [Test Coverage Report](../quality/test-coverage-report.md) - Detailed test analysis
- [System Architecture](../architecture/system-architecture.md) - Architecture overview
- [Research Documentation](../research/thesis-documentation.md) - Academic foundation
