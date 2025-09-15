# 🏥 Health Monitoring System - Verwendungsanleitung

Das Carbon-Aware FinOps Dashboard verfügt über ein umfassendes API-Gesundheitsüberwachungssystem für alle externen Dienste.

## 🚀 Schnellstart

### 1. Vor Dashboard-Start prüfen
```bash
# Einfacher Health Check
python check_health.py

# Oder direkt das Health-Modul
python dashboard/utils/health_checks.py
```

### 2. Dashboard mit automatischer Gesundheitsprüfung starten
```bash
python dashboard/dashboard_main.py
```
Das Dashboard führt automatisch einen Health Check durch und zeigt Ihnen den Status aller APIs.

## 📊 Was wird überwacht?

### ElectricityMap API
- **Zweck**: Deutsche Stromnetz-Kohlenstoffintensität (g CO2/kWh)
- **Konfiguration**: `ELECTRICITYMAP_API_KEY` in `.env` Datei
- **Cache**: 30 Minuten (entspricht API-Update-Frequenz)
- **Status-Codes**:
  - ✅ `healthy`: API antwortet korrekt mit aktuellen Daten
  - ⚠️ `degraded`: API antwortet, aber Datenstruktur unvollständig
  - ❌ `error`: API nicht erreichbar oder API-Key fehlt

### Boavizta API
- **Zweck**: Hardware-Stromverbrauchsdaten für AWS-Instanztypen
- **Konfiguration**: Keine (öffentliche API)
- **Cache**: Keine (schnelle Antwortzeiten)
- **Status-Codes**:
  - ✅ `healthy`: API liefert Stromverbrauchsdaten
  - ⚠️ `degraded`: API antwortet, aber Daten unvollständig
  - ❌ `error`: API nicht erreichbar

### AWS Cost Explorer API
- **Zweck**: Echte AWS-Abrechnungsdaten
- **Konfiguration**: AWS-Profil via `aws configure sso`
- **Cache**: 1 Stunde (API kostet $0.01 pro Aufruf)
- **Status-Codes**:
  - ✅ `healthy`: Kostendaten erfolgreich abgerufen
  - ⚠️ `degraded`: Verbindung da, aber keine Daten
  - ❌ `error`: Berechtigung fehlt oder Profil nicht konfiguriert

## 🔧 Programmatische Verwendung

### Einfacher Status-Check
```python
from dashboard.utils.health_checks import quick_health_check

if quick_health_check():
    print("✅ Dashboard kann gestartet werden")
    # Dashboard starten
else:
    print("⚠️ Einige APIs haben Probleme")
    # Dashboard trotzdem starten, aber mit Hinweis
```

### Detaillierte Gesundheitsanalyse
```python
from dashboard.utils.health_checks import health_check_manager

# Vollständige API-Prüfung
results = health_check_manager.check_all_apis()

# Systemweiter Status
overall = results['system_overall']
print(f"Status: {overall['overall_status']}")
print(f"Bereit: {overall['dashboard_ready']}")

# Einzelne APIs
for api_name in ['electricitymap', 'boavizta', 'aws_cost_explorer']:
    api_status = results[api_name]
    print(f"{api_name}: {api_status['status']} ({api_status['response_time_ms']:.0f}ms)")
```

### Dashboard-Integration
```python
from dashboard.utils.health_dashboard import dashboard_health

# Health Status Card für Dashboard
health_card = dashboard_health.create_health_status_card()

# Startup Health Check
startup_status = dashboard_health.get_startup_health_check()
print("Bereit:", startup_status['ready_to_start'])
```

## 🛠️ Fehlerbehebung

### ElectricityMap Probleme

**Problem**: API-Key nicht konfiguriert
```bash
# Lösung: API-Key in .env setzen
echo "ELECTRICITYMAP_API_KEY=your_key_here" >> .env
```
**API-Key erhalten**: https://app.electricitymap.org/map

**Problem**: "Unauthorized" Fehler
- API-Key prüfen: Ist er korrekt kopiert?
- Gültigkeit prüfen: Läuft das kostenlose Kontingent noch?

### AWS Cost Explorer Probleme

**Problem**: "AWS profile not configured"
```bash
# Lösung: AWS SSO konfigurieren
aws configure sso
```

**Problem**: "Access Denied"
- IAM-Berechtigungen prüfen: `ce:GetCostAndUsage` erforderlich
- AWS-Profil prüfen: `AWS_PROFILE` in `.env` setzen

### Boavizta API Probleme

**Problem**: API nicht erreichbar
- Netzwerkverbindung prüfen
- Firewall/Proxy-Einstellungen überprüfen
- Status: https://api.boavizta.org/v1/cloud/instance (sollte 405 Method Not Allowed zeigen)

## 📈 Performance-Monitoring

### Antwortzeiten überwachen
```python
health_metrics = dashboard_health.get_health_metrics_for_monitoring()
print("Response Times:")
for api, time_ms in health_metrics['api_response_times'].items():
    print(f"  {api}: {time_ms:.0f}ms")
```

### Automatische Überwachung
Das System cached Gesundheitsdaten automatisch:
- **Health Checks**: 1 Minute Cache
- **ElectricityMap**: 30 Minuten Cache
- **AWS Costs**: 1 Stunde Cache

## 🎓 Bachelor Thesis Besonderheiten

### Wissenschaftliche Integrität
- **Keine Fallbacks**: Bei API-Ausfall werden 0-Werte angezeigt
- **Transparenz**: Datenquelle und -verfügbarkeit werden klar kommuniziert  
- **Caching-Strategien**: Basieren auf realen API-Update-Frequenzen

### Fehlerbehandlung
```python
# Beispiel: Wissenschaftlich korrekte Fehlerbehandlung
carbon_intensity = api_client.get_carbon_intensity()
if carbon_intensity is None:
    # KEIN Fallback-Wert - zeige 0 und dokumentiere API-Ausfall
    display_value = 0
    data_source = "API unavailable - no fallback used (scientific rigor)"
```

## 🔄 Automatische Dashboard-Integration

Das Health Check System ist automatisch in das Dashboard integriert:

1. **Beim Start**: Automatischer Health Check mit detailliertem Bericht
2. **Laufzeit**: Cached Health Monitoring für Performance
3. **UI-Integration**: Health Status Cards in Dashboard-Tabs
4. **Logging**: Alle API-Probleme werden strukturiert geloggt

### Beispiel Dashboard-Startup:
```
🚀 Carbon-Aware FinOps Dashboard - Bachelor Thesis
📊 Dashboard URL: http://127.0.0.1:8053

🏥 Checking API Health...
============================================================
🏥 API HEALTH STATUS: HEALTHY
✅ Healthy: 3/3
Dashboard Ready: ✅
============================================================

📋 Startup Recommendations:
   ✅ All APIs operational - dashboard fully functional
```

## 💡 Best Practices

1. **Vor Deployment**: Immer `python check_health.py` ausführen
2. **Entwicklung**: Health Check in automatisierte Tests integrieren
3. **Produktion**: Regelmäßige Health Checks über Monitoring-Tools
4. **Debugging**: Health Logs für Problemdiagnose nutzen

Das Health Monitoring System gewährleistet die Zuverlässigkeit und wissenschaftliche Integrität Ihres Carbon-Aware FinOps Dashboards.