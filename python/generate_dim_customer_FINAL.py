"""
FINAL DimCustomer generator
Real-Time Banking Fraud Analytics project

Creates ONE file only:
    DimCustomer_YYYYMMDD.csv

Final schema:
    customer_id
    customer_name
    age
    gender
    home_location_id
    account_tenure_months

Input:
    Select the finalized DimLocation CSV.

Output:
    Automatically saved in the same folder as DimLocation.
"""

from pathlib import Path
from datetime import datetime
import random
import math
import pandas as pd
from tkinter import Tk, filedialog, messagebox

SEED = 20261003
N_CUSTOMERS = 10_000
FIRST_CUSTOMER_ID = 10001

FIRST_NAMES_MALE = [
    "Aarav","Aditya","Akash","Akshay","Aman","Amit","Aniket","Arjun","Arnav","Aryan",
    "Ayush","Deepak","Dev","Gaurav","Harsh","Ishaan","Jatin","Karan","Kunal","Manish",
    "Mohit","Nikhil","Pranav","Rahul","Raj","Rishabh","Rohan","Sameer","Shivam","Siddharth",
    "Varun","Vedant","Vikas","Yash"
]

FIRST_NAMES_FEMALE = [
    "Aditi","Ananya","Anjali","Anushka","Bhavna","Divya","Isha","Kavya","Khushi","Meera",
    "Naina","Neha","Nisha","Pallavi","Pooja","Priya","Rhea","Ritika","Sakshi","Sanjana",
    "Shreya","Simran","Sneha","Sonia","Tanvi"
]

LAST_NAMES = [
    "Agarwal","Bansal","Bhat","Chauhan","Choudhary","Das","Desai","Deshmukh","Dubey","Ghosh",
    "Gupta","Iyer","Jain","Joshi","Kapoor","Khan","Kulkarni","Kumar","Malhotra","Mehta",
    "Menon","Mishra","Mukherjee","Nair","Naik","Pandey","Patel","Patil","Pillai","Prasad",
    "Rao","Reddy","Roy","Saxena","Sen","Shah","Sharma","Shetty","Shinde","Singh",
    "Sinha","Srivastava","Thakur","Tiwari","Trivedi","Verma","Yadav"
]

# Synthetic city sampling weights for portfolio data.
# They are NOT official population or bank-customer statistics.
CITY_WEIGHTS = {
    "Mumbai":12, "New Delhi":12, "Delhi":12, "Bengaluru":12,
    "Hyderabad":10, "Chennai":10, "Kolkata":10, "Pune":9,
    "Ahmedabad":8, "Surat":7, "Jaipur":7, "Lucknow":7,
    "Kanpur":6, "Nagpur":6, "Indore":6, "Patna":6,
    "Gurugram":6, "Noida":6, "Bhopal":5, "Kochi":5,
    "Coimbatore":5, "Visakhapatnam":5, "Bhubaneswar":5,
    "Ludhiana":5, "Nashik":5, "Vadodara":5, "Rajkot":4,
    "Varanasi":4, "Prayagraj":4, "Ranchi":4, "Guwahati":4,
    "Chandigarh":4, "Dehradun":4, "Thiruvananthapuram":4,
    "Mysuru":4, "Madurai":4, "Vijayawada":4, "Raipur":4,
    "Jodhpur":4, "Srinagar":3, "Jammu":3
}
DEFAULT_CITY_WEIGHT = 2.0


def choose_location_file():
    root = Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    path = filedialog.askopenfilename(
        title="Select finalized DimLocation CSV",
        filetypes=[("CSV files", "*.csv")]
    )
    root.destroy()
    return Path(path) if path else None


def exact_weighted_counts(weights, total):
    total_weight = sum(weights)
    raw = [w / total_weight * total for w in weights]
    counts = [math.floor(x) for x in raw]
    remaining = total - sum(counts)
    order = sorted(
        range(len(raw)),
        key=lambda i: raw[i] - counts[i],
        reverse=True
    )
    for i in order[:remaining]:
        counts[i] += 1
    return counts


def generate_age(rng):
    # Adult banking customers with a realistic middle-heavy synthetic distribution.
    bands = [(18,24,0.14), (25,34,0.29), (35,44,0.24),
             (45,54,0.17), (55,64,0.10), (65,75,0.06)]
    pick = rng.random()
    cumulative = 0
    for low, high, weight in bands:
        cumulative += weight
        if pick <= cumulative:
            return rng.randint(low, high)
    return rng.randint(65, 75)


def generate_tenure_months(rng, age):
    # Tenure cannot exceed the approximate number of months since age 18.
    max_possible = max(1, min(240, (age - 18) * 12))
    if max_possible <= 12:
        return rng.randint(1, max_possible)

    # Most customers are established, while retaining newer accounts.
    x = rng.random()
    if x < 0.20:
        return rng.randint(1, min(12, max_possible))
    elif x < 0.50:
        return rng.randint(13, min(36, max_possible)) if max_possible >= 13 else rng.randint(1, max_possible)
    elif x < 0.80:
        return rng.randint(37, min(84, max_possible)) if max_possible >= 37 else rng.randint(1, max_possible)
    else:
        return rng.randint(85, max_possible) if max_possible >= 85 else rng.randint(1, max_possible)


def main():
    rng = random.Random(SEED)

    input_path = choose_location_file()
    if input_path is None:
        print("No DimLocation file selected. Cancelled.")
        return

    locations = pd.read_csv(input_path)

    required = {"location_id","city","state_ut","region","latitude","longitude"}
    missing = required - set(locations.columns)
    if missing:
        raise ValueError(f"DimLocation missing columns: {sorted(missing)}")
    if locations["location_id"].duplicated().any():
        raise ValueError("Duplicate location_id found in DimLocation.")

    weights = [
        CITY_WEIGHTS.get(str(city), DEFAULT_CITY_WEIGHT)
        for city in locations["city"]
    ]
    counts = exact_weighted_counts(weights, N_CUSTOMERS)

    home_ids = []
    for location_id, count in zip(locations["location_id"], counts):
        home_ids.extend([int(location_id)] * count)
    rng.shuffle(home_ids)

    rows = []
    used_names = {}

    for idx, customer_id in enumerate(
        range(FIRST_CUSTOMER_ID, FIRST_CUSTOMER_ID + N_CUSTOMERS)
    ):
        gender = rng.choice(["Male", "Female"])
        first = rng.choice(
            FIRST_NAMES_MALE if gender == "Male" else FIRST_NAMES_FEMALE
        )
        last = rng.choice(LAST_NAMES)
        base_name = f"{first} {last}"

        # Duplicate names are legitimate in a 10k population, so customer_id remains
        # the unique key. No artificial number is added to a person's name.
        used_names[base_name] = used_names.get(base_name, 0) + 1

        age = generate_age(rng)
        tenure = generate_tenure_months(rng, age)

        rows.append({
            "customer_id": customer_id,
            "customer_name": base_name,
            "age": age,
            "gender": gender,
            "home_location_id": home_ids[idx],
            "account_tenure_months": tenure
        })

    df = pd.DataFrame(rows, columns=[
        "customer_id",
        "customer_name",
        "age",
        "gender",
        "home_location_id",
        "account_tenure_months"
    ])

    # FINAL validation
    valid_locations = set(locations["location_id"].astype(int))
    assert len(df) == 10_000
    assert df["customer_id"].is_unique
    assert df["customer_id"].min() == 10001
    assert df["customer_id"].max() == 20000
    assert df.isna().sum().sum() == 0
    assert df["age"].between(18, 75).all()
    assert set(df["gender"].unique()).issubset({"Male", "Female"})
    assert df["home_location_id"].isin(valid_locations).all()
    assert df["account_tenure_months"].ge(1).all()
    assert df["home_location_id"].nunique() == len(locations)

    date_stamp = datetime.now().strftime("%Y%m%d")
    output_path = input_path.parent / f"DimCustomer_{date_stamp}.csv"
    df.to_csv(output_path, index=False, encoding="utf-8-sig")

    print("\nDimCustomer generated successfully.")
    print(f"Rows             : {len(df):,}")
    print(f"Customer IDs     : {df.customer_id.min()} - {df.customer_id.max()}")
    print(f"Locations used   : {df.home_location_id.nunique()}")
    print(f"Null values      : {df.isna().sum().sum()}")
    print(f"Duplicate IDs    : {df.customer_id.duplicated().sum()}")
    print(f"Output           : {output_path}")

    root = Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    messagebox.showinfo(
        "DimCustomer Complete",
        f"10,000 customers generated successfully.\n\n{output_path.name}"
    )
    root.destroy()


if __name__ == "__main__":
    main()