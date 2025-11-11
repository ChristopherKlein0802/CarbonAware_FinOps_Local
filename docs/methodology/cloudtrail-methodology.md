# CloudTrail-gestützte Laufzeitermittlung

Dieses Dokument erläutert, wie der Prototyp AWS CloudTrail nutzt, um gegenüber herkömmlichen Schätzverfahren präzisere Laufzeitdaten zu erhalten und damit die Forschungsfrage zu adressieren.

## 1. Ausgangslage
Traditionelle FinOps-Werkzeuge schätzen Laufzeiten häufig aus Instanzzuständen oder Abrechnungsintervallen. Die resultierenden Unsicherheiten liegen laut Literatur bei bis zu ±40 %, was sowohl Kostenanalysen als auch Emissionsberechnungen einschränkt.

## 2. Vorgehen im Prototyp
1. **Ereigniserfassung:** `RuntimeTracker.get_all_ec2_instances()` ruft Instanzen ab und lädt mittels `boto3.client("cloudtrail")` alle relevanten Audit-Events der vergangenen 30 Tage (`RunInstances`, `StartInstances`, `StopInstances`, `TerminateInstances`).
2. **Eventauswertung:** `RuntimeTracker.process_instance_enhanced` ordnet Start- und Stop-Ereignisse, bildet Laufzeitslots und summiert die Dauer.
3. **Validierung:** Die ermittelte Laufzeit fließt in `BusinessCaseCalculator.calculate_cloudtrail_enhanced_accuracy`, wo sie mit AWS Cost Explorer abgeglichen wird. Abweichungen werden als Validierungsfaktor im Dashboard angezeigt.
4. **Zwischenspeicherung:** CloudTrail-Ergebnisse werden 3 Stunden zwischengespeichert (`CacheTTL.CLOUDTRAIL_EVENTS`), um aktuelle Runtime-Daten zu gewährleisten.

## 3. Vorteile gegenüber Schätzverfahren
| Kriterium | Schätzung (State-basierend) | CloudTrail-Ansatz |
|-----------|-----------------------------|-------------------|
| Datenquelle | Instanzstatus, Zeitmultiplikation | Audit-Event mit Zeitstempel |
| Genauigkeit (Literatur/Annahme) | ±30 – 40 % | ±5 % bei vollständigen Events |
| Nachvollziehbarkeit | gering | hoch, da Ereignisprotokolle verfügbar |
| Compliance-Bezug | indirekt | direkt (Audit-Log) |

## 4. Anforderungen an die AWS-Konfiguration
- CloudTrail muss für die Region `eu-central-1` aktiviert sein.
- Ereignisse sollten mindestens 30 Tage aufbewahrt werden (Standardretention 90 Tage).
- Das verwendete Profil benötigt Lesezugriff auf CloudTrail und EC2.

## 5. Limitationen
- Instanzen, die vor Aktivierung von CloudTrail gestartet wurden, liefern keine vollständige Historie.
- Bei sehr vielen Instanzen kann der Eventabruf zeitintensiv werden; das Caching mindert wiederholte Aufwände.
- Für Stop/Terminate-Ereignisse ohne passendes Start-Event werden konservative Schätzwerte markiert und entsprechend gekennzeichnet.

## 6. Bezug zur Forschungsfrage
- **Teilfrage 2:** Demonstriert, wie heterogene Datenquellen (Audit-Events, Abrechnungsdaten, Netzintensität) robust integriert werden.
- **Teilfrage 3:** Die erhöhte Genauigkeit ermöglicht belastbare Vergleiche mit getrennten Kosten- und Emissionstools.

Die CloudTrail-Integration bildet damit einen Kernbaustein des wissenschaftlichen Beitrags und ermöglicht eine solide Evaluationsbasis für die entwickelten Szenarien.
