# Business documentation

The project includes a professional 3–4-page Business Requirements Document (BRD), which is supplied in the companion archive as `docs/Final_BRD.docx`. It covers the business problem, five KQL rules, historical and rolling-hour KPI definitions, three Power BI pages, the separate Real-Time Dashboard, acceptance criteria, and explicit limitations.

The portfolio package also includes a Power BI Desktop `.pbix`, representative screenshots, synthetic dimension CSVs and a small synthetic transaction sample. These binary assets are separate from the currently committed text sources.

**Operational boundaries:** `Critical_Fraud_Email_Alert` configured; email receipt not verified. `07_Persist_FraudAlerts_Updated.kql` uses destructive `.set-or-replace`. The 9,678 injected cases are not persisted alert counts.
