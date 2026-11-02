# Validation and interpretation

| Month | Historical transactions (CSV) | Injected synthetic anomaly cases (local ground truth) | Alerts shown in historical Power BI screenshot |
|---|---:|---:|---:|
| July 2026 | 68,400 | 2,674 | 2,674 |
| August 2026 | 77,600 | 3,197 | 3,197 |
| September 2026 | 94,000 | 3,807 | 3,807 |
| **Total** | **240,000** | **9,678** | **9,678** |

**Reconciliation boundary:** The injected-case and dashboard-alert counts match **in aggregate**. This does **not** independently establish that all 9,678 persisted alert IDs match all 9,678 injected triggering IDs. Do not claim precision, recall or zero false positives without an ID-level join and KQL output validation.

**Historical CSV quality checks performed:** 240,000 rows; 240,000 unique transaction IDs; 10,000 distinct customers; **0 missing values** across all 10 transaction fields; total synthetic amount **₹2,455,534,267.18** (**₹245.55 Cr**).

- Five deterministic KQL rules; **no ML**.
- Overlapping distinct scenarios escalate to Critical.
- Consolidated potential exposure is the maximum applicable scenario exposure, not a sum of overlapping amounts **within the same consolidated alert**.
- Alert Rate uses **distinct flagged transaction IDs** divided by all transactions in the matching time window.
- Potential exposure is **not** actual monetary loss.
- The dashboard's last-hour query refresh is distinct from transaction ingestion, KQL persistence and Power BI refresh.
- Activator `Critical_Fraud_Email_Alert` was configured, but successful email receipt was not verified.
- `07_Persist_FraudAlerts_Updated.kql` contains `.set-or-replace`, which overwrites existing persisted alerts.
- The extended July–November dataset contains **future-dated synthetic November 2026 transactions** relative to **1 November 2026**.
- **Open visual reconciliation issues:** extended exposure chart breakdowns approximately **₹48.37 Cr** versus KPI **₹45.28 Cr**; repeat-customer KPI **5,203** versus pie categories **3,179 + 1,601 = 4,780**; historical Critical-by-Scenario bar labels inconsistent with **1,440** Critical-alert headline. See [Insights](INSIGHTS.md#4-outstanding-quality-checks-before-claiming-complete-reconciliation).

---

[⬅ Back to Main README](../README.md)
