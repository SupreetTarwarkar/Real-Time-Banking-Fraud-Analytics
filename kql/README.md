# KQL Fraud Detection

KQL queries evaluate transaction patterns in Eventhouse and prepare consolidated fraud-risk alerts.

| Script | Function |
|---|---|
| [`06_Final_FraudAlerts_Updated.kql`](06_Final_FraudAlerts_Updated.kql) | Five detection scenarios, severity assignment, scenario consolidation and alert details |
| [`07_Persist_FraudAlerts_Updated.kql`](07_Persist_FraudAlerts_Updated.kql) | Writes consolidated results to the `FraudAlerts` table |

**Detection scenarios:** High Velocity, Spending Burst, Unusual High Value, Unusual Transaction Time and Impossible Travel.

Multi-scenario matches are consolidated into a single alert and classified as Critical when two or more distinct rules match.

**Persistence behavior:** The second script uses **`.set-or-replace FraudAlerts`**, which replaces the target table's contents. It is intended for a controlled development workflow and is not an incremental production ingestion pattern.

[Detection rules](../README.md#fraud-detection-rules) · [Business requirements](../docs/Final_BRD.md)

---

[⬅ Back to Main README](../README.md)
