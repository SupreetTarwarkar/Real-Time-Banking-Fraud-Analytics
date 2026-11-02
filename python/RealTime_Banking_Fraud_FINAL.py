"""Banking simulator: historical-profiled live fraud activity for Fabric."""
from __future__ import annotations

import calendar
from functools import lru_cache
import hashlib
import json
import math
import os
import random
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

import tkinter as tk
from tkinter import filedialog

INDIA_TZ = timezone(timedelta(hours=5, minutes=30))  # IST has no DST; works on Windows without tzdata
START_DATE = date(2026, 10, 1)  # live start (IST)
HIST_START_DATE = date(2026, 7, 1)
HIST_END_DATE = date(2026, 9, 30)
HIST_MONTH_TARGETS = {(2026, 7): 68_400, (2026, 8): 77_600, (2026, 9): 94_000}
HIST_FRAUD_TARGETS = {(2026, 7): 2_674, (2026, 8): 3_197, (2026, 9): 3_807}
MAX_BATCH_EVENTS = 300  # Limits unconfirmed in-flight work; no time.sleep()
# October/November: fixed exact volumes. December/January are optional examples.
LIVE_FIXED_MONTHS = {
    (2026, 10): (81_000, 3.95),
    (2026, 11): (88_000, 3.90),
    (2026, 12): (84_500, 3.93),
    (2027, 1): (91_000, 3.97),
}
# Later months: bounded deterministic fluctuations (no 110K+ jumps).
FUTURE_TX_BOUNDS = (79_000, 94_000)
FUTURE_MAX_MONTH_CHANGE = 6_000
FUTURE_RATE_BOUNDS = (3.85, 4.05)
NORMAL_OFFHOUR_SHARE = 0.002  # 0.2% 00:00-05:30 IST
NORMAL_EARLY_MORNING_SHARE = 0.002  # 0.2% 05:30-10:30 IST


CHANNELS = ("UPI", "Debit Card", "Credit Card", "IMPS", "Net Banking", "ATM")
CHANNEL_WEIGHTS = (0.43, 0.15, 0.14, 0.10, 0.10, 0.08)
TYPE_BY_CHANNEL = {
    "UPI": (("P2P Transfer", "Merchant Payment"), (0.45, 0.55)),
    "Debit Card": (("Purchase",), (1,)),
    "Credit Card": (("Purchase",), (1,)),
    "IMPS": (("Fund Transfer",), (1,)),
    "Net Banking": (("Fund Transfer", "Bill Payment"), (0.70, 0.30)),
    "ATM": (("Cash Withdrawal",), (1,)),
}
AMOUNT_BANDS = {
    "UPI": (10, 25_000), "Debit Card": (100, 30_000),
    "Credit Card": (200, 75_000), "IMPS": (500, 100_000),
    "Net Banking": (500, 200_000), "ATM": (500, 20_000),
}
MERCHANTS = (
    "Groceries", "Food & Dining", "Fuel", "Shopping", "Utilities", "Travel",
    "Healthcare", "Entertainment", "Education", "Electronics", "Other",
)
MERCHANT_WEIGHTS = (0.18, 0.15, 0.10, 0.15, 0.10, 0.08, 0.07, 0.06, 0.04, 0.04, 0.03)
SCENARIOS = ("High Velocity", "Spending Burst", "Impossible Travel", "Unusual High Value", "Unusual Transaction Time")
UPI_SCENARIO_SHARES = (2475 / 5498, 1448 / 5498, 1575 / 5498)
# Original Jul-Sep dashboard: Credit Card 181.0M, Net Banking 84.9M, UPI 20.7M.
# These are exposure-chart aggregates (not guaranteed additive across alerts).
# Target NEW anomaly-block amounts roughly follow that 63.2 / 29.6 / 7.2 mix.
# Spending Burst: >=50k in 15 min; UHV: >25k and above normal comparable transfers.
LIVE_SPENDING_BURST_TOTAL = 74_000.0
LIVE_UNUSUAL_HIGH_VALUE = 39_000.0
LIVE_AMOUNT_VARIATION = 0.055




def stable_seed(run_id, label):
    return int(hashlib.sha256(f"{run_id}:{label}".encode()).hexdigest()[:16], 16) % (2**32)


def distribute(total, days, rng):
    """Allocate irregular positive daily totals, preserving exact monthly sum."""
    n = len(days)
    groups = [(0, min(10, n)), (min(10, n), min(20, n)), (min(20, n), n)]
    shares = (0.415, 0.335, 0.250)
    group_targets = [round(total * shares[0]), round(total * shares[1])]
    group_targets.append(total - sum(group_targets))
    result = [0] * n
    for (a, b), target in zip(groups, group_targets):
        if a == b:
            continue
        weights = [rng.uniform(0.8, 1.2) for _ in range(a, b)]
        expected = [target * w / sum(weights) for w in weights]
        whole = [math.floor(v) for v in expected]
        for i in sorted(range(len(whole)), key=lambda j: expected[j] - whole[j], reverse=True)[:target - sum(whole)]:
            whole[i] += 1
        result[a:b] = whole
    assert sum(result) == total and min(result) > 0
    return result


def live_month_targets(run_id, year, month):
    key = (year, month)
    if key in LIVE_FIXED_MONTHS:
        return LIVE_FIXED_MONTHS[key]
    if key < (2026, 10):
        raise ValueError("Live data begins October 2026")
    # Walk month-by-month from January 2027 to ensure deterministic resumes.
    prior_tx, prior_rate = LIVE_FIXED_MONTHS[(2027, 1)]
    yy, mm = 2027, 2
    while (yy, mm) <= key:
        rng = random.Random(stable_seed(run_id, f"future-volume-{yy}-{mm}"))
        prior_tx = max(FUTURE_TX_BOUNDS[0], min(FUTURE_TX_BOUNDS[1],
                       prior_tx + rng.randint(-FUTURE_MAX_MONTH_CHANGE, FUTURE_MAX_MONTH_CHANGE)))
        prior_rate = round(rng.uniform(*FUTURE_RATE_BOUNDS), 2)
        yy, mm = (yy + 1, 1) if mm == 12 else (yy, mm + 1)
    return prior_tx, prior_rate


def month_plan(run_id, year, month, historical=False):
    if not historical:
        daily_tx, daily_cases, _ = live_scenario_plan(run_id, year, month)
        return daily_tx, daily_cases
    rng = random.Random(stable_seed(run_id, f"month-{year}-{month}"))
    days = calendar.monthrange(year, month)[1]
    tx_total = HIST_MONTH_TARGETS[(year, month)]
    case_total = HIST_FRAUD_TARGETS[(year, month)]
    # Historical branch preserved: it is not sent when Live is selected.
    return distribute(tx_total, range(days), rng), distribute(case_total, range(days), rng)


def allocate_exact(total, shares):
    expected = [total * share for share in shares]
    counts = [int(x) for x in expected]
    for i in sorted(range(len(counts)), key=lambda j: expected[j] - counts[j], reverse=True)[:total - sum(counts)]:
        counts[i] += 1
    return counts


def scenario_plan(run_id, year, month, historical=False):
    if not historical:
        daily_tx, daily_cases, by_day = live_scenario_plan(run_id, year, month)
        return daily_tx, daily_cases, [scenario for day in by_day for scenario, _ in day]
    daily_tx, daily_cases = month_plan(run_id, year, month, historical=True)
    total = sum(daily_cases)
    shares = (0.248, 0.214, 0.538)
    credit, net, upi = allocate_exact(total, shares)
    hv, travel, offhour = allocate_exact(upi, UPI_SCENARIO_SHARES)
    scenarios = (["High Velocity"] * hv + ["Impossible Travel"] * travel +
                 ["Unusual Transaction Time"] * offhour +
                 ["Spending Burst"] * credit + ["Unusual High Value"] * net)
    rng = random.Random(stable_seed(run_id, f"scenario-plan-{year}-{month}"))
    rng.shuffle(scenarios)
    first_day_cases = daily_cases[0]
    replacements = (i for i in range(first_day_cases, len(scenarios))
                    if scenarios[i] != "Unusual Transaction Time")
    for i in range(first_day_cases):
        if scenarios[i] == "Unusual Transaction Time":
            j = next(replacements)
            scenarios[i], scenarios[j] = scenarios[j], scenarios[i]
    return daily_tx, daily_cases, scenarios


def load_inputs():
    """Require the user to select BOTH dimension CSVs on EVERY launch, in either mode.

    Do not auto-detect CSVs, use old checkpoint paths, or silently reuse paths.
    Validate both files before opening the Eventstream connection or sending data.
    """
    selected = []
    for label in ("DimCustomer.csv", "DimLocation.csv"):
        print(f"Select {label} in the file picker (required for both modes).", flush=True)
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        try:
            path = filedialog.askopenfilename(
                parent=root,
                title=f"REQUIRED - Select {label}",
                filetypes=[("CSV files", "*.csv")],
            )
        finally:
            root.destroy()
        if not path or not Path(path).is_file():
            raise SystemExit(f"{label} was not selected. No transactions sent.")
        selected.append(Path(path))

    customers = pd.read_csv(selected[0])
    locations = pd.read_csv(selected[1])
    required_c = {"customer_id", "home_location_id"}
    required_l = {"location_id", "latitude", "longitude"}
    if not required_c.issubset(customers.columns) or len(customers) != 10_000:
        raise ValueError("DimCustomer must have 10,000 rows and customer_id, home_location_id.")
    if not required_l.issubset(locations.columns) or len(locations) != 105:
        raise ValueError("DimLocation must have 105 rows and location_id, latitude, longitude.")
    if customers["customer_id"].duplicated().any() or locations["location_id"].duplicated().any():
        raise ValueError("Duplicate customer_id or location_id in dimension CSV.")
    if not set(customers["home_location_id"].astype(int)).issubset(set(locations["location_id"].astype(int))):
        raise ValueError("Some customer home_location_id values do not exist in DimLocation.")
    # Reject invalid numeric or missing IDs before any Eventstream send.
    for frame, key in ((customers, "customer_id"), (customers, "home_location_id"),
                       (locations, "location_id")):
        if frame[key].isna().any():
            raise ValueError(f"{key} contains null values.")
    print("Both dimension CSVs loaded and validated.", flush=True)
    return customers, locations, selected


def connection_dialog():
    env = os.getenv("FABRIC_EVENTHUB_CONNECTION_STRING", "").strip()
    if env:
        return env
    root = tk.Tk()
    root.title("Fabric Eventstream Connection")
    root.geometry("780x245")
    root.attributes("-topmost", True)
    root.columnconfigure(0, weight=1)
    tk.Label(root, text="Paste the FULL Eventstream Secondary Connection String", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, padx=16, pady=14, sticky="w")
    tk.Label(root, text="Connection string stays masked and is never saved to disk.").grid(row=1, column=0, padx=16, sticky="w")
    entry = tk.Entry(root, show="*", font=("Consolas", 10))
    entry.grid(row=2, column=0, padx=16, pady=12, sticky="ew")
    status = tk.StringVar(value="")
    tk.Label(root, textvariable=status).grid(row=3, column=0, padx=16, sticky="w")
    frame = tk.Frame(root)
    frame.grid(row=4, column=0, padx=16, pady=10, sticky="w")
    result = {"value": None}

    def paste():
        try:
            entry.delete(0, "end")
            entry.insert(0, root.clipboard_get().strip())
        except tk.TclError:
            status.set("Copy the full connection string first.")

    def connect():
        s = entry.get().strip()
        if not all(x in s for x in ("Endpoint=", "SharedAccessKeyName=", "SharedAccessKey=")):
            status.set("Paste the FULL connection string, not only the key.")
            return
        result["value"] = s
        root.quit()

    tk.Button(frame, text="Paste from Clipboard", command=paste, width=23).pack(side="left", padx=(0, 12))
    tk.Button(frame, text="Connect", command=connect, width=12).pack(side="left", padx=(0, 12))
    tk.Button(frame, text="Cancel", command=root.quit, width=12).pack(side="left")
    root.protocol("WM_DELETE_WINDOW", root.quit)
    root.bind("<Return>", lambda _: connect())
    root.mainloop()
    root.destroy()
    if not result["value"]:
        raise SystemExit("Connection cancelled; no transactions sent.")
    return result["value"]


def create_producer():
    conn = connection_dialog()
    kwargs = {"conn_str": conn}
    if "EntityPath=" not in conn:
        hub = os.getenv("FABRIC_EVENTHUB_NAME", "").strip() or input("Event Hub entity name: ").strip()
        if not hub:
            raise ValueError("Event Hub entity name is required.")
        kwargs["eventhub_name"] = hub
    from azure.eventhub import EventHubProducerClient
    return EventHubProducerClient.from_connection_string(**kwargs)


def context_for(customers, locations, run_id):
    rng = np.random.default_rng(stable_seed(run_id, "customers"))
    customer_ids = customers["customer_id"].astype(int).to_numpy()
    home_map = dict(zip(customers["customer_id"].astype(int), customers["home_location_id"].astype(int)))
    activity = rng.lognormal(0.0, 0.70, size=len(customer_ids))
    activity /= activity.sum()
    loc = locations[["location_id", "latitude", "longitude"]].copy()
    vals = list(loc.itertuples(index=False, name=None))
    # A limited deterministic sample is sufficient to find distant location pairs.
    severe_pairs = []
    for i, (lid1, lat1, lon1) in enumerate(vals):
        for lid2, lat2, lon2 in vals[i+1:]:
            dlat = math.radians(float(lat2) - float(lat1))
            dlon = math.radians(float(lon2) - float(lon1))
            a = math.sin(dlat/2)**2 + math.cos(math.radians(float(lat1))) * math.cos(math.radians(float(lat2))) * math.sin(dlon/2)**2
            km = 12742.0176 * math.asin(min(1.0, math.sqrt(a)))
            if km >= 800:
                severe_pairs.append((int(lid1), int(lid2)))
    if not severe_pairs:
        raise ValueError("DimLocation has no >=800 km pairs for Impossible Travel fraud.")
    return customer_ids, home_map, activity, severe_pairs


def normal_timestamp(rng, midnight, day):
    # Most routine traffic is daytime, with a small amount across other hours.
    # This deliberately reduces false positives under naive UTC off-hours KQL.
    min_second = 5 * 3600 + 30 * 60 if day == 1 else 0
    roll = rng.random()
    if roll < NORMAL_OFFHOUR_SHARE and day != 1:
        second = rng.randrange(0, 5 * 3600 + 30 * 60)
    elif roll < NORMAL_OFFHOUR_SHARE + NORMAL_EARLY_MORNING_SHARE:
        second = rng.randrange(5 * 3600 + 30 * 60, 10 * 3600 + 30 * 60)
    else:
        second = rng.randrange(10 * 3600 + 30 * 60, 24 * 3600)
    second = max(min_second, second)
    return midnight + timedelta(seconds=second, microseconds=rng.randrange(1_000_000))


def normal_record(ctx, rng, nrng, ts, cid=None, *, historical=False):
    customer_ids, home_map, activity, _ = ctx
    if cid is None:
        cid = int(nrng.choice(customer_ids, p=activity))
    channel = rng.choices(CHANNELS, weights=CHANNEL_WEIGHTS)[0]
    tx_type = rng.choices(*TYPE_BY_CHANNEL[channel])[0]
    low, high = AMOUNT_BANDS[channel]
    if channel == "Net Banking" and tx_type == "Fund Transfer":
        low, high = 9_000, 24_000
    amount = low + float(nrng.beta(1.35, 5.2)) * (high - low)
    if ts.day <= 10:
        amount *= rng.uniform(1.03, 1.14)
    elif ts.day >= 21:
        amount *= rng.uniform(0.86, 0.99)
    # Net Banking routine fund transfers remain below the KQL UHV trigger.
    # For other channels, keep the original wider normal amount bands so
    # total transaction value does not collapse relative to July-September.
    ceiling = 22_000.0 if historical or channel in ("Net Banking", "UPI") else high
    amount = round(min(max(amount, low), high, ceiling), 2)
    merchant = "Not Applicable" if tx_type in ("P2P Transfer", "Fund Transfer", "Cash Withdrawal") else rng.choices(MERCHANTS, weights=MERCHANT_WEIGHTS)[0]
    return {
        "transaction_id": "", "transaction_timestamp": ts,
        "customer_id": cid, "amount": amount, "payment_channel": channel,
        "transaction_type": tx_type, "merchant_category": merchant,
        "location_id": int(home_map[cid]), "device_id": f"DEV-{cid}-{rng.randint(1, 3):02d}",
        "transaction_status": rng.choices(("Success", "Failed", "Reversed"), weights=(0.965, 0.025, 0.010))[0],
    }


def fraud_block(ctx, rng, nrng, midnight, scenario, cid, *, historical=False):
    """Keep each fraud case's timestamps in the SAME day and correct KQL bins."""
    def make(ts, **fields):
        row = normal_record(ctx, rng, nrng, ts, cid=cid, historical=historical)
        row.update(fields)
        row["transaction_status"] = "Success"
        return row

    home = int(ctx[1][cid])
    device = f"DEV-{cid}-01"
    if scenario == "High Velocity":
        # Fixed two-minute bin: three events 5, 45, 85 seconds from its start.
        minute = rng.randrange(630, 24*60 - 2, 2)
        base = midnight + timedelta(minutes=minute)
        return [make(base + timedelta(seconds=s), amount=1500.0, payment_channel="UPI", transaction_type="P2P Transfer", merchant_category="Not Applicable", location_id=home, device_id=device) for s in (5, 45, 85)]
    if scenario == "Spending Burst":
        minute = rng.randrange(630, 24*60 - 15, 15)
        base = midnight + timedelta(minutes=minute)
        specs = ((0, "Credit Card", "Purchase"), (4, "Credit Card", "Purchase"), (8, "Credit Card", "Purchase"))
        if historical:
            amounts = (20_000.0, 20_000.0, 20_000.0)
        else:
            total = LIVE_SPENDING_BURST_TOTAL * rng.uniform(1-LIVE_AMOUNT_VARIATION, 1+LIVE_AMOUNT_VARIATION)
            amounts = (round(total * 0.30, 2), round(total * 0.32, 2), round(total * 0.38, 2))
        return [make(base + timedelta(minutes=m), amount=amount, payment_channel=ch, transaction_type=typ, merchant_category="Shopping", location_id=home, device_id=device) for (m, ch, typ), amount in zip(specs, amounts)]
    if scenario == "Impossible Travel":
        minute = rng.randint(630, 24*60 - 21)
        base = midnight + timedelta(minutes=minute)
        loc1, loc2 = rng.choice(ctx[3])
        return [make(base, payment_channel="UPI", transaction_type="P2P Transfer",
                     merchant_category="Not Applicable", amount=1500.0,
                     location_id=loc1, device_id=device),
                make(base + timedelta(minutes=20), payment_channel="UPI",
                     transaction_type="P2P Transfer", merchant_category="Not Applicable",
                     amount=1500.0, location_id=loc2, device_id=device)]
    if scenario == "Unusual High Value":
        minute = rng.randint(630, 24*60 - 1)
        trigger = midnight + timedelta(minutes=minute)
        amount = 180_000.0 if historical else round(
            LIVE_UNUSUAL_HIGH_VALUE * rng.uniform(1-LIVE_AMOUNT_VARIATION, 1+LIVE_AMOUNT_VARIATION), 2
        )
        return [make(trigger, amount=amount, payment_channel="Net Banking",
                     transaction_type="Fund Transfer", merchant_category="Not Applicable",
                     location_id=home, device_id=device)]
    if scenario == "Unusual Transaction Time":
        # Only days 2+ use 00:00-05:00 IST, to avoid UTC month rollover.
        minute = rng.randrange(330, 630, 30) if midnight.day == 1 else rng.randrange(0, 5*60, 30)
        base = midnight + timedelta(minutes=minute)
        return [make(base + timedelta(seconds=s), amount=1200.0, payment_channel="UPI", transaction_type="P2P Transfer", merchant_category="Not Applicable", location_id=home, device_id=device) for s in (10, 70)]
    raise ValueError(scenario)


# Live fraud-case proportions are derived from the 9,678 historical GroundTruth
# records (July-September). This does not read or modify the historical dataset.
# Each combination is reproduced as one consolidated KQL alert when detected.
LIVE_CASE_PROFILE = {
    ("High Velocity", "Suspicious"): 1320,
    ("High Velocity", "Severe"): 720,
    ("High Velocity", "Critical"): 360,
    ("Spending Burst", "Suspicious"): 1180,
    ("Spending Burst", "Severe"): 640,
    ("Spending Burst", "Critical"): 300,
    ("Unusual High Value", "Suspicious"): 1000,
    ("Unusual High Value", "Severe"): 520,
    ("Unusual High Value", "Critical"): 300,
    ("Unusual Transaction Time", "Suspicious"): 1110,
    ("Unusual Transaction Time", "Severe"): 400,
    ("Impossible Travel", "Suspicious"): 728,
    ("Impossible Travel", "Severe"): 620,
    ("High Velocity + Spending Burst", "Critical"): 120,
    ("High Velocity + Unusual High Value", "Critical"): 75,
    ("Spending Burst + Unusual Transaction Time", "Critical"): 70,
    ("Unusual High Value + Impossible Travel", "Critical"): 65,
    ("High Velocity + Impossible Travel", "Critical"): 55,
    ("Unusual Transaction Time + Impossible Travel", "Critical"): 45,
    ("Spending Burst + Unusual High Value", "Critical"): 30,
    ("High Velocity + Unusual Transaction Time", "Critical"): 20,
}
assert sum(LIVE_CASE_PROFILE.values()) == 9678
# Actual historical daily coverage: first 10 / middle 10 / remaining days.
LIVE_TX_SEGMENT_SHARES = (0.397, 0.315, 0.288)
LIVE_CASE_SEGMENT_SHARES = (0.415, 0.315, 0.270)
_LIVE_CUSTOMER_PLANS = {}


def live_segment_days(total, year, month, rng, shares, label):
    """Preserve historical within-month peaks and exact monthly totals."""
    n = calendar.monthrange(year, month)[1]
    bounds = ((0, 10), (10, 20), (20, n))
    quotas = allocate_exact(total, shares)
    result = []
    phase = rng.uniform(0, 2 * math.pi)
    state = rng.uniform(-0.035, 0.035)
    for (start, end), quota in zip(bounds, quotas):
        weights = []
        for i in range(start, end):
            state = 0.65 * state + rng.gauss(0, 0.038 if label == "fraud" else 0.030)
            wave = 0.035 * math.sin(2 * math.pi * i / 8.5 + phase)
            weights.append(max(0.60, 1.0 + state + wave))
        result.extend(allocate_exact(quota, [w / sum(weights) for w in weights]))
    assert len(result) == n and sum(result) == total and min(result) > 0
    return result


@lru_cache(maxsize=16)
def live_scenario_plan(run_id, year, month):
    """Return daily totals and KQL-aligned scenario/severity specifications."""
    rng = random.Random(stable_seed(run_id, f"live-month-{year}-{month}"))
    total_tx, rate = live_month_targets(run_id, year, month)
    total_cases = int(total_tx * rate / 100 + 0.5)
    daily_tx = live_segment_days(total_tx, year, month, rng, LIVE_TX_SEGMENT_SHARES, "tx")
    daily_cases = live_segment_days(total_cases, year, month, rng, LIVE_CASE_SEGMENT_SHARES, "fraud")
    keys = list(LIVE_CASE_PROFILE)
    # Very small reproducible month-to-month variation around historical ratios.
    weights = [LIVE_CASE_PROFILE[k] * rng.uniform(0.98, 1.02) for k in keys]
    quotas = allocate_exact(total_cases, [w / sum(weights) for w in weights])
    specs = [k for key, count in zip(keys, quotas) for k in [key] * count]
    rng.shuffle(specs)
    # First day must not contain IST 00:00-05:00 cases (UTC previous month).
    slots_left = list(daily_cases)
    by_day = [[] for _ in daily_cases]
    specs.sort(key=lambda spec: "Unusual Transaction Time" in spec[0], reverse=True)
    for spec in specs:
        earliest = 2 if "Unusual Transaction Time" in spec[0] else 1
        choices = list(range(earliest - 1, len(daily_cases)))
        day_idx = rng.choices(choices, weights=[slots_left[i] for i in choices])[0]
        if slots_left[day_idx] <= 0:
            raise AssertionError("No daily slot for live scenario")
        slots_left[day_idx] -= 1
        by_day[day_idx].append(spec)
    assert sum(slots_left) == 0
    for day_specs in by_day:
        rng.shuffle(day_specs)
    return daily_tx, daily_cases, by_day


def live_month_customers(ctx, run_id, year, month):
    key = (run_id, year, month)
    if key not in _LIVE_CUSTOMER_PLANS:
        # Avoid assigning successive high-value anomalies to the same customer:
        # prior injected transfers would distort KQL's running-average baseline.
        prior_uhv = set()
        if (year, month) > (2026, 10):
            previous = (date(year, month, 1) - timedelta(days=1))
            previous_plan = live_month_customers(ctx, run_id, previous.year, previous.month)
            prior_uhv.update(previous_plan[3])
            for (rid, py, pm), plan in _LIVE_CUSTOMER_PLANS.items():
                if rid == run_id and (py, pm) < (year, month):
                    prior_uhv.update(plan[3])
        _, daily_cases, by_day_specs = live_scenario_plan(run_id, year, month)
        flat_specs = [spec for day in by_day_specs for spec in day]
        rng = np.random.default_rng(stable_seed(run_id, f"live-customers-{year}-{month}"))
        uhv_indices = [i for i, (scenario, _) in enumerate(flat_specs)
                       if "Unusual High Value" in scenario]
        non_uhv_indices = [i for i in range(len(flat_specs)) if i not in set(uhv_indices)]
        available = ~np.isin(ctx[0], np.fromiter(prior_uhv, dtype=int))
        eligible_ids = ctx[0][available]
        eligible_weights = ctx[2][available]
        if len(eligible_ids) < len(uhv_indices):
            # Beyond the four fixed months, retain a rolling prior-month guard.
            eligible_ids = ctx[0]
            eligible_weights = ctx[2]
        eligible_weights = eligible_weights / eligible_weights.sum()
        uhv_customers = rng.choice(eligible_ids, size=len(uhv_indices),
                                   replace=False, p=eligible_weights)
        other_mask = ~np.isin(ctx[0], uhv_customers)
        other_ids = ctx[0][other_mask]
        other_weights = ctx[2][other_mask]
        other_weights = other_weights / other_weights.sum()
        other_customers = rng.choice(other_ids, size=len(non_uhv_indices),
                                     replace=False, p=other_weights)
        assigned = np.empty(len(flat_specs), dtype=ctx[0].dtype)
        assigned[uhv_indices] = uhv_customers
        assigned[non_uhv_indices] = other_customers
        normal_mask = ~np.isin(ctx[0], assigned)
        normal_ids = ctx[0][normal_mask]
        normal_weights = ctx[2][normal_mask]
        normal_weights = normal_weights / normal_weights.sum()
        by_day = []
        offset = 0
        for count in daily_cases:
            by_day.append(assigned[offset:offset + count])
            offset += count
        # Memory-only plan: no progress journal, JSON, or auxiliary CSV files.
        _LIVE_CUSTOMER_PLANS[key] = (by_day, normal_ids, normal_weights,
                                     set(map(int, uhv_customers)))
    return _LIVE_CUSTOMER_PLANS[key]


def live_moderate_pairs(locations):
    vals = list(locations[["location_id", "latitude", "longitude"]].itertuples(index=False, name=None))
    pairs = []
    for i, (a, lat1, lon1) in enumerate(vals):
        for b, lat2, lon2 in vals[i + 1:]:
            p1, p2 = math.radians(float(lat1)), math.radians(float(lat2))
            dl = math.radians(float(lat2) - float(lat1))
            dn = math.radians(float(lon2) - float(lon1))
            x = math.sin(dl/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dn/2)**2
            km = 12742.0176 * math.asin(min(1.0, math.sqrt(x)))
            if 500 <= km < 800:
                pairs.append((int(a), int(b)))
    if not pairs:
        raise ValueError("DimLocation must contain a 500-799 km pair for Suspicious Impossible Travel.")
    return pairs


def live_fraud_block(ctx, moderate_pairs, rng, nrng, midnight, scenario, severity, cid):
    """Emit the historical five-rule and eight-overlap patterns, with matching triggers."""
    home = int(ctx[1][cid])
    device = f"DEV-{cid}-01"

    def make(ts, *, channel="UPI", tx_type="P2P Transfer", amount=1500.0,
             location_id=None, merchant=None):
        row = normal_record(ctx, rng, nrng, ts, cid=cid, historical=True)
        row.update(payment_channel=channel, transaction_type=tx_type,
                   amount=round(amount, 2), location_id=home if location_id is None else location_id,
                   device_id=device, transaction_status="Success",
                   merchant_category=(merchant if merchant is not None else
                                      ("Not Applicable" if tx_type in ("P2P Transfer", "Fund Transfer", "Cash Withdrawal")
                                       else "Shopping")))
        return row

    def daytime_bin(size=15, *, after_support=False):
        earliest = 840 if after_support else 630
        minute = rng.randrange(earliest, 22 * 60 - size, size)
        return midnight + timedelta(minutes=minute)

    def offhour_bin():
        # Never called on the first day of a month.
        return midnight + timedelta(minutes=rng.randrange(0, 9) * 30, seconds=5)

    def supports():
        # Two comparable Net Banking transfers, separated by hours, preceding UHV.
        return [make(midnight + timedelta(hours=10, minutes=45), channel="Net Banking",
                     tx_type="Fund Transfer", amount=12000),
                make(midnight + timedelta(hours=12, minutes=45), channel="Net Banking",
                     tx_type="Fund Transfer", amount=14000)]

    def uhv_amount(sev):
        # Approximate the original comparable-transfer ratios (KQL decides severity).
        return {"Suspicious": 34000, "Severe": 48000, "Critical": 64000}[sev] * rng.uniform(0.985, 1.015)

    if scenario == "High Velocity":
        n = {"Suspicious": 3, "Severe": 4, "Critical": 6}[severity]
        base = daytime_bin(2)
        return [make(base + timedelta(seconds=80 * i / (n-1))) for i in range(n)]

    if scenario == "Spending Burst":
        total = {"Suspicious": 60000, "Severe": 85000, "Critical": 110000}[severity] * rng.uniform(0.98, 1.02)
        base = daytime_bin(15)
        return [make(base + timedelta(minutes=m), channel="Credit Card", tx_type="Purchase",
                     amount=total * part) for m, part in ((0, .30), (4, .32), (8, .38))]

    if scenario == "Unusual High Value":
        base = daytime_bin(15, after_support=True)
        return supports() + [make(base, channel="Net Banking", tx_type="Fund Transfer",
                                  amount=uhv_amount(severity))]

    if scenario == "Unusual Transaction Time":
        base = offhour_bin()
        n = 1 if severity == "Suspicious" else 2
        # A small share of legitimate payment types is represented in UPI exposure.
        merchant = rng.random() < 0.22
        return [make(base + timedelta(minutes=10*i),
                     channel="UPI", tx_type="Merchant Payment" if merchant else "P2P Transfer",
                     amount=1500.0 if merchant else 1200.0,
                     merchant="Groceries" if merchant else "Not Applicable") for i in range(n)]

    if scenario == "Impossible Travel":
        a, b = rng.choice(moderate_pairs if severity == "Suspicious" else ctx[3])
        base = daytime_bin(30)
        return [make(base, location_id=a), make(base + timedelta(minutes=20), location_id=b)]

    if scenario == "High Velocity + Spending Burst":
        base = daytime_bin(2)
        return [make(base + timedelta(seconds=s), channel="Credit Card", tx_type="Purchase",
                     amount=20000) for s in (5, 45, 85)]

    if scenario == "High Velocity + Unusual High Value":
        base = daytime_bin(2, after_support=True)
        return supports() + [make(base + timedelta(seconds=s)) for s in (5, 45)] + [
            make(base + timedelta(seconds=85), channel="Net Banking", tx_type="Fund Transfer", amount=34000)]

    if scenario == "Spending Burst + Unusual Transaction Time":
        base = offhour_bin()
        return [make(base + timedelta(minutes=m), channel="Credit Card", tx_type="Purchase",
                     amount=20000) for m in (0, 4, 8)]

    if scenario == "Unusual High Value + Impossible Travel":
        a, b = rng.choice(moderate_pairs)
        base = daytime_bin(30, after_support=True)
        return supports() + [make(base, location_id=a), make(base + timedelta(minutes=20),
            channel="Net Banking", tx_type="Fund Transfer", amount=34000, location_id=b)]

    if scenario == "High Velocity + Impossible Travel":
        a, b = rng.choice(moderate_pairs)
        base = daytime_bin(2)
        return [make(base + timedelta(seconds=s), location_id=loc)
                for s, loc in ((5, a), (45, a), (85, b))]

    if scenario == "Unusual Transaction Time + Impossible Travel":
        a, b = rng.choice(moderate_pairs)
        base = offhour_bin()
        return [make(base, location_id=a), make(base + timedelta(minutes=20), location_id=b)]

    if scenario == "Spending Burst + Unusual High Value":
        base = daytime_bin(15, after_support=True)
        return supports() + [
            make(base, channel="Credit Card", tx_type="Purchase", amount=20000),
            make(base + timedelta(minutes=4), channel="Credit Card", tx_type="Purchase", amount=20000),
            make(base + timedelta(minutes=8), channel="Net Banking", tx_type="Fund Transfer", amount=34000)]

    if scenario == "High Velocity + Unusual Transaction Time":
        base = offhour_bin()
        return [make(base + timedelta(seconds=s)) for s in (5, 45, 85)]

    raise ValueError(f"Unsupported live fraud scenario: {scenario}")


def live_make_day(ctx, moderate_pairs, run_id, d):
    rng = random.Random(stable_seed(run_id, f"day-{d.isoformat()}"))
    nrng = np.random.default_rng(stable_seed(run_id, f"numpy-{d.isoformat()}"))
    daily_tx, _, by_day = live_scenario_plan(run_id, d.year, d.month)
    customer_days, normal_ids, normal_weights, _ = live_month_customers(ctx, run_id, d.year, d.month)
    target = daily_tx[d.day - 1]
    midnight = datetime(d.year, d.month, d.day, tzinfo=INDIA_TZ)
    rows = []
    for cid, (scenario, severity) in zip(customer_days[d.day - 1], by_day[d.day - 1]):
        rows.extend(live_fraud_block(ctx, moderate_pairs, rng, nrng, midnight,
                                     scenario, severity, int(cid)))
    if len(rows) > target:
        raise RuntimeError(f"Fraud rows exceed live transaction target on {d}")
    sampled = nrng.choice(normal_ids, size=target - len(rows), p=normal_weights)
    for cid in sampled:
        # Routine transactions stay in the ordinary business hours; intentional
        # off-hours alerts are injected separately and therefore remain measurable.
        ts = normal_timestamp(rng, midnight, d.day)
        if ts.hour < 5 or (ts.hour == 5 and ts.minute < 30):
            ts = midnight + timedelta(hours=10, minutes=30,
                                      seconds=rng.randrange(3600))
        rows.append(normal_record(ctx, rng, nrng, ts, cid=int(cid), historical=True))
    rows.sort(key=lambda x: x["transaction_timestamp"])
    for i, row in enumerate(rows, 1):
        if row["transaction_timestamp"].date() != d:
            raise AssertionError(f"Live timestamp crossed day boundary: {d}")
        row["transaction_id"] = f"LIVE-{run_id[:12].upper()}-{d:%Y%m%d}-{i:06d}"
    assert len(rows) == target
    return rows


def make_day(ctx, run_id, d, historical=False):
    if not historical:
        return live_make_day(ctx, _LIVE_MODERATE_PAIRS, run_id, d)
    rng = random.Random(stable_seed(run_id, f"day-{d.isoformat()}"))
    nrng = np.random.default_rng(stable_seed(run_id, f"numpy-{d.isoformat()}"))
    daily_tx, daily_cases, scenario_sequence = scenario_plan(run_id, d.year, d.month, historical=historical)
    target = daily_tx[d.day - 1]
    cases = daily_cases[d.day - 1]
    midnight = datetime(d.year, d.month, d.day, tzinfo=INDIA_TZ)
    # Each case gets a different customer on that day to limit rule interference.
    fraud_customers = nrng.choice(ctx[0], size=cases, replace=False, p=ctx[2]).tolist()
    rows = []
    first_case = sum(daily_cases[:d.day - 1])
    for cid, scenario in zip(fraud_customers, scenario_sequence[first_case:first_case + cases]):
        rows.extend(fraud_block(ctx, rng, nrng, midnight, scenario, int(cid), historical=historical))
    if len(rows) > target:
        raise RuntimeError(f"Fraud rows exceed daily total for {d}.")
    # Keep routine traffic away from that day's deliberately anomalous customers.
    available = ~np.isin(ctx[0], np.asarray(fraud_customers, dtype=int))
    normal_ids = ctx[0][available]
    normal_weights = ctx[2][available]
    normal_weights = normal_weights / normal_weights.sum()
    normal_count = target - len(rows)
    sampled_customers = nrng.choice(normal_ids, size=normal_count, p=normal_weights)
    for cid in sampled_customers:
        ts = normal_timestamp(rng, midnight, d.day)
        rows.append(normal_record(ctx, rng, nrng, ts, cid=int(cid), historical=historical))
    rows.sort(key=lambda x: x["transaction_timestamp"])
    for i, row in enumerate(rows, 1):
        if row["transaction_timestamp"].date() != d:
            raise AssertionError(f"Date crossed month/day boundary: {d}")
        prefix = "HIST" if historical else "LIVE"
        row["transaction_id"] = f"{prefix}-{run_id[:12].upper()}-{d:%Y%m%d}-{i:06d}"
    assert len(rows) == target
    return rows


def make_event(row):
    body = dict(row)
    body["transaction_timestamp"] = row["transaction_timestamp"].isoformat(timespec="seconds")
    from azure.eventhub import EventData
    return EventData(json.dumps(body, separators=(",", ":"), ensure_ascii=False))


def send_next_batch(producer, day, offset):
    """Return count only after Event Hubs confirms the batch was sent."""
    batch = producer.create_batch()
    n = 0
    while offset + n < len(day) and n < MAX_BATCH_EVENTS:
        event = make_event(day[offset + n])
        try:
            batch.add(event)
        except ValueError:
            if n == 0:
                raise ValueError("A single transaction exceeds Event Hub batch capacity.")
            break
        n += 1
    if not n:
        raise RuntimeError("Empty batch; cannot advance progress.")
    producer.send_batch(batch)
    return n


def confirm_next_live_month(completed_month):
    """Ask before generating or sending ANY records for the following live month."""
    next_month = (completed_month.replace(day=1) + timedelta(days=32)).replace(day=1)
    while True:
        answer = input(
            f"\n{completed_month:%B %Y} finished. "
            f"Send {next_month:%B %Y} transactions? (Y/N): "
        ).strip().lower()
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            print(f"Stopped after {completed_month:%B %Y}.", flush=True)
            return False
        print("Enter Y or N.", flush=True)


def run_stream(producer, customers, locations, run_id, *, historical=False):
    """Stream historical or live events directly, without creating progress files."""
    start_date = HIST_START_DATE if historical else START_DATE
    mode = "HISTORICAL" if historical else "LIVE"
    ctx = context_for(customers, locations, run_id)
    if not historical:
        global _LIVE_MODERATE_PAIRS
        _LIVE_MODERATE_PAIRS = live_moderate_pairs(locations)
    d = start_date
    sent = 0
    print(f"\nFAST {mode} STREAM | Ctrl+C to stop", flush=True)
    current_month = None
    month_sent = 0
    while not historical or d <= HIST_END_DATE:
        month_key = (d.year, d.month)
        if month_key != current_month:
            current_month = month_key
            tx_per_day = (scenario_plan(run_id, d.year, d.month, historical=True)[0]
                          if historical else live_scenario_plan(run_id, d.year, d.month)[0])
            month_sent = 0
            print(f"\n{d:%B %Y} | target {sum(tx_per_day):,} transactions", flush=True)
        day = make_day(ctx, run_id, d, historical=historical)
        offset = 0
        while offset < len(day):
            count = send_next_batch(producer, day, offset)
            offset += count
            sent += count
            month_sent += count
        last_day = calendar.monthrange(d.year, d.month)[1]
        if d.day in (1, 5, 10, 15, 20, 25, last_day):
            print(f"{d:%B %Y} | Day {d.day:02d}/{last_day:02d} COMPLETE | month: {month_sent:,} | total sent: {sent:,}", flush=True)
        if d.day == last_day:
            print(f"{d:%B %Y} COMPLETE | {month_sent:,} transactions sent", flush=True)
            if not historical and not confirm_next_live_month(d):
                return
        d += timedelta(days=1)
    if historical:
        print(f"\nHISTORICAL COMPLETE | {sent:,} transactions sent. No live data sent.")


def validate_live_plan(run_id):
    """Silent, offline preflight: no extra terminal disclosures or files."""
    for (year, month), (target, rate) in LIVE_FIXED_MONTHS.items():
        daily_tx, daily_cases, by_day = live_scenario_plan(run_id, year, month)
        expected_cases = int(target * rate / 100 + 0.5)
        if sum(daily_tx) != target or sum(daily_cases) != expected_cases:
            raise RuntimeError(f"Monthly volume/rate mismatch: {year}-{month:02d}")
        if sum(len(specs) for specs in by_day) != expected_cases:
            raise RuntimeError(f"Monthly scenario mismatch: {year}-{month:02d}")
        if any("Unusual Transaction Time" in scenario for scenario, _ in by_day[0]):
            raise RuntimeError("UTC month rollover in first-day off-hour scenarios")
        counts = [sum(" + " in scenario for scenario, _ in day) for day in by_day]
        if not (0.045 <= sum(counts) / expected_cases <= 0.055):
            raise RuntimeError("Historical multi-scenario mix not preserved")


def main():
    print("=" * 67)
    print("BANKING FRAUD SIMULATOR | MICROSOFT FABRIC")
    print("=" * 67)
    print("1 = Historical Data | 01 Jul - 30 Sep 2026")
    print("2 = Live Data       | From 01 Oct 2026")
    choice = input("Select 1 or 2: ").strip()
    if choice not in ("1", "2"):
        print("Invalid option. No records sent.")
        return
    historical = choice == "1"
    customers, locations, _ = load_inputs()
    run_id = uuid.uuid4().hex
    if not historical:
        validate_live_plan(run_id)
    producer = create_producer()
    try:
        run_stream(producer, customers, locations, run_id, historical=historical)
    except KeyboardInterrupt:
        print("\nStopped. No progress file was created; restarting begins from the first month.")
    finally:
        producer.close()


if __name__ == "__main__":
    main()