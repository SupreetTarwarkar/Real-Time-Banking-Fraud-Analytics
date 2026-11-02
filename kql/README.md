# KQL Fraud Detection

Microsoft Fabric Eventhouse queries for transaction schema creation, rule-based fraud-risk detection, consolidated alert persistence and alert analysis.

## Query files

| File | Purpose |
|---|---|
| [00 - FactTransactions schema](00_Create_FactTransactions.kql) | Defines the ten-field Eventhouse transaction table |
| [01 - High Velocity](01_High_Velocity.kql) | Detects frequent transactions in two-minute customer windows |
| [02 - Spending Burst](02_Spending_Burst.kql) | Flags concentrated spending over 15-minute windows |
| [03 - Unusual High Value](03_Unusual_High_Value.kql) | Compares Net Banking transfers with prior comparable customer activity |
| [04 - Unusual Transaction Time](04_Unusual_Transaction_Time.kql) | Detects activity between midnight and 05:00 IST |
| [05 - Impossible Travel](05_Impossible_Travel.kql) | Compares transaction locations and elapsed time |
| [06 - Final FraudAlerts](06_Final_FraudAlerts_Updated.kql) | Combines five rules, consolidates overlapping scenarios and assigns severity |
| [07 - Persist FraudAlerts](07_Persist_FraudAlerts_Updated.kql) | Writes consolidated alerts into Eventhouse |

The individual scenario queries include monthly summary checks. The final consolidation query also contains a validation-oriented summary. Alert rules are deterministic KQL logic, not a trained fraud prediction model.

## Implementation notes

- Multiple scenarios for the same triggering event are consolidated into a single alert. Two or more distinct matches result in Critical severity.
- The persistence query uses `.set-or-replace FraudAlerts`, which **replaces** existing table contents. Do not run it against data you need to preserve.
- The geographic rule relies on the `dimlocation` external table.

[Project overview](../README.md) | [Business insights](../docs/INSIGHTS.md)
