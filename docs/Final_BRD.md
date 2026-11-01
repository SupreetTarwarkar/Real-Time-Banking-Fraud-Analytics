# Business Requirements Document
## Real-Time Banking Fraud Analytics

**Version:** 1.0 · **Date:** 01 November 2026  
**Project:** Independent synthetic-data portfolio implementation  
**Stack:** Python · Microsoft Fabric Eventstream · Eventhouse/KQL · Lakehouse · Power BI · Fabric Activator

### 1. Business background and problem statement

Digital banking transactions can exhibit abnormal frequency, spending, location and timing patterns. Fraud-risk teams require an explainable view of potentially suspicious activity, its severity, the associated transaction/customer, and the monetary exposure requiring investigation. Historical reporting alone does not provide an adequate operational view of recent events.

This project demonstrates rule-based fraud-risk analytics with **fully synthetic Indian banking data**. It neither identifies confirmed fraud nor blocks transactions.

### 2. Business objectives

| ID | Business requirement |
|---|---|
| BR-01 | Detect five defined transaction-risk patterns with deterministic, explainable rules. |
| BR-02 | Prioritize investigation using Suspicious, Severe and Critical severity levels and alert reasons. |
| BR-03 | Quantify flagged activity and potential exposure without double-counting overlapping scenarios within a consolidated alert. |
| BR-04 | Provide historical Power BI analysis and a separate recent-window operational dashboard. |
| BR-05 | Support a configurable Critical-alert notification rule, subject to independent delivery verification. |

### 3. Key business questions

- How many transactions are monitored, and what share of **distinct transactions** is flagged?
- Which fraud-risk scenarios, severity levels, payment channels and locations require attention?
- Which transaction/customer triggered an alert, and what deterministic rule explains it?
- What potential INR exposure is associated with flagged activity?
- How do historical patterns compare with the rolling operational view?

### 4. Data sources and workflow

| Item | Baseline |
|---|---|
| Historical synthetic transactions | **240,000** (Jul 68,400; Aug 77,600; Sep 94,000) |
| Historical period | 1 July–30 September 2026 |
| Synthetic customers | **10,000** |
| Indian locations | **105** |
| Simulator-injected anomaly cases | **9,678** (4.03% of historical transactions) |

The **9,678 injected cases are not the persisted KQL `FraudAlerts` count**.

| Stage | Component | Business role |
|---|---|---|
| Generate and ingest | Python simulator → Eventstream | Create synthetic transactions and route incoming events |
| Store and detect | Eventhouse + KQL | Query `FactTransactions` and consolidate rule-based alerts |
| Model and report | Lakehouse + semantic model + Power BI | Support dimensions, historical KPIs and analytical pages |
| Monitor and notify | Real-Time Dashboard + Activator | Display recent alerts and configure Critical-event notification |

### 5. Fraud detection requirements

| Scenario | Implemented trigger and severity |
|---|---|
| High Velocity | Same customer, fixed 2-minute window: 3 transactions Suspicious; 4–5 Severe; ≥6 Critical |
| Spending Burst | ≥3 transactions in a 15-minute window and cumulative amount ≥₹50,000 Suspicious; ≥₹75,000 Severe; ≥₹1,00,000 Critical |
| Impossible Travel | Consecutive customer transactions ≥500 km apart within 30 minutes Suspicious; ≥800 km within 30 minutes or ≥500 km within 15 minutes Severe |
| Unusual High Value | Net Banking **Fund Transfer** only; amount >₹25,000 and ≥2× prior comparable average. One prior comparable transfer caps severity at Suspicious; with ≥2 prior transfers, ≥3× Severe and ≥4× Critical |
| Unusual Transaction Time | 00:00–05:00 IST; one transaction in a 30-minute window Suspicious; ≥2 Severe |

**Consolidation:** Two or more **distinct scenarios** for one consolidated event escalate final severity to **Critical**. Preserve scenario names and explanatory reasons. Use the **maximum** applicable scenario exposure within the alert rather than summing overlapping scenario exposures.

### 6. KPIs and analytical definitions

| Metric | Business definition |
|---|---|
| Total Transactions | Number of transactions in the selected reporting period |
| Fraud Alerts | Count of rule-generated `FraudAlerts` records; not confirmed fraud |
| Critical Alerts | Alerts whose final severity is Critical |
| Alert Rate | **Distinct flagged transaction IDs ÷ total transactions in the same period × 100** |
| Potential Fraud Exposure | Sum of rule-derived `potential_exposure_inr`; **not realized loss** |

Historical and recent-window measures must use their own matching time filters. Do not interchange simulator-injected cases, alert rows and distinct flagged transactions.

### 7. Dashboard and reporting requirements

| Output | Required content |
|---|---|
| Power BI — Fraud Overview | Historical KPIs, trends, date/context slicers and exposure analysis |
| Power BI — Fraud Investigation | Transaction/customer investigation with scenario, severity and alert-reason context |
| Power BI — Risk Patterns | Geographic map, city/state rankings, channel-risk rate, scenario-by-channel and weekly-risk analysis |
| Real-Time Dashboard | Rolling last-hour **five KPIs**: Transactions, Fraud Alerts, Critical Alerts, Potential Exposure, Alert Rate; plus investigation table |
| Investigation table | Alert ID, Transaction ID, Customer ID, Transaction Location, Amount (INR), Fraud Scenario, Severity, Alert Reason |
| Fabric Activator | `Critical_Fraud_Email_Alert` configured; successful email receipt **not verified** |

Dashboard Live Refresh re-executes queries; it does not itself generate transactions or guarantee that new `FraudAlerts` have been persisted.

### 8. Deliverables and acceptance criteria

| ID | Deliverable | Acceptance evidence |
|---|---|---|
| AC-01 | Synthetic historical dataset | 240,000 records with documented monthly distribution; reference dimensions |
| AC-02 | Five KQL detection rules | Documented thresholds, severity, consolidated reasons and exposure logic |
| AC-03 | Fabric data workflow | Accurate Eventstream, Eventhouse, Lakehouse and persistence pipeline |
| AC-04 | Historical Power BI report | Three analytical pages, filters, labels and validated measures |
| AC-05 | Real-Time Dashboard | Five rolling-hour KPIs and investigation table with correct fields |
| AC-06 | Critical notification rule | Configuration retained; **received email required** before claiming delivery succeeded |
| AC-07 | Portfolio documentation | BRD, source scripts, representative screenshots and accurate README |

### 9. Scope, assumptions and limitations

| In scope | Out of scope / not claimed |
|---|---|
| Synthetic Indian banking transactions and controlled simulated live batches | Real customer/bank data or real-world fraud-incidence estimates |
| Five explainable KQL scenarios and multi-scenario consolidation | Machine learning, predictive scoring or confirmed fraud |
| Historical Power BI and recent-window Eventhouse monitoring | Production payment blocking or enterprise case management |
| Configured Critical-alert Activator rule | Guaranteed email delivery, new-only alerting or uninterrupted 24/7 ingestion |
| Potential exposure and rule-based alert rate | Actual monetary loss, regulatory certification or production readiness |

Business time is interpreted in **IST** where applicable. Event arrival, persisted-alert updates and Power BI refresh are separate processes. Current persisted-alert totals and notification delivery must be independently verified before public reporting.

**Implementation references:** `kql/06_Final_FraudAlerts_Updated.kql`, `kql/07_Persist_FraudAlerts_Updated.kql`, confirmed final Python simulator and completed dashboard evidence.
