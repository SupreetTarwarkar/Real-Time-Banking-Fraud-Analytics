# Challenges and lessons learned

This project was built as a learning and portfolio exercise. The key work was integrating **synthetic streaming, explainable KQL rules, Microsoft Fabric storage/orchestration and Power BI reporting**.

| Challenge | Implementation or lesson | Evidence |
|---|---|---|
| Designing realistic synthetic data without using real customer information | Python generator with historical and controlled live modes; 10,000 synthetic customers and Indian location dimension | `python/` and `data/` |
| Complete date coverage | Earlier simulation required coverage fixes for the 1st and 28th–31st of relevant months; the historical baseline covers July–September | Final simulator and historical transaction CSV |
| Five different fraud-risk patterns | Used fixed time-window aggregation, customer-level transfer history, IST conversion and geospatial distance checks | `kql/06_Final_FraudAlerts_Updated.kql` |
| One event matching several rules | Consolidated distinct scenarios, escalated multi-scenario cases to Critical and used maximum applicable exposure to avoid overlap within the same alert | KQL `FinalAlerts` |
| Separating real-time display from persisted data | Learned that Eventstream ingestion, KQL execution, pipeline persistence, dashboard query refresh and semantic-model refresh are separate operations | Fabric pipeline and Real-Time Dashboard |
| Building investigation-ready visuals | Created three Power BI pages with date/geographic filtering, critical alerts, scenario/channel views and risk maps | PBIX and screenshots in companion asset package |
| Avoiding misleading metrics | Compared raw counts with normalized rates; distinguished potential exposure from actual loss and injected anomalies from persisted detections | [Insights](INSIGHTS.md) |
| Reconciling report totals | Identified mismatches between headline exposure and chart breakdowns, and between repeat-customer KPI and chart categories; **reconciliation remains open** | [Outstanding QA checks](INSIGHTS.md#4-outstanding-quality-checks-before-claiming-complete-reconciliation) |
| Managing destructive persistence | `.set-or-replace FraudAlerts` overwrites prior records; needs validation and a safer incremental approach for production use | `kql/07_Persist_FraudAlerts_Updated.kql` |
| Alert notifications | Configured Fabric Activator for Critical events, but successful email delivery was not independently verified | Project configuration |
| Python expertise and responsible AI use | Used **ChatGPT to assist Python simulator development and debugging in VS Code**; concentrated on understanding inputs, detection logic, outputs, Fabric integration and reporting. This is **AI-assisted coding**, not a claim of advanced independent Python engineering | Final Python simulator |

## Next validation priorities

1. Reconcile the Power BI exposure charts against the headline measure, with matching filter context and distinct alert grain.
2. Check repeat-customer KPI and chart denominators.
3. Verify the historical Critical-by-Scenario visual.
4. Perform an ID-level join of persisted alerts to locally held synthetic ground truth before claiming detection precision/recall.
5. Test Fabric Activator delivery and duplicate-notification behavior in a controlled environment.
6. Replace destructive alert-table rebuilds with an appropriately validated incremental persistence strategy if extending the project.

No real bank data, production fraud-prevention accuracy, uninterrupted service or confirmed financial loss is claimed.

---

[⬅ Back to Main README](../README.md)
