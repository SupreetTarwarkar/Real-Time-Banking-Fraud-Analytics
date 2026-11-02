# Business Insights

Analysis of the synthetic transaction data and fraud-risk dashboards developed in **Microsoft Fabric and Power BI**.

## Performance overview

The project includes a **240,000-transaction historical baseline** (July–September 2026) and an **extended 409,000-transaction simulation** (July–November 2026).

| KPI | Historical baseline | Extended simulation |
|---|---:|---:|
| Transactions | **240,000** | **409,000** |
| Customers | **10,000** | **10,000** |
| Fraud-risk alerts | **9,678** | **16,244** |
| Alert rate | **4.03%** | **3.97%** |
| Transaction value | **₹245.55 Cr** | **₹394.73 Cr** |
| Potential exposure | **₹26.81 Cr** | **₹45.28 Cr** |
| Critical alerts | **1,440** | **2,465** |
| Multi-scenario alerts | **480** | **796** |

The extended simulation includes November 2026 test transactions, some future-dated relative to the publication date. All figures describe synthetic activity; potential exposure is not a confirmed loss.

## Fraud Overview: monthly activity

| Month | Transactions | Fraud-risk alerts | Alert rate |
|---|---:|---:|---:|
| July | 68,400 | 2,674 | **3.91%** |
| August | 77,600 | 3,197 | **4.12%** |
| September | 94,000 | 3,807 | **4.05%** |
| October | 81,000 | 3,156 | **3.90%** |
| November | 88,000 | 3,410 | **3.88%** |
| **Total** | **409,000** | **16,244** | **3.97%** |

### 1. Alert volume and alert rate tell different stories

**September** generated the most alerts (**3,807**) alongside the highest transaction volume (**94,000**). **August**, however, had the highest alert rate (**4.12%**).

This distinction matters when comparing periods: a higher alert count can reflect more transaction activity rather than a higher proportion of flagged transactions.

### 2. Transaction volume does not equal transaction value

The following channel distribution was calculated from the **240,000-row July–September transaction dataset**.

| Payment channel | Transactions | Share of transactions | Transaction value | Share of value |
|---|---:|---:|---:|---:|
| UPI | 106,063 | **44.19%** | ₹50.24 Cr | **20.46%** |
| Credit Card | 34,602 | 14.42% | ₹58.85 Cr | 23.96% |
| Net Banking | 27,400 | 11.42% | ₹58.62 Cr | 23.87% |
| IMPS | 23,352 | 9.73% | ₹50.02 Cr | 20.37% |
| Debit Card | 31,572 | 13.16% | ₹20.09 Cr | 8.18% |
| ATM | 17,011 | 7.09% | ₹7.74 Cr | 3.15% |

**UPI** accounted for nearly half of transactions but approximately one-fifth of their total value. **Credit Card** and **Net Banking** each represented almost one-quarter of transaction value with substantially lower transaction counts.

Channel analysis therefore benefits from separate views of **frequency, value and flagged activity**.

## Fraud Investigation: severity and exposure

### 3. Multi-scenario alerts support prioritization

The extended simulation displays:

| Investigation KPI | Value |
|---|---:|
| Critical alerts | **2,465** |
| Multi-scenario alerts | **796** |
| Critical-alert potential exposure | **₹12.42 Cr** |
| Multi-scenario-alert potential exposure | **₹3.08 Cr** |

Multi-scenario alerts represent approximately **32.3% of the Critical alert count**. The KQL consolidation logic raises an alert to Critical when two or more distinct scenarios match, preserving the contributing scenarios and their reasons.

### 4. Exposure varies by fraud scenario and channel

In the extended dashboard's category-level exposure visuals:

- **Spending Burst** has the largest displayed scenario exposure: **₹28.79 Cr**.
- **Credit Card** has the largest displayed payment-channel exposure: **₹30.38 Cr**.

These visuals support scenario and channel comparisons. Their totals are not yet reconciled to the headline exposure measure; the specific discrepancy is recorded in [Data Validation](VALIDATION.md).

## Risk Patterns: location and behavior

### 5. Alert concentration and potential exposure have different geographic leaders

| Geographic metric | Leading location | Value |
|---|---|---:|
| State alert count | **Maharashtra** | **1,286** |
| City alert count | **New Delhi** | **476** |
| City potential exposure | **Bengaluru** | **₹1.42 Cr** |

The leading city for alert frequency differs from the leading city for potential exposure. Using both measures helps distinguish where flagged activity is concentrated from where larger amounts are associated with those alerts.

### 6. Scenario patterns differ by payment channel

The extended scenario-by-channel heatmap highlights:

- **High Velocity** and **Impossible Travel** under **UPI**.
- **Spending Burst** under **Credit Card**.
- **Unusual High Value** under **Net Banking**.

These patterns are properties of the simulated dataset and the configured rules, not estimates of real-world banking fraud behavior.

## Real-Time Monitoring: operational snapshot

The Fabric Real-Time Dashboard provides a separate last-hour monitoring view.

| Last-hour KPI | Captured value |
|---|---:|
| Transactions | **282** |
| Fraud-risk alerts | **14** |
| Critical alerts | **1** |
| Potential exposure | **₹310.3K** |
| Alert rate | **4.96%** |

The investigation table links alerts to transaction IDs, customer IDs, locations, amounts, scenarios, severity and alert reasons. The displayed figures represent one captured window, rather than cumulative totals.

## Data quality and analytical scope

The inspected historical transaction file contained:

- **240,000** rows and **240,000 unique transaction IDs**.
- **10,000** distinct customers.
- **Zero missing values** across the ten transaction fields.
- **₹2,455,534,267.18** in simulated transaction value.

Monthly rates are calculated as the displayed fraud-risk alert count divided by the corresponding transaction count. The extended figures are taken from Power BI screenshots, while the historical transaction and channel calculations are based on the July–September CSV.

[**Data validation and metric definitions**](VALIDATION.md) documents aggregation differences, detection reconciliation and operational limitations.

---

[⬅ Back to Main README](../README.md)
