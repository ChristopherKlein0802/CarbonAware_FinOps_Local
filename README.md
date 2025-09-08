# Infrastructure Analysis & Optimization Potential Tool - Bachelor Thesis

## 🎯 Project Overview
This **Bachelor Thesis tool** analyzes AWS infrastructure to calculate **both cost and carbon consumption**, then determines **optimization potential** through various scheduling strategies. Unlike traditional FinOps tools that focus only on cost, this tool demonstrates the value of **carbon-aware optimization** for German cloud deployments.

### 🏆 Core Thesis Contribution
**First FinOps tool that quantifies BOTH cost AND carbon optimization potential**
- Real AWS Cost Explorer integration with German electricity grid data
- Business case calculator showing ROI of carbon-aware optimization  
- Scientific methodology for comparing cost-only vs. carbon-aware strategies

## ⚡ Analysis-Focused Approach

### What This Tool Does:
✅ **Analyzes** current AWS infrastructure costs and carbon emissions  
✅ **Calculates** optimization potential for different scheduling strategies  
✅ **Generates** business cases with ROI and ESG impact metrics  
✅ **Demonstrates** value through test instances with optimized cost differences  

### What This Tool Does NOT Do:
❌ **No automatic infrastructure changes** - analysis and recommendations only  
❌ **No production disruption** - safe to deploy in any AWS environment  
❌ **No trust required** - shows potential before implementation

## 📁 Project Structure

```
CarbonAware_FinOps_Local/
├── README.md                    # Main project documentation
├── Makefile                     # Build and deployment commands  
├── requirements.txt             # Python dependencies
│
├── docs/                        # 📚 Documentation
│   ├── project-summary.md       # Detailed project overview
│   ├── thesis-assessment.md     # Academic assessment criteria
│   ├── deployment-guide.md      # Deployment instructions
│   ├── api-integration-guide.md # API setup and usage
│   └── makefile-guide.md        # Available make commands
│
├── src/                         # 🐍 Application source code
│   ├── visualization/           # Dashboard and interactive charts
│   ├── services/                # AWS and external API clients
│   ├── analytics/               # Data analysis logic
│   ├── carbon/                  # Carbon intensity calculations
│   ├── config/                  # Configuration management
│   └── utils/                   # Utility functions
│
├── tests/                       # 🧪 Test suite
│   ├── examples/                # Demo and example scripts
│   └── test_*.py                # Unit and integration tests
│
├── infrastructure/              # 🏗️ Infrastructure as Code
│   └── terraform/               # AWS resource definitions
│
└── config/                      # ⚙️ Configuration files
    └── pyrightconfig.json       # Type checker settings
```

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)
```bash
# Clone repository
git clone <your-repo>
cd CarbonAware_FinOps_Local
make setup-env
```

### Option 2: Manual Setup
```bash
# 1. Copy and edit configuration
cp infrastructure/terraform/terraform.tfvars.example infrastructure/terraform/terraform.tfvars
# Edit terraform.tfvars with your AWS Account ID and profile

# 2. Run individual commands
make setup
make deploy
make dashboard
```  

## 🔬 Scientific Methodology

### Data Sources:
- **AWS Cost Explorer API** - Real billing data from any AWS account
- **ElectricityMap API** - Real-time German electricity grid carbon intensity
- **Boavizta API** - Scientific hardware power consumption data (with comprehensive fallback)
- **German Focus** - EU-Central-1 (Frankfurt) region optimization with real grid data

### Optimization Scenarios Analyzed:
1. **Office Hours** (8-18h, Mo-Fr): ~72% runtime reduction
2. **Weekdays Only** (24h, Mo-Fr): ~28% runtime reduction  
3. **Carbon-Aware** (avoids high CO2 periods): ~15% runtime reduction, 34% carbon reduction

### Calculation Transparency:
```
Cost Savings = Current Cost × (1 - Runtime Reduction Factor)
Carbon Savings = Power (kW) × Runtime Hours × Grid Intensity (gCO2/kWh) ÷ 1000
Combined ROI = (Cost Savings × 12) ÷ Implementation Cost × 100%
```

## 🚀 Quick Start

### 1. Universal Deployment (Any AWS Account)
```bash
# Set your API key and AWS profile
export ELECTRICITYMAP_API_KEY=your-api-key
export AWS_PROFILE=your-aws-profile

# Deploy infrastructure analysis tool
./deploy_universal.sh
```

### 2. View Analysis Dashboard
```bash
# Launch optimization analysis dashboard
python3 optimization_analysis_dashboard.py

# Access at: http://localhost:8051
```

## 📊 Dashboard Features

### 1. **Current Infrastructure Analysis**
- Real monthly costs from AWS Cost Explorer
- CO2 emissions using German grid data
- Instance-level breakdown with cost/carbon ratios

### 2. **Optimization Potential Calculator**
- Scheduling scenario comparisons
- Cost vs. carbon trade-off analysis
- Specific recommendations per instance

### 3. **Business Case Generator** 
- ROI calculations with payback periods
- ESG impact metrics for management
- Cost per kg CO2 saved analysis

### 4. **Methodology Documentation**
- Transparent calculation formulas
- Data source explanations
- German grid focus rationale

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ AWS Test        │    │ Infrastructure   │    │ Cost Explorer   │
│ Instances       │◄───┤ Analyzer Lambda  │───►│ (Real Costs)    │
│ (4 instances)   │    │ (Analysis Only)  │    │ API             │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Demonstrates    │    │ DynamoDB         │    │ ElectricityMap  │
│ Optimization    │    │ Analysis Results │    │ German Grid API │
│ Potential       │    │ Storage          │    │ (Real CO2 Data) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 ▼
                    ┌──────────────────┐
                    │ Analysis         │
                    │ Dashboard        │
                    │ (Port 8051)      │
                    └──────────────────┘
```

## 📁 Project Structure

```
├── optimization_analysis_dashboard.py    # Main analysis dashboard
├── deploy_universal.sh                   # Universal deployment script
├── UNIVERSAL_DEPLOYMENT.md              # Deployment documentation
├── src/
│   ├── lambda/scheduler_handler.py      # Infrastructure analyzer (analysis-only)
│   ├── carbon/carbon_api_client.py      # Carbon intensity API integration
│   └── config/settings.py               # Configuration management
├── infrastructure/terraform/             # AWS infrastructure as code
│   ├── main.tf                         # Core infrastructure + test instances
│   ├── lambda.tf                       # Analysis Lambda function
│   └── variables.tf                    # Configurable parameters
└── tests/                              # Test suite
```

## 🇩🇪 German Focus

### Why German Electricity Grid?
- **Accuracy**: ElectricityMap free tier covers Germany comprehensively
- **Variability**: German grid has significant coal/renewable mix variations
- **Research Value**: Demonstrates regional carbon optimization importance
- **Business Relevance**: Major EU market for cloud sustainability

### Regional Optimization:
- **Primary**: EU-Central-1 (Frankfurt) - German data center
- **Secondary**: EU-Central-2 (Zurich) - Uses German grid proxy data
- **Carbon Intensity**: Real-time data from German electricity grid

## 🎓 Bachelor Thesis Value

### Academic Contributions:
1. **Novel Approach**: First tool combining real AWS costs with regional carbon data
2. **Scientific Method**: Transparent calculations with reproducible results  
3. **Practical Application**: Deployable tool demonstrating real-world value
4. **Competitive Analysis**: Clear differentiation from existing FinOps tools

### Business Value:
1. **Risk-Free**: Analysis only, no infrastructure modifications
2. **ROI Focused**: Clear business case with payback calculations
3. **ESG Compliance**: Environmental impact metrics for reporting
4. **German Market**: Optimized for German electricity grid patterns

## 🔍 Competitive Analysis

| Feature | This Tool | Cloud Carbon Footprint | AWS Carbon Lake | Traditional FinOps |
|---------|-----------|-------------------------|-----------------|-------------------|
| **Real AWS Cost Integration** | ✅ | ❌ | ❌ | ✅ |
| **Regional Carbon Data** | ✅ German Grid | ❌ Generic | ❌ Limited | ❌ None |
| **Combined Optimization** | ✅ Cost + Carbon | ❌ Carbon Only | ❌ Reporting Only | ❌ Cost Only |
| **Business Case Generator** | ✅ ROI + ESG | ❌ | ❌ | ✅ Cost Only |
| **Analysis-First Approach** | ✅ Safe Deployment | ❌ | ✅ | ❌ |

## 🛠️ Development & Testing

### Local Development:
```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/

# Start local dashboard
python optimization_analysis_dashboard.py
```

### Test Infrastructure:
- **4 Test Instances**: Different scheduling patterns for demonstration
- **Real Cost Data**: Uses actual AWS billing for accuracy
- **German Grid Data**: Real-time CO2 intensity from ElectricityMap

## 📈 Results & Validation

### Expected Outcomes:
- **Cost Optimization**: 15-75% potential savings depending on workload pattern
- **Carbon Reduction**: 15-34% CO2 savings through intelligent scheduling
- **Combined Value**: 20-40% better overall optimization vs. cost-only approaches
- **Business Impact**: Clear ROI with 3-12 month payback periods

### Validation Methods:
- **Real Data**: AWS Cost Explorer + ElectricityMap APIs
- **German Specificity**: Regional grid patterns and carbon intensity
- **Comparative Analysis**: Cost-only vs. carbon-aware optimization
- **Business Metrics**: ROI, payback period, ESG impact calculations

## 📚 Documentation

- **[Universal Deployment Guide](UNIVERSAL_DEPLOYMENT.md)** - Deploy to any AWS account
- **[Makefile Commands](MAKEFILE_GUIDE.md)** - Development shortcuts
- **Architecture Documentation** - In-code documentation and comments

## 🤝 Contributing

This is a Bachelor Thesis project focused on demonstrating carbon-aware FinOps optimization for German cloud infrastructure. The analysis-first approach ensures safe deployment while providing scientific validation of optimization potential.

## 📄 License

This project is developed as part of a Bachelor Thesis research. See institution guidelines for usage and distribution.

---

**🎓 Bachelor Thesis Tool: Infrastructure Analysis & Optimization Potential**  
*Demonstrating the business value of carbon-aware cloud optimization in German AWS regions*