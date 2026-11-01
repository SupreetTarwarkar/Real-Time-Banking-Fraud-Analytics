# Validation and interpretation

| Month | Historical transactions | Simulator-injected anomaly cases |
|---|---:|---:|
| July 2026 | 68,400 | 2,674 |
| August 2026 | 77,600 | 3,197 |
| September 2026 | 94,000 | 3,807 |
| **Total** | **240,000** | **9,678** |

The simulator-injected cases and persisted KQL `FraudAlerts` are different populations. A current persisted alert count has not been independently established here.

- Five deterministic KQL rules; **no ML**.
- Overlapping distinct scenarios escalate to Critical.
- Consolidated potential exposure is the maximum applicable scenario exposure, not a sum of overlapping amounts.
- Alert Rate uses **distinct flagged transaction IDs** divided by all transactions in the matching time window.
- Potential exposure is **not** actual monetary loss.
- The dashboard's last-hour query refresh is distinct from transaction ingestion, KQL persistence and Power BI refresh.
- Activator `Critical_Fraud_Email_Alert` was configured, but successful email receipt was not verified.
- `07_Persist_FraudAlerts_Updated.kql` contains `.set-or-replace`, which overwrites existing persisted alerts.
