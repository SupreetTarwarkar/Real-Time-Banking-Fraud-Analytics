# KQL: fraud-risk detection and alert persistence

| File | Purpose |
|---|---|
| [`06_Final_FraudAlerts_Updated.kql`](06_Final_FraudAlerts_Updated.kql) | Applies the **five explainable fraud-risk rules**, consolidates scenarios and produces investigation-ready alert records |
| [`07_Persist_FraudAlerts_Updated.kql`](07_Persist_FraudAlerts_Updated.kql) | Persists the consolidated results to the `FraudAlerts` table in Eventhouse |

**Five detection scenarios:** High Velocity, Spending Burst, Unusual High Value, Unusual Transaction Time and Impossible Travel.

**Execution warning:** The persistence script uses **`.set-or-replace FraudAlerts`**, which overwrites existing persisted data. Review the KQL and use a development environment; do not execute against a production table without a safe persistence plan.

The rules are deterministic **KQL**, not machine learning. Read the [architecture and detection explanation](../README.md#4-fraud-detection-logic), [validation](../docs/VALIDATION.md) and [lessons learned](../docs/CHALLENGES_AND_LEARNINGS.md).

---

[⬅ Back to Main README](../README.md)
