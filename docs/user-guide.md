# 📱 Dashboard User Guide - September 2025

## 🚀 **Quick Start Guide**

### **Launch Dashboard**
```bash
cd /Users/ch.klein/Documents/Bachelorthesis/CarbonAware_FinOps_Local
cd src
streamlit run app.py
```

**Access:** http://localhost:8501

---

## 📋 **Dashboard Navigation**

### **🏆 1. Executive Summary (Main Page)**
**Purpose:** SME management overview with immediate business value

**Key Elements:**
- **🇩🇪 German Grid Status:** Live carbon intensity with color-coded recommendations
  - 🟢 Green (<200g): Optimal time for workloads
  - 🟡 Yellow (200-350g): Moderate - consider delays
  - 🔴 Red (>350g): Avoid non-urgent tasks

- **📊 Current Infrastructure:** Your 4 baseline instances
  - Active instances count
  - Monthly cost (€20.81)
  - Monthly CO₂ (0.37 kg)
  - Optimization potential percentage

- **🏢 SME Scenario Calculator:**
  - Input field: Number of instances (1-500)
  - Quick buttons: 20/50/100 instances
  - Instant calculations: Cost, CO₂, Savings, ROI

- **📈 Optimization Chart:** Visual comparison of different approaches

**How to Use:**
1. Check current German grid status for immediate recommendations
2. Enter your company's instance count in calculator
3. Review projected savings and ROI timeline
4. Use scenarios for business case presentations

### **🇩🇪 2. Carbon Optimization**
**Purpose:** Demonstrate real-time German grid advantage

**Key Features:**
- **📊 24h Grid Pattern:** Shows daily carbon intensity variation
  - Optimal times: 12:00-16:00 (solar peak)
  - Avoid times: 18:00-22:00 (coal peak)
  - Current time highlighted with red star

- **💡 Smart Scheduling:** Actionable recommendations
  - What to do now vs what to postpone
  - Specific time windows for optimization

- **📈 Traditional vs Smart:** Quantified comparison
  - Current constant usage approach
  - Smart carbon-aware scheduling
  - Potential CO₂ reduction (20-30%)

- **🇪🇺 EU Compliance:** Business benefits for SMEs

**How to Use:**
1. Check optimal scheduling times for your workloads
2. Plan batch jobs during green periods
3. Use metrics for EU compliance reporting
4. Reference for customer carbon credentials

### **🔄 3. Competitive Analysis**
**Purpose:** Justify tool selection and investment

**Key Sections:**
- **📊 Feature Comparison:** Our tool vs competitors
- **💰 Cost Analysis:** €20/month vs €200+ for separate tools
- **📈 ROI Demonstration:** Quantified integration advantages
- **🏢 SME Value Proposition:** Why choose integrated approach

**Business Use Cases:**
- Management decision justification
- Vendor selection documentation
- Investment approval presentations
- Competitive positioning analysis

### **🏗️ 4. Infrastructure**
**Purpose:** Technical details for IT teams

**Content:**
- Instance-level breakdown
- Technical specifications
- Cost per instance analysis
- Validation metrics

**Target Audience:** Technical stakeholders, DevOps teams

### **🔬 5. Research Methods**
**Purpose:** Academic methodology and validation

**Content:**
- Scientific data sources
- Validation methodology
- Academic disclaimers
- Literature references

**Target Audience:** Academic reviewers, thesis committee

---

## 🎯 **Business Use Cases**

### **📊 Executive Presentations**
**Page:** Executive Summary
**Scenario:** Monthly board meeting, quarterly reviews
**Key Metrics:**
- Current grid status and immediate actions
- SME calculator results for budget planning
- ROI timeline for investment decisions

### **🌱 ESG Reporting**
**Page:** Carbon Optimization
**Scenario:** Sustainability reports, customer requirements
**Key Metrics:**
- CO₂ reduction percentages
- EU compliance status
- Carbon-aware scheduling benefits

### **💼 Vendor Justification**
**Page:** Competitive Analysis
**Scenario:** Tool selection, budget approval
**Key Metrics:**
- Cost comparison (€20 vs €200+)
- Feature advantages
- Implementation timeline (3 days vs weeks)

### **🔧 Technical Implementation**
**Page:** Infrastructure + Research Methods
**Scenario:** IT planning, academic validation
**Key Metrics:**
- Technical specifications
- Data source validation
- Scientific methodology

---

## 📈 **Key Dashboard Metrics**

### **🏢 SME Calculator Results**
For different company sizes:

| **Company Size** | **Instances** | **Monthly Savings** | **Annual ROI** | **Payback** |
|------------------|---------------|---------------------|----------------|-------------|
| Small SME | 20 | €33.30 | €400/year | 15 months |
| Medium SME | 50 | €83.24 | €999/year | 6 months |
| Large SME | 100 | €166.48 | €1,998/year | 3 months |

### **🔄 Competitive Advantage**
- **Cost Advantage:** 90% lower (€20 vs €200+/month)
- **ROI Advantage:** 67% better than separate tools
- **Speed Advantage:** 90% faster (3 days vs weeks)
- **Integration Advantage:** 32% vs 25% optimization

### **🇩🇪 German Grid Benefits**
- **Real-time Updates:** Every 30 minutes
- **Variation Range:** 150-550g CO₂/kWh daily
- **Optimization Potential:** Up to 60% better than static averages
- **EU Compliance:** Built-in ETS pricing (€50/tonne)

---

## 🛠️ **Troubleshooting**

### **🔄 Dashboard Not Loading**
```bash
# Check if in correct directory
pwd  # Should show: .../CarbonAware_FinOps_Local

# Navigate to src
cd src

# Launch dashboard
streamlit run app.py
```

### **📊 No Data Displayed**
**Symptoms:** "No infrastructure data available"
**Solution:** Check API connections
- ElectricityMaps API key in .env
- AWS profile configuration
- Internet connectivity

### **🏢 Calculator Not Updating**
**Symptoms:** SME calculator shows old values
**Solution:**
- Refresh browser page
- Clear browser cache
- Restart Streamlit server

### **💰 Cost Data Missing**
**Symptoms:** "Calculating..." instead of metrics
**Solution:**
- Verify AWS Cost Explorer permissions
- Check AWS profile access
- Wait for API cache refresh (1 hour)

---

## 📝 **Best Practices**

### **🎯 For Business Presentations**
1. **Start with Executive Summary** - immediate business value
2. **Use SME Calculator** - customize for audience size
3. **Show Competitive Analysis** - justify investment
4. **Reference German Grid** - demonstrate real-time advantage

### **🔬 For Academic Defense**
1. **Research Methods First** - establish credibility
2. **Show Technical Infrastructure** - demonstrate implementation
3. **Use Executive Summary** - business relevance
4. **Competitive Analysis** - market gap validation

### **🏢 For Customer Demos**
1. **Carbon Optimization Page** - environmental benefits
2. **Executive Summary Calculator** - cost savings
3. **Competitive Analysis** - why not alternatives
4. **Infrastructure Page** - technical capabilities

---

## 📚 **Additional Resources**

### **Documentation Links**
- [Scientific Improvements](./scientific-improvements-september-2025.md) - Technical validation
- [Validation Results](./validation-results-summary.md) - Performance evidence
- [Dashboard Restructuring](./dashboard-restructuring-september-2025.md) - Implementation details

### **API Documentation**
- ElectricityMaps: Real-time German grid data
- AWS Cost Explorer: Monthly billing validation
- AWS Pricing API: Instance-specific costs
- Boavizta: Hardware power consumption

### **Academic References**
- AWS Well-Architected Framework 2024
- Green Software Foundation Guidelines 2024
- EU ETS Carbon Pricing Framework
- German Energy Market Analysis

---

## 🎓 **Thesis Integration**

### **📊 For Introduction Section**
Use Executive Summary screenshots to demonstrate:
- Business relevance of research question
- Real-world application potential
- SME market opportunity quantification

### **📈 For Results Section**
Use Competitive Analysis to show:
- Integration advantage quantification
- Market positioning evidence
- ROI validation with scenarios

### **🔬 For Methodology Section**
Use Research Methods page to document:
- Scientific data sources
- Validation methodology
- Conservative estimate approach

### **💼 For Discussion Section**
Use Carbon Optimization to demonstrate:
- Real-time vs static advantage
- German market specialization
- EU compliance integration

---

**🎯 This dashboard provides comprehensive evidence for your Bachelor thesis while serving as a practical business tool for SME decision-making.**