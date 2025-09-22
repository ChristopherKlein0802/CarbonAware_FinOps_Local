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
**Purpose:** Verdichteter Überblick für Management und Stakeholder.

**Key Elements:**
- **🇩🇪 German Grid Status:** Live-Intensität mit Ampelbewertung (🟢 < 200 g, 🟡 200–350 g, 🔴 > 350 g CO₂/kWh).
- **Kosten- und CO₂-Metriken:** Aggregierte Monatswerte basierend auf den aktuell verfügbaren Instanzdaten.
- **Business-Case-Kacheln:** Einsparpotenziale und Validierungsstatus, soweit durch echte API-Daten gedeckt.

**So nutzt du die Seite:**
1. Grid-Status prüfen und kurzfristige Maßnahmen ableiten.
2. Kosten- und Emissionswerte einordnen, bei Warnungen Quellencheck starten.
3. Business-Case-Hinweise lesen; bei „Schätzwerte“ Hinweise aus Methodik beachten.

### **🇩🇪 2. Carbon Optimization**
**Purpose:** Visualisierung der stündlichen Netzintensität für Lastverschiebung.

**Key Features:**
- **📊 24h-Pattern:** Plot der letzten Stunden (ElectricityMaps-History oder lokale Sammlung).
- **🔍 Status-Karten:** Empfohlene Vorgehensweise je nach aktueller Intensität.
- **📈 Fortschrittsanzeige:** Hinweis, ob bereits genügend Messpunkte für ein Tagesprofil vorliegen.

**Praxis-Tipps:**
1. Chart beobachten und geplante Batch-Jobs in grüne Zeitfenster legen.
2. Bei unvollständigen Daten (Hinweis im Chart) zusätzliche Messläufe starten.
3. Werte für ESG-/CSRD-Reporting dokumentieren.

### **🏗️ 3. Infrastructure**
**Purpose:** Technische Detailanalyse für DevOps und FinOps.

**Inhalte:**
- **Instanz-Tabelle:** Laufzeit, CPU, Kosten- und CO₂-Werte mit NO-FALLBACK-Hinweisen.
- **Summen- und Durchschnittswerte:** Aggregierte Kennzahlen über alle Instanzen.
- **Datenqualitäts-Hinweise:** Transparente Anzeige, wenn CloudTrail oder CloudWatch noch keine Messwerte liefern.

**Empfohlenes Vorgehen:**
1. Tabelle nach Warnsymbolen durchsuchen (⚠️ bedeutet fehlende Primärdaten).
2. Auffällige Instanzen (z. B. hohe Wattzahl) gegen AWS-Metriken verifizieren.
3. Ergebnisse in Validierungsdokumentation übertragen.

---

## 🎯 **Business Use Cases**

### **📊 Executive Presentations**
**Seite:** Executive Summary
**Szenario:** Monatliche Management-Updates
**Relevante Kennzahlen:** Grid-Status, validierte Kosten-/CO₂-Werte, Business-Case-Narrative inkl. Unsicherheiten.

### **🌱 ESG Reporting & CSRD**
**Seite:** Carbon Optimization
**Szenario:** Nachhaltigkeitsreporting, Kundenaudits
**Relevante Kennzahlen:** 24h-Intensitätsprofil, dokumentierte Unsicherheiten, Quellenangaben (ElectricityMaps, Boavizta).

### **🔧 Technischer Betrieb**
**Seite:** Infrastructure
**Szenario:** FinOps-/DevOps-Analyse der Instanzflotte
**Relevante Kennzahlen:** Laufzeiten (CloudTrail), CPU (CloudWatch), Kostenbindung (AWS Pricing/Cost Explorer) und Datenqualitäts-Hinweise.

---

## 📈 **Key Dashboard Metrics**

### **🏢 Beobachtete Kennzahlen**
Die angezeigten Werte stammen ausschließlich aus den aktuell verfügbaren API-Daten. Fehlende Messwerte werden mit ⚠️ gekennzeichnet und fließen nicht in Summen ein (siehe NO-FALLBACK-Policy).

### **🇩🇪 German Grid Insights**
- **Aktualisierung:** bis zu stündlich (ElectricityMaps + lokaler Cache).
- **Variationsband:** typischerweise 150–550 g CO₂/kWh laut Literatur [16][17]; konkrete Werte stammen aus der Messung.
- **Compliance-Hinweis:** EU-ETS-Preis (€50/t) wird für Sensitivitätsanalysen genutzt; keine automatische Berichterstattung.

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
