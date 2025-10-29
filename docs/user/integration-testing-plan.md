# Plan für Integrationstests: Carbon-Aware FinOps

## Ziele
1. Den vollständigen Datenpfad von externen APIs bis zur Streamlit-Ausgabe prüfen.
2. Reproduzierbare Messläufe mit kommentierten Rohdaten für wissenschaftliche Evidenz erzeugen.
3. Regressionen in Caching, Berechnung und Business-Case-Erstellung frühzeitig erkennen.

## Testszenarien
| Szenario | Beschreibung | Primäre Datenquellen | Erwartete Evidenz |
|----------|--------------|----------------------|-------------------|
| Baseline Monitoring | Referenz-Snapshot mit vier EC2-Instanzen (m6a.large, non-burstable, varied schedules) | ElectricityMaps, Boavizta, AWS Pricing/CloudTrail/CloudWatch | JSON-Artefakte inkl. Zusammenfassung |
| Carbon-aware Scheduling | Gezielte Start/Stop-Aktionen mit Vorher/Nachher-Vergleich | CloudTrail, CloudWatch, ElectricityMaps | Ereignistimeline, Laufzeitdeltas, Carbon-Vergleich |
| Kostenvalidierung | Abgleich der berechneten Monatskosten mit Cost Explorer | AWS Cost Explorer, Pricing API | Bericht zur Validierungsabweichung |
| Fehlerhandling | Simulationslauf mit API-Verfügbarkeitsproblem | ElectricityMaps oder CloudTrail | Logauszug + Hinweis im Dashboard |

## Datenfluss
1. **Vorbereitung:** CloudTrail mit 30 Tagen Aufbewahrung aktivieren, CloudWatch-Metriken prüfen, Credentials in `.env` pflegen.
2. **Ausführung:** `tests/integration/test_pipeline.py` ruft `DataProcessor.get_infrastructure_data()` auf, speichert `dashboard_data.json` und `metadata.json` unter `artifacts/integration/<timestamp>/`.
3. **Verifikation:** Kostenwerte gegen Cost Explorer (±2 % Toleranz) prüfen, Laufzeiten mit CloudWatch-Mittelwerten abgleichen, Auffälligkeiten dokumentieren.
4. **Wiederholung:** `make test-integration` als Standardkommando nutzen; Artefakte lokal archivieren, vertrauliche Rohdaten nicht ins Repository übernehmen.

## Werkzeugempfehlungen
- Markierung `@pytest.mark.integration` zur Trennung von Unit-Tests.
- Bei Bedarf Aufzeichnungstools (z. B. pytest-recording) einsetzen, unter Berücksichtigung von Zugangsrichtlinien.
- Ergänzende Skripte oder Notebooks zur Auswertung der Artefakte dokumentieren.

## Dokumentation
- Ergebnisse in `docs/validation-results.md` fortschreiben.
- Relevante Artefakt-Auszüge bzw. Statistiken als Anhang in der Arbeit referenzieren.

## Offene Punkte
1. Erweiterung des Integrationstests um Szenario-Läufe (Start/Stop, Fehlerfälle).
2. Geplante Auswertungsfrequenz festlegen (z. B. wöchentlich).
3. Einbettung der Ergebnisse in Präsentation und Verteidigungsmaterial.
