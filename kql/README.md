# KQL Fraud Detection

This project uses Microsoft Fabric Eventhouse and Kusto Query Language (KQL) to identify suspicious patterns in **synthetic banking transactions**. Five rules generate explainable risk signals, which are then consolidated into investigation alerts. A triggered rule is **not proof of fraud**.

## Query files

| Query | Purpose |
|---|---|
| [00 - Create FactTransactions](00_Create_FactTransactions.kql) | Creates the ten-column Eventhouse table used for transaction ingestion |
| [01 - High Velocity](01_High_Velocity.kql) | Detects unusually frequent transactions in short customer-level windows |
| [02 - Spending Burst](02_Spending_Burst.kql) | Detects multiple transactions with a high combined amount |
| [03 - Unusual High Value](03_Unusual_High_Value.kql) | Compares a Net Banking fund transfer with the customer's earlier comparable transfers |
| [04 - Unusual Transaction Time](04_Unusual_Transaction_Time.kql) | Identifies transactions during configured overnight hours in IST |
| [05 - Impossible Travel](05_Impossible_Travel.kql) | Detects implausibly fast changes between transaction locations |
| [06 - Final FraudAlerts](06_Final_FraudAlerts_Updated.kql) | Combines all five rules, resolves overlapping matches and determines final alert severity |
| [07 - Persist FraudAlerts](07_Persist_FraudAlerts_Updated.kql) | Stores consolidated results in the Eventhouse `FraudAlerts` table |

## Detection scenarios

### 1. High Velocity

**What it means:** A customer makes several payments or transfers in a very short time. A sudden burst can indicate automated attempts, account misuse or rapid movement of funds, although legitimate repeated payments can also trigger it.

**Project rule:** Count transactions per customer in a fixed **2-minute window**.

- **Suspicious:** 3 transactions
- **Severe:** 4-5 transactions
- **Critical:** 6 or more transactions

**Example:** Six transactions from the same customer fall within one 2-minute window. The rule generates a Critical High Velocity signal.

### 2. Spending Burst

**What it means:** A customer makes several transactions whose **combined value** is unusually high within a short interval. Unlike High Velocity, this rule considers both transaction count and total spending.

**Project rule:** At least **3 transactions in a fixed 15-minute window**, with a combined amount of **INR 50,000 or more**.

- **Suspicious:** INR 50,000 to below INR 75,000
- **Severe:** INR 75,000 to below INR 1,00,000
- **Critical:** INR 1,00,000 or more

**Example:** Three transactions of INR 20,000, INR 35,000 and INR 50,000 occur within the same 15-minute window. Their INR 1,05,000 total triggers a Critical Spending Burst signal.

### 3. Unusual High Value

**What it means:** A transfer is substantially larger than the customer's previous comparable activity. A behavioural comparison is more informative than treating every large payment as suspicious.

**Project rule:** Evaluate **Net Banking - Fund Transfer** transactions above **INR 25,000** and at least **2 times** the customer's previous average for the same transaction category.

- **Suspicious:** 2x to below 3x the previous average
- **Severe:** 3x to below 4x the previous average, with at least 2 earlier comparable transfers
- **Critical:** 4x or more, with at least 2 earlier comparable transfers

When only **one** earlier comparable transfer exists, severity is capped at **Suspicious** because the historical baseline is limited.

**Example:** A customer whose earlier comparable transfers average INR 20,000 makes an INR 80,000 transfer. With sufficient prior history, the 4x increase triggers Critical severity.

### 4. Unusual Transaction Time

**What it means:** Activity occurs during a configured overnight period when a customer's transactions may warrant additional review. Late-night activity alone does not establish fraud.

**Project rule:** Identify transactions between **00:00 and 05:00 IST**, grouped by customer into fixed **30-minute windows**.

- **Suspicious:** 1 transaction in the window
- **Severe:** 2 or more transactions in the window

**Example:** Two transactions occur at 02:05 AM and 02:12 AM IST for the same customer. They fall in the same 30-minute window and trigger Severe severity.

### 5. Impossible Travel

**What it means:** Two consecutive transactions for the same customer appear to originate from locations too far apart to be physically reached within the elapsed time. This may indicate account compromise, but location-data errors, remote access and shared credentials can also explain a signal.

**Project rule:** Compare consecutive customer transactions using city coordinates from the external `dimlocation` table.

- **Suspicious:** At least **500 km** apart within **30 minutes**
- **Severe:** At least **800 km** apart within 30 minutes, or at least **500 km** apart within 15 minutes

**Example:** A customer's transaction is recorded in Mumbai and another approximately 800 km away 20 minutes later. The rule flags Severe Impossible Travel risk.

**Location limitation:** The query uses transaction-associated location coordinates. These are not verified GPS travel records and do not establish the customer's physical movement.

## Alert consolidation and persistence

**06 - Final FraudAlerts:** Combines the five rule outputs. When multiple distinct scenarios are associated with the same triggering transaction and timestamp, they are consolidated into one alert, preserving scenario names and reasons. **Two or more distinct scenarios are classified as Critical**. For overlapping detections, the consolidation uses the maximum scenario exposure rather than summing overlapping amounts.

**07 - Persist FraudAlerts:** Writes the consolidated results to the `FraudAlerts` Eventhouse table using `.set-or-replace`. **This replaces existing table contents**, so it is appropriate only for a controlled rebuild, not incremental production processing.

## Regulatory context

The Reserve Bank of India identifies transaction velocity, time zones, geo-location, IP origin and unusual customer behaviour as relevant parameters for fraud-risk monitoring. Its fraud-risk management framework also emphasizes early warning signals and analysis of unusual digital transactions.

**Important:** The time windows, distance limits, transaction counts, amounts and severity categories above are **project-defined thresholds**, not thresholds prescribed or endorsed by RBI. This is a synthetic, rule-based analytics demonstration, not an RBI-certified fraud detection system.

**RBI references:**
- [Master Direction - Security Controls for Digital Payment Products and Services (2021), paragraphs 36-38](https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=12032)
- [Fraud Risk Management in Commercial Banks and AIFIs Directions, 2024](https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=12702)
- [Master Directions on Cyber Resilience and Digital Payment Security Controls for non-bank PSOs (2024)](https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=12715)

[Project overview](../README.md) | [Business insights](../docs/INSIGHTS.md)
