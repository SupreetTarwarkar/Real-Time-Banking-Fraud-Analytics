# Synthetic Banking Data

The repository includes reference dimensions and a representative sample of the transaction schema.

| Dataset | Records | Purpose |
|---|---:|---|
| [`DimCustomer.csv`](DimCustomer.csv) | **10,000** | Synthetic customer attributes |
| [`DimLocation.csv`](DimLocation.csv) | **105** | Indian reference locations |
| [`FactTransactions_sample.csv`](FactTransactions_sample.csv) | **200** | Sample transaction structure and fields |

The complete historical transaction export and the simulator's private ground-truth validation data are not part of the public repository. The simulator can regenerate synthetic records, which may differ from the original export.

[Python generation scripts](../python/README.md) · [Historical dataset findings](../docs/INSIGHTS.md)

---

[⬅ Back to Main README](../README.md)
