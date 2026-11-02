# Python Transaction Simulator

The Python scripts generate synthetic transaction events and reference dimensions used by the Microsoft Fabric analytical workflow.

| File | Function |
|---|---|
| [`RealTime_Banking_Fraud_FINAL.py`](RealTime_Banking_Fraud_FINAL.py) | Historical and controlled live-mode transaction generation |
| [`generate_dim_customer_FINAL.py`](generate_dim_customer_FINAL.py) | Synthetic customer dimension |
| [`generate_dim_location_FINAL.py`](generate_dim_location_FINAL.py) | Indian location dimension |
| [`requirements.txt`](requirements.txt) | NumPy, pandas and Azure Event Hubs SDK |

### Execution

Run from the repository root:

```bash
python -m pip install -r python/requirements.txt
python python/RealTime_Banking_Fraud_FINAL.py
```

**Option 1:** Historical July–September 2026 generation.  
**Option 2:** Controlled live-mode synthetic generation.

Fabric/Eventstream connection settings must be supplied privately. Running the simulator again may resend transactions.

**Development:** Python scripting and debugging were carried out in VS Code with ChatGPT assistance.

[View the data samples](../data/README.md) · [Architecture](../README.md#architecture-and-technology)

---

[⬅ Back to Main README](../README.md)
