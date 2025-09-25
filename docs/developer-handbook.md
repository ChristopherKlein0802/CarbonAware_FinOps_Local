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
- **Schichtentrennung:** Logik in den bestehenden Modulen platzieren (`api`, `core`, `models`, `utils`, `views`).
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

## 6. Wartungsstatus (September 2025)
| Modul | Umfang (≈ Zeilen) | Beobachtung |
|-------|-------------------|-------------|
| `src/core/processor.py` | ~400 | Zentrale Geschäftslogik inkl. Validierung. |
| `src/core/tracker.py` | ~300 | Laufzeitverarbeitung mit CloudTrail. |
| `src/views/overview.py` | ~450 | Umfangreiche UI-Komponenten, Kandidat für weitere Aufteilung. |
| `src/api/aws.py` | ~250 | Mehrere AWS-Clients, nutzt zentrale Cache-Helfer. |
| `src/utils/cache.py` | ~150 | Konsolidierte Cache-Funktionen, keine Duplikate. |

## 7. Stärken
- Konsistente Nutzung von Dataclasses (`src/models/`), erleichtert Tests und Audits.
- Cache-Logik zentralisiert (`src/utils/cache.py`).
- Logging & Fehlerbehandlung überwiegend spezifisch (boto3-, ClientError-, Timeout-Handling).

## 8. Verbesserungsplan
1. **View-Komponenten modularisieren:** `src/views/overview.py` in kleinere Dateien aufteilen.
2. **Typannotationen verfeinern:** `Any`-Rückgaben reduzieren, insbesondere in Views.
3. **Szenariobasierte Integrationstests:** Start/Stop-Szenarien ergänzen, um Literaturwerte empirisch zu hinterlegen.
4. **Konfiguration vereinheitlichen:** Verstreute Konstanten (z. B. Wechselkurs) zentralisieren.

| Priorität | Maßnahme | Nutzen |
|-----------|----------|--------|
| Hoch | View-Komponenten modularisieren | Bessere Testbarkeit, klarere Verantwortlichkeiten |
| Mittel | Typannotationen erweitern | Frühzeitige Fehlererkennung, saubere API-Dokumentation |
| Mittel | Szenario-Integrationstests | Evidenz für Forschungsfragen, Regressionserkennung |
| Niedrig | Zentrale Konfiguration | Vereinfachte Adaption für weitere Regionen |

## 9. Risiken und Gegenmaßnahmen
- **API-Limits:** Cache-Strategien nutzen (`src/utils/cache.py`), um Kosten zu begrenzen.
- **Unvollständige Daten:** Dashboard kennzeichnet Lücken; fehlende Messreihen erneut ausführen.
- **Scope Creep:** Fokus auf KMU und deutsche Stromnetz-Daten beibehalten, Erweiterungen als Future Work markieren.

Dieses Handbuch stellt sicher, dass Entwicklungstätigkeiten konsistent mit den wissenschaftlichen Anforderungen der Bachelorarbeit erfolgen.
