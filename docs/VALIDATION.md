# Data Validation and Metric Definitions

This document records the datasets, KPI definitions and outstanding reconciliation items associated with the Power BI and Fabric reporting layers.

## Historical transaction validation

The July–September 2026 synthetic transaction dataset was checked for completeness and uniqueness.

| Check | Result |
|---|---:|
| Transaction rows | **240,000** |
| Unique transaction IDs | **240,000** |
| Distinct customers | **10,000** |
| Missing values across 10 transaction fields | **0** |
| Total transaction value | **₹2,455,534,267.18** |

### Monthly transaction and alert distribution

| Month | Transactions | Simulator-injected anomaly cases | Alerts displayed in Power BI |
|---|---:|---:|---:|
| July 2026 | 68,400 | 2,674 | 2,674 |
| August 2026 | 77,600 | 3,197 | 3,197 |
| September 2026 | 94,000 | 3,807 | 3,807 |
| **Total** | **240,000** | **9,678** | **9,678** |

The injected-case and dashboard-alert totals match at the aggregate level. **Transaction-ID-level reconciliation against persisted Eventhouse `FraudAlerts` has not been completed**, so these totals are not a precision or recall measurement.

## KPI definitions

| KPI | Definition |
|---|---|
| **Total Transactions** | Transactions in the selected reporting period |
| **Fraud Alerts** | Records produced by the rule-based fraud-risk detection process |
| **Alert Rate** | Distinct flagged transaction IDs divided by transactions in the matching time period |
| **Critical Alerts** | Consolidated alerts with final severity `Critical` |
| **Multi-scenario Alerts** | Alerts with at least two distinct matched detection scenarios |
| **Potential Fraud Exposure** | Sum of rule-derived exposure estimates at the selected aggregation grain; not actual loss |

Within a consolidated alert, overlapping scenario exposure is represented by the **maximum** applicable amount. The report's aggregate visuals still require reconciliation against this definition.

## Report reconciliation

The following differences were identified while comparing KPI cards and visual breakdowns in the available report screenshots.

| Area | KPI / comparison | Status |
|---|---|---|
| Extended potential exposure | Headline **₹45.28 Cr** vs category charts totaling approximately **₹48.37 Cr** | **Open:** reconcile measure grain, filter context and overlap handling |
| Repeat-alert customers | KPI **5,203** vs displayed 2- and 3-alert categories **3,179 + 1,601 = 4,780** | **Open:** verify customer definitions and filters |
| Historical Critical-by-Scenario chart | Scenario bars labeled **2,400 / 2,120 / 1,820 / 1,510 / 1,348** vs **1,440** Critical alerts | **Open:** review visual title, measure and filter context |
| Detection accuracy | **9,678** aggregate injected cases and **9,678** historical dashboard alerts | **Open:** validate matching transaction IDs and unmatched cases |
| Activator notifications | `Critical_Fraud_Email_Alert` configured | **Open:** verify email receipt and duplicate behavior |

These are analytical validation items, not confirmed explanations of the differences.

## Data and system scope

- **Synthetic data:** All transaction and customer records are generated for this project.
- **Extended simulation:** November 2026 includes test records that may be future-dated relative to publication.
- **Detection method:** Five deterministic KQL rules; no predictive machine learning.
- **Monitoring window:** The Real-Time Dashboard's last-hour KPIs are distinct from cumulative Power BI measures.
- **Persistence behavior:** `07_Persist_FraudAlerts_Updated.kql` uses `.set-or-replace FraudAlerts`, replacing existing table contents.
- **Alert meaning:** A flagged transaction is a candidate for investigation, not confirmed fraud. Potential exposure is not realized financial loss.

---

[⬅ Back to Main README](../README.md)
