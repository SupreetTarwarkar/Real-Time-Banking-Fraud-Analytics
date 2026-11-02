# Business insights and analytical findings

**Project:** Real-Time Banking Fraud Analytics | Microsoft Fabric, KQL and Power BI  
**Data classification:** **100% synthetic**. Figures are demonstrations of the simulator and dashboard, **not real banking fraud statistics**.

## Evidence and time-period boundaries

- **July–September 2026:** 240,000-row local `FactTransactions_202607_202609.csv` independently inspected for row counts, unique IDs, nulls, transaction values and channel mix. Historical Power BI screenshots supply alert and potential-exposure KPIs.
- **July–November 2026:** Later Power BI screenshots supply additional October/November transaction and alert counts, severity, geography and potential-exposure figures. **As of 1 November 2026, the November 2026 data include future-dated synthetic test transactions**; they are not observations from elapsed real time.
- The local simulator ground-truth file contains 9,678 injected anomaly cases with 9,678 distinct triggering transaction IDs. The historical Power BI screenshot **also displays 9,678 fraud-risk alerts**. Matching totals **do not independently prove** one-to-one KQL detection accuracy or ID-level reconciliation.

## 1. Historical baseline: July–September 2026

| Metric | Value | Source |
|---|---:|---|
| Transactions | **240,000** | Local FactTransactions CSV, independently counted |
| Unique transaction IDs | **240,000** | Local FactTransactions CSV |
| Unique customers | **10,000** | Local FactTransactions CSV |
| Missing values across the 10 transaction fields | **0** | Local FactTransactions CSV |
| Transaction amount | **₹245.55 Cr** | CSV sum: ₹2,455,534,267.18 |
| Fraud-risk alerts shown | **9,678** | Power BI Fraud Overview screenshot |
| Flagged transaction rate shown | **4.03%** | Power BI Fraud Overview screenshot |
| Potential fraud exposure shown | **₹26.81 Cr** | Power BI Fraud Overview screenshot; *not confirmed loss* |
| Critical alerts shown | **1,440** | Power BI Fraud Investigation screenshot |
| Multi-scenario alerts shown | **480** | Power BI Fraud Investigation screenshot |

### Finding A: The highest alert count was not the highest alert rate

| Month | Transactions | Alerts displayed | Alerts ÷ transactions |
|---|---:|---:|---:|
| July | 68,400 | 2,674 | **3.91%** |
| August | 77,600 | 3,197 | **4.12%** |
| September | 94,000 | 3,807 | **4.05%** |
| **Total** | **240,000** | **9,678** | **4.03%** |

**Interpretation:** September produced the **most alerts (3,807)**, but August had the **highest normalized alert rate (4.12%)**. Raw counts increase with transaction volume; risk monitoring should compare rates using consistent denominators. These are synthetic outcomes, not estimates of real-world fraud prevalence.

### Finding B: High-volume channels are not necessarily highest-value channels

The following figures were **calculated directly from the 240,000-row CSV**, not inferred from chart labels.

| Payment channel | Transactions | Share of count | Total amount | Share of amount |
|---|---:|---:|---:|---:|
| UPI | 106,063 | **44.19%** | ₹50.24 Cr | **20.46%** |
| Credit Card | 34,602 | 14.42% | **₹58.85 Cr** | 23.96% |
| Net Banking | 27,400 | 11.42% | **₹58.62 Cr** | 23.87% |
| IMPS | 23,352 | 9.73% | ₹50.02 Cr | 20.37% |
| Debit Card | 31,572 | 13.16% | ₹20.09 Cr | 8.18% |
| ATM | 17,011 | 7.09% | ₹7.74 Cr | 3.15% |

**Interpretation:** UPI accounts for **44.19% of transactions but only 20.46% of transaction value**. Credit Card and Net Banking have fewer transactions but each contribute about 24% of value. The distinction matters when designing channel-level monitoring; transaction frequency alone does not establish monetary exposure.

## 2. Extended synthetic simulation: July–November 2026

These figures come from the **later Power BI screenshots**, not from the locally inspected July–September CSV.

| Month | Transactions shown | Alerts shown | Calculated alert rate |
|---|---:|---:|---:|
| July | 68,400 | 2,674 | 3.91% |
| August | 77,600 | 3,197 | 4.12% |
| September | 94,000 | 3,807 | 4.05% |
| October | 81,000 | 3,156 | 3.90% |
| November | 88,000 | 3,410 | 3.88% |
| **Total** | **409,000** | **16,244** | **3.97%** |

| Extended dashboard KPI | Value |
|---|---:|
| Synthetic customers | 10,000 |
| Total transaction amount | **₹394.73 Cr** |
| Potential fraud exposure | **₹45.28 Cr** |
| Critical alerts | **2,465** |
| Multi-scenario alerts | **796** |
| Critical-alert potential exposure | **₹12.42 Cr** |
| Multi-scenario-alert potential exposure | **₹3.08 Cr** |

### Finding C: A modest change in the simulated alert rate

The October–November simulated extension contains **169,000 transactions** and **6,566 alerts**, a **3.89%** rate versus **4.03%** in July–September: approximately **0.15 percentage points lower**. This is a result of **controlled synthetic simulation**, not evidence that real banking risk improved.

### Finding D: Multi-scenario alerts affect investigation priority

Of the **2,465** Critical alerts, **796** are labeled multi-scenario, approximately **32.3% of Critical alerts**. The implemented KQL elevates a consolidated alert to Critical when **two or more distinct scenarios** are triggered. It also takes the **maximum** applicable scenario exposure rather than adding overlapping scenario exposures. This makes multi-rule investigation and exposure deduplication meaningful implementation topics.

### Finding E: Geography changes the investigation view

- **Maharashtra**: highest state alert count, **1,286**.
- **New Delhi**: highest city alert count, **476**.
- **Bengaluru**: highest city-level potential exposure, **₹1.42 Cr**.

The city with the most alerts is **not** the city with the highest displayed potential exposure. Counts and exposure should be examined separately. These are **simulated** geographic patterns; they do not imply any city has higher actual fraud risk.

### Finding F: Scenario and channel patterns

- **Spending Burst** is the largest scenario in the extended dashboard's exposure breakdown (**₹287.9 million / ₹28.79 Cr**).
- **Credit Card** is the largest payment channel in its exposure breakdown (**₹303.8 million / ₹30.38 Cr**).
- The scenario-by-channel heatmap shows **High Velocity** and **Impossible Travel** prominently under UPI, **Spending Burst** under Credit Card, and **Unusual High Value** under Net Banking.

**Important:** These are **charted breakdowns, not reconciled additive totals**. The scenario and channel charts each sum to approximately **₹48.37 Cr**, whereas the headline potential-exposure KPI is **₹45.28 Cr**. The **₹3.09 Cr difference remains to be reconciled**. It could reflect different aggregation or overlap handling, but that cause has **not been verified**. Do **not** sum the bars or claim the charts tie to the headline.

## 3. Operational monitoring snapshot

A single screenshot of `RealTime_Banking_Fraud_Monitoring` shows a **last-hour** snapshot: **282 transactions, 14 alerts, 1 Critical alert, ₹310.3K potential exposure, 4.96% alert rate**. These are **time-window-specific**, not lifetime or guaranteed continuously refreshed totals. The dashboard also exposes transaction IDs, customer IDs, locations, amounts, scenario, severity and alert reason for investigation.

## 4. Outstanding quality checks before claiming complete reconciliation

1. **Exposure breakdowns:** Headline **₹45.28 Cr** vs category charts approximately **₹48.37 Cr**; reconcile filters, grouping and overlapping scenarios.
2. **Repeat-alert customers:** Later Risk Patterns KPI shows **5,203**, but the pie categories for 2 and 3 alerts show **3,179 + 1,601 = 4,780**. The **423-customer difference** and displayed **60.77%** require definition/filter verification.
3. **Historical Critical-by-Scenario visual:** The older Fraud Investigation screenshot labels the five base-scenario totals (**2,400 / 2,120 / 1,820 / 1,510 / 1,348**) as Critical-by-Scenario, although the headline Critical count is **1,440**. Do not use that chart as a critical-only distribution until the visual/measure is checked.
4. **Detection accuracy:** A 9,678-to-9,678 total match does not establish an ID-level join between injected ground truth and persisted `FraudAlerts`. Validate true positives, unmatched detections and false positives separately before reporting precision/recall.
5. **Temporal scope:** November 2026 synthetic records extend beyond the publication date of **1 November 2026**. Describe them as future-dated test data.
6. **Activator:** A Critical-alert rule was configured; email receipt and new-only behavior were **not verified**.
7. **Persistence:** `.set-or-replace FraudAlerts` is destructive and does not establish incremental, exactly-once alert ingestion.

## 5. Resume-ready, defensible project bullets

These bullets describe a **portfolio project**, not professional production experience. Retain only activities you can explain in an interview.

- Built an end-to-end **Microsoft Fabric** fraud-risk analytics portfolio using **Eventstream, Eventhouse/KQL, Lakehouse and Power BI**, with **5 explainable detection rules** and a **3-page analytical report**.
- Analyzed **240,000 synthetic historical transactions** across **10,000 customers**, verifying **0 missing transaction fields** and **240,000 unique transaction IDs**, and reported **₹245.55 Cr** in simulated transaction value.
- Developed investigation-oriented reporting for a **409,000-transaction synthetic test dataset**, displaying **16,244 fraud-risk alerts**, a **3.97%** flagged rate and **2,465** Critical alerts, with separate rolling-hour operational monitoring.

**AI assistance:** ChatGPT assisted development/debugging of the Python simulator in VS Code. Do not imply the simulator was fully handwritten without AI or that the KQL rules constitute machine learning.

---

*Source basis: local synthetic FactTransactions CSV, local synthetic ground-truth validation file (not committed), verified KQL scripts, and project Power BI/Fabric screenshots. Calculated percentages are rounded to two decimal places.*

---

[⬅ Back to Main README](../README.md)
