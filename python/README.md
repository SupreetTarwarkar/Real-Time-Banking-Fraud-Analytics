# Python: synthetic transaction simulator

| File | Purpose |
|---|---|
| [`RealTime_Banking_Fraud_FINAL.py`](RealTime_Banking_Fraud_FINAL.py) | Confirmed final synthetic banking transaction simulator, with historical and controlled live modes |
| [`generate_dim_customer_FINAL.py`](generate_dim_customer_FINAL.py) | Generates synthetic customer dimension data |
| [`generate_dim_location_FINAL.py`](generate_dim_location_FINAL.py) | Generates synthetic location reference data |
| [`requirements.txt`](requirements.txt) | Python dependencies: NumPy, pandas and Azure Event Hubs SDK |

From the **repository root**:

```bash
python -m pip install -r python/requirements.txt
python python/RealTime_Banking_Fraud_FINAL.py
```

**Simulator modes:** Option 1 generates the historical July–September 2026 simulation; Option 2 runs controlled live-mode synthetic generation. Configure Fabric/Eventstream credentials privately before attempting to send events. Re-running may resend events.

**Development disclosure:** ChatGPT assisted Python simulator development and debugging in VS Code. This is an AI-assisted learning project, not a claim of independent advanced Python engineering.

See [synthetic sample data](../data/README.md), [architecture](../README.md#3-tools-and-architecture) and [technical lessons](../docs/CHALLENGES_AND_LEARNINGS.md).

---

[⬅ Back to Main README](../README.md)
