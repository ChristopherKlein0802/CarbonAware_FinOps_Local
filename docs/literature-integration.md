# Literature Integration: Carbon-Aware FinOps

## 1. Overview
This document summarises the sources that inform the design of the Carbon-Aware FinOps prototype and maps each literature strand to concrete implementation decisions. All references correspond to the numbering in `docs/references.md`.

## 2. Cloud Cost Optimisation
- **AWS Well-Architected Framework** emphasises right-sizing, workload scheduling, and accurate monitoring. These recommendations justify the collection of AWS Pricing, Cost Explorer, CloudTrail, and CloudWatch data for visibility and governance [7], [8], [13].
- **Industry studies** such as McKinsey and Deloitte quantify achievable cost reductions (15–25 %) and highlight organisational requirements for FinOps practices. The business case calculator therefore uses conservative optimisation factors derived from these studies [7], [9].
- **Gartner market analyses** indicate a fragmented tool landscape and motivate an integrated solution for SMEs with limited budgets [8].

## 3. Carbon Accounting and Energy Models
- **Energy-proportional computing literature** supplies the 30/70 idle-to-load power scaling used in `calculate_simple_power_consumption` [1], [2], [3].
- **Emission standards** from the IEA, EPA, and Green Software Foundation provide the methodological baseline for converting power consumption and grid intensity into CO₂ equivalents [4]–[6].
- **Carbon-aware scheduling research** (MIT, Microsoft, Google) demonstrates the value of temporal load shifting and motivates the dashboard’s optimisation scenarios [14], [15], [20].

## 4. Regional and Regulatory Context
- **German energy market reports** (Agora Energiewende, Fraunhofer ISE, BDEW) describe the national carbon intensity profile, enabling the localisation of ElectricityMaps data and the interpretation of scheduling windows [16]–[18].
- **EU policy documents** (Fit for 55) and SME digitalisation studies substantiate the compliance and adoption pressures faced by German SMEs, reinforcing the market focus of the prototype [11], [12], [19].

## 5. Monitoring and Runtime Measurement
- **AWS CloudTrail documentation** motivates the use of audit logs for runtime reconstruction, while highlighting the need for explicit configuration and data retention management [13].
- **NIST and related infrastructure monitoring guidelines** support the multi-source approach to measurement and verification, combining CloudTrail with CloudWatch metrics for triangulation [20].

## 6. Synthesis for the Prototype
- The integration of five APIs operationalises the literature’s call for accurate, real-time data across cost and carbon domains.
- Conservative uncertainty intervals reflect scientific caution where empirical validation is pending.
- The documentation and software architecture aim to bridge academic rigour with practical SME applicability by ensuring reproducibility, transparency, and explicit limitation statements.

## 7. References
Alle Literaturangaben befinden sich in `docs/references.md`.
