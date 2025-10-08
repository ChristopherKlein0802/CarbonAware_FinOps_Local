# Developer Handbook

Dieses Handbuch bündelt Richtlinien für Entwicklung und Wartung des Carbon-Aware-FinOps-Prototyps. Es verbindet wissenschaftliche Anforderungen, Coding Standards und aktuelle Wartungsaufgaben.

## 1. Projektkontext
- **Forschungsfrage:** Wie lässt sich ein integriertes Monitoring-System entwickeln, das Kosten und CO₂-Emissionen von Cloud-Infrastrukturen simultan erfasst, und welche Vorteile bietet dieser Ansatz gegenüber bestehenden getrennten Lösungen?
- **Zielgruppe:** Deutsche KMU mit 20–100 AWS-Instanzen in `eu-central-1`.
- **Methodik:** Design-Science-Ansatz mit offen dokumentierten Artefakten und reproduzierbaren Auswertungen.

## 2. Wissenschaftliche Prinzipien
- **No-Fallback-Policy:** API-Fehler führen zu `None` bzw. Warnungen im Dashboard; es werden keine Ersatzwerte generiert.
- **Konservative Formulierungen:** Ergebnisse als Szenarien oder theoretische Potenziale kennzeichnen, solange keine Langzeitmessung vorliegt.
- **Unsicherheitsangaben:** Jede Kennzahl erhält begleitende Fehlerintervalle (z. B. ±5 % ElectricityMaps, ±10 % Boavizta, ±2 % AWS Cost).

## 3. Coding Standards
- **Benennung:** Deskriptive Funktions- und Variablennamen (z. B. `calculate_theoretical_scenarios`).
- **Dokstrings:** Formeln, Datenquellen und Unsicherheit dokumentieren (`Formula: CO₂ = Power × Grid_Intensity × Runtime / 1000`).
- **Fehlerbehandlung:** Spezifische Exceptions bevorzugen, Logeinträge mit Handlungshinweisen versehen.
- **Tests:** Neue Logik durch Unit-Tests (`tests/unit/`) absichern; Integrationstests nutzen reale API-Aufrufe.

## 4. Architekturvorgaben
- **Schichtentrennung:** Logik in den bestehenden Modulen platzieren (`infrastructure`, `services`, `core`, `models`, `utils`, `views`).
- **Konfiguration:** Konstanten zentral (z. B. `src/constants.py`) statt im Code verstreut pflegen.
- **Logging:** INFO für Nutzerereignisse, WARNING/ERROR für Fehler; Debug-Ausgaben optional über `LOG_LEVEL`.

## 5. Workflow und Reviews
1. Literatur/Quellen prüfen und in Kommentaren oder Dokumentation referenzieren.
2. Implementieren, Tests ergänzen, Unsicherheiten aktualisieren.
3. `make test` und bei Bedarf `make test-integration` ausführen.
4. Dokumentation anpassen (`docs/calculations.md`, `docs/validation-results.md`, README, etc.).

**Review-Checkliste**
- Fehlerbehandlung ohne Fallbackwerte?
- Unsicherheiten/Quellen angegeben?
- Tests vorhanden und aktuell?
- Dokumentation spiegelt Änderungen wider?
- Auswirkungen auf Forschungsfrage/Teilfragen berücksichtigt?

## 6. Wartungsstatus (Oktober 2025)
| Modul | Umfang (≈ Zeilen) | Beobachtung |
|-------|-------------------|-------------|
| `src/application/orchestrator.py` | ~219 | Dashboard-Orchestrator (refactored von processor.py), koordiniert Use Cases. |
| `src/domain/services/runtime.py` | ~382 | Runtime-Service für EC2/CloudTrail/CloudWatch, solide DDD-Implementierung. |
| `src/domain/services/carbon.py` | ~218 | Carbon-Daten-Service, ElectricityMaps Integration. |
| `src/application/calculator.py` | ~189 | Business-Case-Calculator (ersetzt BusinessInsightsService), McKinsey/MIT-basiert. |
| `src/presentation/pages/overview.py` | ~81 | ✅ **Modularisiert** - nur noch Orchestrierung. |
| `src/presentation/components/` | ~900 (gesamt) | Neue modulare Komponenten (validation, business_case, metrics), gut testbar. |
| `src/infrastructure/gateways/aws.py` | ~540 | Konsolidierter AWS-Gateway (EC2, CloudTrail, CloudWatch, Cost Explorer, Pricing). |
| `src/infrastructure/cache.py` | ~98 | Konsolidierte Cache-Funktionen, TTL-basiert, keine Duplikate. |
| `src/config/settings.py` | ~142 | Zentralisierte Konfiguration inkl. `EUR_USD_RATE` und Region-Mappings. |

## 7. Stärken
- Konsistente Nutzung von Dataclasses (`src/domain/models.py`), erleichtert Tests und Audits.
- **Clean Architecture**: 4-Layer-Trennung (Domain, Application, Infrastructure, Presentation) mit Dependency Inversion.
- **Modulare UI-Architektur** (`src/presentation/components/`): Overview-Page auf ~81 Zeilen reduziert.
- **Domain-Services** (`src/domain/services/`): Klare Trennung Runtime/Carbon mit Protocol-basierter Dependency Injection.
- Cache-Logik zentralisiert (`src/infrastructure/cache.py`) mit TTL-basiertem Management.
- **Vollständige Type Hints**: `CarbonIntensity` statt `Any` in `DashboardData`.
- **Konfigurierbare Konstanten**: `EUR_USD_RATE` via `.env` überschreibbar.
- Logging & Fehlerbehandlung überwiegend spezifisch (boto3-, ClientError-, Timeout-Handling).
- **80 Unit Tests** (100% passing) mit vollständiger Domain-Logic-Abdeckung.

## 8. Erledigte Verbesserungen (Oktober 2025)
✅ **View-Komponenten modularisiert:** `src/views/components/` mit 5 Komponenten (Grid Status, Metrics, Business Case, Validation, Time Series).
✅ **Typannotationen verbessert:** `Optional[CarbonIntensity]` statt `Optional[Any]` in `DashboardData`.
✅ **Konfiguration zentralisiert:** `EUR_USD_RATE` jetzt in `src/config/settings.py` via `.env` konfigurierbar.
✅ **Service-Layer dokumentiert:** `system-architecture.md` beschreibt nun Runtime-, Carbon- und Business-Services.

## 9. Verbesserungsplan (nächste Schritte)
| Priorität | Maßnahme | Nutzen |
|-----------|----------|--------|
| Hoch | Szenario-Integrationstests | Evidenz für Forschungsfragen, Regressionserkennung |
| Mittel | Infrastructure-Page modularisieren | Analog zu overview.py für Konsistenz |
| Mittel | Carbon-Page Components extrahieren | Vereinheitlichung der View-Struktur |
| Niedrig | Weitere Regionen-Unterstützung | Adaption für internationale KMU |

## 10. Risiken und Gegenmaßnahmen
- **API-Limits:** Cache-Strategien nutzen (`src/infrastructure/cache.py`), um Kosten zu begrenzen.
- **Unvollständige Daten:** Dashboard kennzeichnet Lücken; fehlende Messreihen erneut ausführen.
- **Scope Creep:** Fokus auf KMU und deutsche Stromnetz-Daten beibehalten, Erweiterungen als Future Work markieren.

Dieses Handbuch stellt sicher, dass Entwicklungstätigkeiten konsistent mit den wissenschaftlichen Anforderungen der Bachelorarbeit erfolgen.
