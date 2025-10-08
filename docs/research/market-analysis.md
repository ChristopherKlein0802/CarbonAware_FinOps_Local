# Markt- und Wettbewerbsanalyse

Diese Analyse untersucht, inwieweit bestehende Lösungen die gleichzeitige Erfassung von Cloud-Kosten und CO₂-Emissionen unterstützen und welche Lücken der entwickelte Prototyp adressiert.

## 1. Untersuchungsrahmen
- **Forschungsfrage:** Wie lässt sich ein integriertes Monitoring-System entwickeln, das Kosten und CO₂-Emissionen simultan erfasst, und welche Vorteile bietet dieser Ansatz gegenüber getrennten Lösungen?
- **Zielgruppe:** Deutsche KMU mit bis zu 100 Instanzen in AWS `eu-central-1`.
- **Methodik:** Desk-Research (Gartner Market Guide, Green Software Foundation Directory, Anbieterwebseiten), ergänzt um Literatur zu FinOps und Carbon Accounting.

## 2. Marktsegmente
| Segment | Beispiele | Stärken | Grenzen im Kontext der Forschungsfrage |
|---------|-----------|---------|-----------------------------------------|
| Cloud-FinOps-Plattformen | CloudHealth, nOps, Apptio | Ausgereifte Kostenoptimierung, Reporting | Fehlen CO₂-Daten oder bieten diese nur als Zusatzmodul |
| Carbon-Reporting-Tools | Cloud Carbon Footprint, Persefoni | Ausführliche CO₂-Bilanzen | Keine tiefgehende Kostenintegration, oft ohne Echtzeitnetzbezug |
| Provider-eigene Angebote | AWS Cost Explorer, AWS Customer Carbon Footprint Tool | Direkte Integration, geringe Einstiegshürde | Kosten- und Emissionssicht getrennt, regionale Besonderheiten kaum abbildbar |
| Open-Source/Academic Tools | GSF SCI, Cloud Carbon Footprint (OSS), Forschungsvorhaben | Transparente Modelle | Hoher Implementierungsaufwand, fehlende Business-Cases für KMU |

## 3. Preis- und Funktionsvergleich (Stand 09/2025)
| Anbieter | Monatliche Kosten (Listenpreis) | Kostenanalyse | CO₂-Analyse | Echtzeit-Strommix | KMU-Fokus |
|----------|-------------------------------|---------------|--------------|-------------------|-----------|
| CloudHealth | ≥ €300 | ✔︎ | ✘ | ✘ | ✘ |
| nOps | ≥ €150 | ✔︎ | ✘ | ✘ | Teilweise |
| Cloud Carbon Footprint | OSS / Support-Pakete | ✘ | ✔︎ | ✘ | ✘ |
| AWS Cost Explorer + AWS Carbon Tool | inkludiert | ✔︎ | ✔︎ (aggregiert) | ✘ | ✘ |
| Carbon-Aware FinOps Prototyp | API-Kosten ≈ €5–20 | ✔︎ | ✔︎ | ✔︎ (ElectricityMaps) | ✔︎ |

> **Hinweis:** Preise basieren auf veröffentlichten Informationen ohne individuelle Rabatte. Der Prototyp nutzt ausschließlich API-Kosten und vermeidet Lizenzgebühren.

## 4. Abgeleitete Lücke
1. **Integration:** In der untersuchten Stichprobe existiert keine Lösung, die Kosten, Emissionen und regional spezifische Strommixdaten zusammenführt.
2. **Transparenz:** Viele Tools verwenden Durchschnittswerte oder heuristische Laufzeiten; die Kombination aus CloudTrail und ElectricityMaps adressiert diesen Mangel.
3. **KMU-Perspektive:** Die meisten Angebote sind auf Enterprise-Szenarien ausgelegt; die Kostenstruktur ist für kleine Unternehmen häufig zu hoch.

## 5. Relevanz für die Bachelorarbeit
- **Teilfrage 1:** Die Analyse zeigt konkrete Defizite existierender Tools bei der Integration von Kosten- und Emissionsmetriken.
- **Teilfrage 3:** Der Prototyp positioniert sich als kostengünstige Alternative mit dokumentiertem Mehrwert (z. B. gleichzeitige Visualisierung, Validierungsfaktoren).
- **Teilfrage 4:** Die Marktbeobachtungen begründen die Fokussierung auf deutsche KMU und legen potenzielle Erweiterungen auf weitere Regionen nahe.

## 6. Limitationen
- Desk-Research ersetzt keine vollständige Marktstudie; nicht alle Anbieter veröffentlichen detaillierte Funktionslisten.
- Preise können je nach Vertragsgestaltung abweichen.
- Die Analyse konzentriert sich auf AWS; Multi-Cloud-Angebote wurden nur exemplarisch betrachtet.

## 7. Quellen
Verweise sind in `docs/references.md` hinterlegt (insbesondere [6]–[12], [15], [20]).

Diese Marktanalyse dient als Grundlage für die Herleitung der Anforderungen an den Prototypen und die Bewertung seines Mehrwerts gegenüber separaten Tools.
