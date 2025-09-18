# Validierungsergebnisse: Carbon-Aware FinOps Prototyp

## 1. Integrationstest im Überblick
| Datum | Kommando | Artefakte | Anmerkungen |
|-------|----------|-----------|-------------|
| 18.09.2025 | `make test-integration` | `artifacts/integration/20250918T145619/` | Lauf mit ElectricityMaps- und AWS-APIs |

Voraussetzung: `AWS_PROFILE=carbon-finops-sandbox`, `ELECTRICITYMAP_API_KEY`.

## 2. Kennzahlen aus den Artefakten
| Kennzahl | Wert | Quelle |
|----------|------|--------|
| Verarbeitete Instanzen | 4 | `metadata.json` |
| Carbon-Intensität (g CO₂/kWh) | 78,0 | `dashboard_data.json → carbon_intensity.value` |
| Monatliche Gesamtkosten (EUR) | 0,74 | `dashboard_data.json → total_cost_eur` |
| Monatlicher CO₂-Ausstoß (kg) | 0,004 | `dashboard_data.json → total_co2_kg` |
| Laufzeitdaten verfügbar | 4/4 Instanzen | `dashboard_data.json → instances[*].runtime_hours` |

## 3. Interpretation
- CloudTrail lieferte Laufzeitereignisse für alle vier Testinstanzen, sodass Messwerte statt Schätzungen vorliegen.
- ElectricityMaps stellte eine gültige Intensität für `eu-central-1` bereit (78 g CO₂/kWh zum Messzeitpunkt).
- Die geringen Gesamtwerte spiegeln die kurze Messdauer wider; sie dienen als Nachweis der Datenpipeline, nicht als belastbare Extrapolation.

## 4. Abgleich mit Literaturerwartungen
| Aspekt | Literatur | Beobachtung |
|--------|-----------|-------------|
| Laufzeitgenauigkeit | Ziel ±5 % bei ausreichender Datengrundlage [13] | Daten vorhanden, noch keine Langzeitanalyse |
| Kosteneffekte | 15–25 % Einsparpotenzial durch Office-Hours-Scheduling [7] | In diesem Lauf nicht bewertet, da Szenarien fehlen |
| CO₂-Reduktion | 15–35 % durch zeitliche Verschiebung [6], [15] | Noch nicht getestet, Szenario erforderlich |

## 5. Limitationen
- Einzelmessung ohne Zeitreihe.
- Hardwaremodelle und Kosteneinschätzungen sind weiterhin literaturbasiert.
- Artefakte werden lokal gespeichert; für Peer Review sollten relevante Ausschnitte als Anhang bereitgestellt werden.

## 6. Nächste Schritte
1. Wiederholte Messungen (z. B. täglich) zur Analyse von Kosten- und Carbon-Schwankungen.
2. Szenarioexperimente (gezielte Start-/Stop-Zyklen) zur Quantifizierung der Literaturannahmen.
3. Einbindung der Artefakte und Auswertungen in die schriftliche Arbeit.

## 7. Quellen
Die Nummerierung verweist auf `docs/references.md`.
