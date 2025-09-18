# Integration Testing Plan for Carbon-Aware FinOps

## Objectives
1. Validate the full data pipeline from external APIs to Streamlit dashboard artefacts.
2. Produce reproducible measurement runs with annotated raw data for academic evidence.
3. Detect regressions in caching, calculations, and business case aggregation when real AWS and ElectricityMaps data are used.

## Test Scenarios
| Scenario | Description | Primary Data Sources | Expected Evidence |
|----------|-------------|----------------------|-------------------|
| Baseline Monitoring | Collect a reference snapshot with four EC2 instances (t3.micro–t3.large) | ElectricityMaps, Boavizta, AWS Pricing/CloudTrail/CloudWatch | JSON snapshot + dashboard export + log archive |
| Carbon-Aware Scheduling | Execute workload shift (start/stop instances) and capture before/after metrics | CloudTrail, CloudWatch, ElectricityMaps | Event timeline + runtime deltas + carbon comparison |
| Cost Validation | Compare computed monthly totals with AWS Cost Explorer report | AWS Cost Explorer, Pricing API | Validation factor report, cost breakdown |
| Failure Handling | Trigger API unavailability (mock or throttle) to document NO-FALLBACK behaviour | ElectricityMaps or CloudTrail | Log excerpt + dashboard alert screenshot |

## Data Collection Workflow
1. **Preparation**
   - Enable multi-region CloudTrail with 30-day retention.
   - Configure CloudWatch metrics and ensure Boavizta/ElectricityMaps credentials are available.
   - Define `.env.integration` with dedicated API keys and AWS profile (`AWS_PROFILE=carbon-finops-integration`).

2. **Execution Script**
   - Das Repository stellt `tests/integration/test_pipeline.py` bereit. Der Test führt folgende Schritte aus:
     1. Ausführung von `DataProcessor.get_infrastructure_data()` mit Live-Credentials.
     2. Serialisierung der Dataclasses nach `artifacts/integration/<timestamp>/dashboard_data.json`.
     3. Ablage einer Zusammenfassung (`metadata.json`) mit API-Status, Carbon-Verfügbarkeit und Disclaimern.
     4. Optionale Erweiterung: Rohdaten (z. B. CloudWatch-Metriken) ergänzen, sobald hierfür Schnittstellen bereitstehen.

3. **Verification**
   - Compare calculated cost totals against AWS Cost Explorer using tolerance ±2 %.
   - Ensure runtime hours from CloudTrail align with CloudWatch average CPU windows.
   - Document discrepancies and append to `docs/validation-results.md`.

4. **Repeatability**
   - Nutzung des Makefile-Targets `make test-integration` (aktiviert das virtuelle Environment und führt den markierten Test aus).
   - Artefakte lokal archivieren; Rohdaten (AWS-Berichte) nicht einchecken, sondern in der Dokumentation referenzieren.

## Tooling Recommendations
- Use `pytest` with markers (`@pytest.mark.integration`) to separate long-running tests.
- Leverage `pytest-recording` or custom thin adapters to snapshot API responses while respecting credential policies.
- Archive artefacts under `artifacts/integration/<date>` with an accompanying manifest (`manifest.json`).

## Documentation Updates
- Extend `docs/validation-results.md` with a section “Integration Test Evidence” summarising each run, date, and key findings.
- Reference the artefact manifest and note any deviations from expected uncertainty ranges.

## Next Steps
1. Implement the integration test runner and artefact schema as outlined above.
2. Schedule periodic execution (e.g., weekly) to monitor drift in carbon intensity and cost correlation.
3. Incorporate the resulting evidence into the thesis appendices and defence materials.
