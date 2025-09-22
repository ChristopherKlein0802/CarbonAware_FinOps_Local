# Development Guidelines - Carbon-Aware FinOps Bachelor Thesis

## 🎓 **Project Overview**

### **Research Question**
> "Wie kann ein integriertes Carbon-aware FinOps Tool durch Echtzeit-Stromnetz-Daten sowohl Kosten als auch CO2-Emissionen gegenüber separaten Carbon-Reporting und Cost-Optimierung Tools optimieren?"

### **Academic Scope**
Bachelor Thesis exploring integrated carbon-aware cloud cost optimization for German SME market (≤100 AWS instances in EU-Central-1)

### **Unique Contribution**
First tool combining real-time German grid data (ElectricityMaps) + AWS Cost Explorer + SME business case generation in a single academic prototype.

---

## 🔬 **Scientific Principles**

### **NO-FALLBACK Policy (Critical)**
All API failures return `None` or `0.0` - NO dummy data for scientific rigor

```python
# ✅ CORRECT - Academic honesty
if not self.api_key:
    logger.error("❌ ElectricityMap API key not available - NO FALLBACK used")
    return None

# ❌ WRONG - Compromises scientific validity
return {"fallback_value": 420}  # Never do this
```

### **Conservative Academic Language**
```python
# ✅ CORRECT - Appropriate thesis language
"theoretical_scenarios": self.calculate_theoretical_scenarios()
"illustrative_monthly_savings": baseline_cost * 0.20
"methodology_disclaimer": "All optimization calculations require empirical validation"

# ❌ WRONG - Overconfident claims
"validated_competitive_advantage"  # Avoid
"scientifically_proven_savings"    # Avoid
```

### **Transparent Uncertainty Documentation**
```python
API_UNCERTAINTIES = {
    "aws_cost": 0.02,                   # 2% - AWS billing accuracy
    "boavizta_power": 0.10,            # 10% - Hardware estimation uncertainty
    "electricitymap_carbon": 0.05,     # 5% - Grid measurement uncertainty
    "scheduling_assumptions": 0.20,     # 20% - Business variability
}
```

---

## 💻 **Code Standards**

### **Method Naming Convention**
```python
# ✅ ACADEMIC-APPROPRIATE naming
def calculate_theoretical_scenarios()     # Not "validate_competitive_advantage"
def generate_illustrative_business_case() # Not "calculate_proven_roi"
def run_parameter_sensitivity_analysis()  # Not "run_monte_carlo_validation"
```

### **Error Handling with Academic Integrity**
```python
def scientific_api_call(endpoint, params):
    """Academic integrity through explicit failure handling"""
    try:
        response = requests.get(endpoint, params=params, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"❌ API failed: {response.status_code} - NO FALLBACK used")
            return None
    except Exception as e:
        logger.error(f"❌ API error: {e} - NO FALLBACK used")
        return None  # Never fabricate data for academic integrity
```

### **Documentation Requirements**
```python
def calculate_carbon_footprint(instance, carbon_intensity, cpu_utilization):
    """
    Scientific CO2 calculation with real-time data

    Formula: CO2 = Power × Time × Grid_Carbon_Intensity × CPU_Factor

    ACADEMIC DISCLAIMER: All calculations require empirical validation
    """
    # Implementation with transparent uncertainty
```

---

## 🏗️ **Architecture Guidelines**

### **Current Structure (Streamlit App)**
```
src/
├── app.py            # Streamlit entrypoint and global layout
├── api/              # ElectricityMaps, AWS, Boavizta integrations
├── core/             # Data processor, calculators, runtime tracker
├── models/           # Dataclasses for EC2, carbon, business, dashboard
├── utils/            # Cache, logging, validation, UI helpers
└── views/            # Streamlit page components (overview, carbon, infra)
```

### **API Integration Standards**
- **ElectricityMaps API**: German grid carbon intensity (2h caching)
- **Boavizta API**: Scientific hardware power consumption (7d caching)
- **AWS Cost Explorer**: Real billing data (6h caching)
- **AWS Pricing API**: Instance-specific pricing (7d caching)
- **AWS CloudWatch**: CPU utilization metrics (3h caching)

### **Terraform Test Workloads**
- Vier EC2-Testinstanzen starten per User-Data automatisierte CPU-Profile
- Szenarien decken niedrige (~10 %), mittlere (~40 %), hohe (~80 %) und dynamisch wechselnde Last ab
- Lasten werden über `stress-ng` erzeugt, damit CloudWatch/CloudTrail realistische Metriken liefern

---

## 🎯 **Development Workflow**

### **Feature Development Process**
```bash
# 1. Academic compliance check
make lint      # Code quality validation
make test      # Comprehensive testing
make health    # API connectivity verification

# 2. Documentation update
# - Update method docstrings with academic disclaimers
# - Add uncertainty ranges to new calculations
# - Include literature references for new algorithms

# 3. Deployment validation
make deploy    # Test infrastructure deployment
make status    # Infrastructure health check
```

### **Code Review Checklist**
- ✅ All API calls include error handling with NO fallback values
- ✅ Method names reflect academic uncertainty (theoretical_, illustrative_)
- ✅ Business logic includes academic disclaimers and uncertainty ranges
- ✅ Documentation maintains conservative academic language
- ✅ New features include appropriate test coverage

---

## 📊 **Testing Standards**

### **Test Categories**
```
tests/
├── unit/           # calculators, tracker, constants, processor
└── integration/    # pipeline exercise with real APIs (optional)
```

### **Academic Testing Requirements**
- NO mock data for API responses (use real API calls in CI)
- Conservative test assertions with uncertainty ranges
- Integration tests for all external APIs
- Performance tests for caching strategies

---

## 🎓 **Bachelor Thesis Compliance**

### **Academic Requirements Met**
- ✅ **Novel Research Question**: First integrated carbon-aware FinOps approach
- ✅ **Literature Foundation**: 21+ peer-reviewed sources with systematic review
- ✅ **Technical Implementation**: Production-ready dashboard with API integration
- ✅ **Conservative Methodology**: Transparent limitations and uncertainty ranges
- ✅ **Business Validation**: Real ROI calculations with German market focus
- ✅ **Reproducible Research**: Open source with documented APIs

### **Thesis Defense Preparation**
```yaml
Expected Challenges & Responses:
  "Not novel enough":
    - Systematic competitive analysis (no equivalent tool found)
  "Claims too strong":
    - Conservative methodology with ±15% confidence intervals
  "Methodology weak":
    - Scientific APIs with peer-reviewable calculations
  "Not practical":
    - Real AWS deployment with business case validation
```

### **Risk Mitigation Strategy**
- **Scope Limitations**: 4-instance test environment, German-only focus
- **Validation Requirements**: All optimization scenarios require empirical validation
- **Uncertainty Acknowledgment**: API precision undocumented by providers
- **Methodology Status**: Theoretical framework exploration for Bachelor thesis

---

## 🚀 **Quick Commands**

```bash
# Setup and launch
streamlit run src/app.py

# API health check
python -c "from src.api.client import UnifiedAPIClient; print(UnifiedAPIClient().get_current_carbon_intensity('eu-central-1'))"

# Run comprehensive tests
python -m pytest tests/ -v

# Deploy test infrastructure
make deploy && make status

# Clean up resources
make destroy
```

---

## 🎯 **Project Status: THESIS-READY**

**Academic Excellence Indicators:**
1. 🔬 **Scientific Rigor**: NO-FALLBACK policy with conservative estimates
2. ⚡ **Technical Innovation**: 5-API integration with optimized caching
3. 📚 **Academic Positioning**: Novel research question with validated market gap
4. 🛠️ **Practical Implementation**: Real AWS deployment with business validation
5. 🇩🇪 **Market Relevance**: German SME focus with EU compliance integration

**Implementation Cost**: €5/month API costs vs €200+ for separate tools (97.5% savings)

---

*This development guide ensures continued academic integrity while maintaining technical excellence for the Carbon-Aware FinOps Bachelor thesis project.*
