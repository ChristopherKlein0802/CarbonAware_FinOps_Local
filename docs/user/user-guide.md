# Benutzer- und Implementierungshandbuch

Dieses Dokument bündelt Installation, Konfiguration und tägliche Nutzung des Carbon-Aware-FinOps-Dashboards. Es dient sowohl als technische Anleitung als auch als Referenz für die wissenschaftliche Dokumentation.

## 1. Voraussetzungen
- Python ≥ 3.11
- Virtuelle Umgebung (wird über `make setup` automatisch angelegt)
- Zugriff auf ElectricityMaps, Boavizta (optional), AWS Cost Explorer, AWS Pricing, AWS CloudWatch und AWS CloudTrail
- Konfiguriertes AWS-Profil mit Lesezugriff auf die genannten Dienste

## 2. Lokaler Aufbau
```bash
# Repository bereitstellen
git clone <your-repo-url>
cd CarbonAware_FinOps_Local

# Abhängigkeiten installieren und virtuelle Umgebung einrichten
make setup

# Unit-Tests ausführen
make test

# Dashboard starten
make dashboard
# Browser: http://localhost:8501
```

## 3. Konfiguration
1. `.env.example` nach `.env` kopieren.
2. Pflichtvariablen setzen:
   - `ELECTRICITYMAP_API_KEY`
   - `AWS_PROFILE` (falls kein Standardprofil verwendet wird)
   - optional `BOAVIZTA_BASE_URL`
3. AWS SSO (falls genutzt):
```bash
aws configure sso --profile <profilname>
aws sso login --profile <profilname>
```

### 3.1 AWS Identity Center Sitzungsverwaltung
- **Interactive Session Duration** im IAM Identity Center auf den Maximalwert (30 Tage) setzen (`Settings → Security → User session`).
- **Remember devices** aktivieren, damit MFA nur bei Gerätewechseln gefordert wird.
- Nach Änderungen einmal `aws sso login --profile <profilname>` ausführen; die CLI nutzt danach automatisch den verlängerten Cache.
- Hinweis: Trotz 30 Tagen Gerätetreue müssen Cost-Explorer-Tokens weiterhin gemäß Permission-Set-Laufzeit (z. B. 12 h) erneuert werden.
- Die Session-Dauer wird je Permission Set gesetzt. Für persönliche Ausnahmen: eigenes Permission Set anlegen (z. B. `FinOps-Extended`), nur deinem Benutzer zuweisen und dort die 12 h aktivieren. Code-seitig lässt sich diese AWS-Einstellung nicht überschreiben.

### 3.2 Cost-Explorer-Konfiguration im Dashboard-Account
- Cost Explorer im Management- oder Billing-Account aktivieren und **Hourly and Resource Level Data** freischalten (`Billing → Cost Explorer → Preferences`).
- Dem genutzten Permission Set mindestens `arn:aws:iam::aws:policy/AWSCostExplorerReadOnlyAccess` zuweisen; optional `Billing`-Leserechte für konsistente Monatsdaten.
- Sicherstellen, dass `us-east-1` als Cost-Explorer-Region freigeschaltet ist (API-Standardregion).
- Im Dashboard vor dem Start `aws sts get-caller-identity --profile <profilname>` prüfen; bei Fehlern erneut `aws sso login` ausführen, um frische Tokens zu holen.

### 3.3 Automatischer Login-Check im Projekt
- `scripts/ensure_aws_session.sh <profilname>` prüft die Sitzung und startet bei Bedarf `aws sso login`.
- `make`-Kommandos mit AWS-Bezug (z. B. `make validate-aws`, `make plan`, `make dashboard`) sowie die Dashboard-AWS-Clients rufen das Skript automatisch auf.
- Das Skript benötigt weiterhin eine bestätigte IAM-Identity-Center-Session (z. B. per „Remember devices“); bei Ablauf öffnet sich der Browser zum Login.

## 4. Datenintegration und Infrastruktur
| Dienst | Zweck | Modul | Hinweis |
|--------|-------|-------|---------|
| ElectricityMaps | Aktuelle & historische CO₂-Intensität | `src/infrastructure/clients/electricity.py` | API-Key erforderlich |
| Boavizta | Hardware-Leistungsmodelle | `src/infrastructure/clients/boavizta.py` | Optional, reduziert Unsicherheit |
| AWS Cost Explorer | Kostenvalidierung | `src/infrastructure/clients/aws.py` | Billing-Rechte notwendig |
| AWS Pricing | On-Demand-Preise | `src/infrastructure/clients/aws.py` | Standardregion `eu-central-1` |
| AWS CloudTrail | Laufzeitpräzision | `src/services/runtime.py` | Trail für 30 Tage aktiv halten |
| AWS CloudWatch | CPU-Auslastung | `src/infrastructure/clients/aws_runtime.py` | Standardmetriken ausreichend |

Optional kann über `make deploy` eine Terraform-Testumgebung mit vier Instanzen provisioniert werden (`make status`, `make destroy` für Verwaltung).

## 5. Dashboard-Navigation
Das Streamlit-Dashboard bietet drei Hauptseiten (Auswahl über die Sidebar).

### 5.1 Executive Summary
- Verdichtete Kennzahlen zu Kosten, CO₂ und Datenqualität
- Business-Case-Indikatoren mit Validierungsfaktor
- Einsatz in der Thesis: zeigt den Mehrwert der integrierten Lösung und verweist auf Unsicherheiten

### 5.2 Carbon Optimization
- 24h-Profil der deutschen Netzintensität
- Empfehlungen zur Lastverschiebung
- Einsatz in der Thesis: belegt Vorteile gegenüber getrennten Tools (Teilfrage 3)

### 5.3 Infrastructure
- Instanztabellen mit Laufzeit (CloudTrail), CPU (CloudWatch), Kosten und Emissionen
- API-Statusanzeigen nach No-Fallback-Policy
- Einsatz in der Thesis: liefert Rohdaten zur Integration heterogener Quellen (Teilfrage 2)

## 6. Evaluationsablauf
1. **Baseline erfassen:** Dashboard starten und ersten Datensatz erzeugen.
2. **Integrationstest:** `make test-integration` erzeugt Artefakte in `artifacts/integration/<timestamp>/`.
3. **Dokumentation:** Ergebnisse in `docs/validation-results.md` ergänzen, Literaturvergleiche einbinden.
4. **Wiederholung:** Messläufe (z. B. täglich) für Trendanalysen einplanen.

## 7. Interpretation von Kennzahlen
| Symbol/Hinweis | Bedeutung |
|----------------|-----------|
| ⚠️ Warnung | Datenquelle fehlt; Wert wird nicht aggregiert. |
| "Berechnung läuft" | Cache wird aktualisiert oder API-Antwort steht aus. |
| Validierungsfaktor | Verhältnis berechneter zu AWS-Kosten (1,0 = perfekte Übereinstimmung). |

## 8. Typische Einsatzszenarien
- **Management-Update:** Executive Summary exportieren, Aussagen mit `docs/market-analysis.md` ergänzen.
- **ESG-/CSRD-Reporting:** Carbon Optimization heranziehen, Literaturbandbreite ergänzen (vgl. `docs/calculations.md`).
- **FinOps-Review:** Infrastructure-Ansicht für Right-Sizing- und Shutdown-Entscheidungen nutzen.

## 9. Fehlersuche
1. **Keine Daten:** API-Schlüssel/Credentials prüfen; Dashboard zeigt betroffene Dienste an.
2. **Veraltete Werte:** Sidebar-Schaltfläche „Refresh data“ nutzen, Cache wird invalidiert.
3. **Fehlende Laufzeiten:** CloudTrail-Konfiguration und Event-Retention kontrollieren.
4. **Authentifizierungsprobleme:** `aws sso login` erneut ausführen, `.env` prüfen.

## 10. Dokumentation pflegen
- Neue Formeln → `docs/calculations.md`
- Messläufe/Evaluation → `docs/validation-results.md`
- Architekturänderungen → `docs/system-architecture.md`
- README aktualisieren, falls sich Zielsetzung oder Setup ändert.

Dieses Handbuch stellt sicher, dass Installation, Betrieb und wissenschaftliche Nutzung des Prototyps konsistent dokumentiert sind.
