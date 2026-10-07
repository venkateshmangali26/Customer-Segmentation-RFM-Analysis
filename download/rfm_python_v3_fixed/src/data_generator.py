"""
Realistic E-Commerce Transaction Data Generator.
Produces 50,000+ realistic transaction records with authentic consumer behavior patterns,
anomalies (cancellations, guest checkouts), and diverse product categories.
"""

import random
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd

from src.config import DEFAULT_N_CUSTOMERS, DEFAULT_N_TRANSACTIONS, RANDOM_SEED, RAW_DATA_FILE

PRODUCT_CATALOG = [
    {"code": "85123A", "desc": "WHITE HANGING HEART T-LIGHT HOLDER", "cat": "Home & Kitchen", "base_price": 2.55},
    {"code": "71053", "desc": "WHITE METAL LANTERN", "cat": "Home & Kitchen", "base_price": 3.39},
    {"code": "84406B", "desc": "CREAM CUPID HEARTS COAT HANGER", "cat": "Home & Kitchen", "base_price": 2.75},
    {"code": "84029G", "desc": "KNITTED UNION FLAG HOT WATER BOTTLE", "cat": "Home & Kitchen", "base_price": 3.45},
    {"code": "84029E", "desc": "RED WOOLLY HOTTIE WHITE HEART", "cat": "Home & Kitchen", "base_price": 3.39},
    {"code": "22752", "desc": "SET 7 BABUSHKA NESTING BOXES", "cat": "Gifts & Novelties", "base_price": 7.65},
    {"code": "21730", "desc": "GLASS STAR FROSTED T-LIGHT HOLDER", "cat": "Home & Kitchen", "base_price": 4.25},
    {"code": "22633", "desc": "HAND WARMER UNION JACK", "cat": "Apparel & Accessories", "base_price": 1.85},
    {"code": "22632", "desc": "HAND WARMER RED RETROSPOT", "cat": "Apparel & Accessories", "base_price": 1.85},
    {"code": "84879", "desc": "ASSORTED COLOUR BIRD ORNAMENT", "cat": "Gifts & Novelties", "base_price": 1.69},
    {"code": "22745", "desc": "POPPY'S PLAYHOUSE BEDROOM", "cat": "Toys & Games", "base_price": 2.10},
    {"code": "22748", "desc": "POPPY'S PLAYHOUSE KITCHEN", "cat": "Toys & Games", "base_price": 2.10},
    {"code": "22749", "desc": "FELTCRAFT PRINCESS CHARLOTTE DOLL", "cat": "Toys & Games", "base_price": 3.75},
    {"code": "22310", "desc": "IVORY KNITTED MUG COSY", "cat": "Home & Kitchen", "base_price": 1.65},
    {"code": "84969", "desc": "BOX OF 6 ASSORTED COLOUR TEASPOONS", "cat": "Home & Kitchen", "base_price": 4.25},
    {"code": "22423", "desc": "REGENCY CAKESTAND 3 TIER", "cat": "Home & Kitchen", "base_price": 12.75},
    {"code": "22720", "desc": "SET OF 3 CAKE TINS PANTRY DESIGN", "cat": "Home & Kitchen", "base_price": 4.95},
    {"code": "21212", "desc": "PACK OF 72 RETROSPOT CAKE CASES", "cat": "Home & Kitchen", "base_price": 0.55},
    {"code": "20725", "desc": "LUNCH BAG RED RETROSPOT", "cat": "Apparel & Accessories", "base_price": 1.65},
    {"code": "20727", "desc": "LUNCH BAG BLACK SKULL", "cat": "Apparel & Accessories", "base_price": 1.65},
    {"code": "20728", "desc": "LUNCH BAG CARS BLUE", "cat": "Apparel & Accessories", "base_price": 1.65},
    {"code": "22383", "desc": "LUNCH BAG SUKI DESIGN", "cat": "Apparel & Accessories", "base_price": 1.65},
    {"code": "20726", "desc": "LUNCH BAG WOODLAND", "cat": "Apparel & Accessories", "base_price": 1.65},
    {"code": "22384", "desc": "LUNCH BAG PINK POLKADOT", "cat": "Apparel & Accessories", "base_price": 1.65},
    {"code": "22382", "desc": "LUNCH BAG SPACEBOY DESIGN", "cat": "Apparel & Accessories", "base_price": 1.65},
    {"code": "22960", "desc": "JAM MAKING SET WITH JARS", "cat": "Home & Kitchen", "base_price": 4.25},
    {"code": "22961", "desc": "JAM MAKING SET PRINTED", "cat": "Home & Kitchen", "base_price": 1.45},
    {"code": "22659", "desc": "SILK PURSE BABUSHKA RED", "cat": "Apparel & Accessories", "base_price": 3.25},
    {"code": "22660", "desc": "SILK PURSE BABUSHKA BLUE", "cat": "Apparel & Accessories", "base_price": 3.25},
    {"code": "22197", "desc": "SMALL POPCORN HOLDER", "cat": "Home & Kitchen", "base_price": 0.85},
    {"code": "22198", "desc": "LARGE POPCORN HOLDER", "cat": "Home & Kitchen", "base_price": 1.65},
    {"code": "47566", "desc": "PARTY BUNTING", "cat": "Gifts & Novelties", "base_price": 4.95},
    {"code": "22386", "desc": "JUMBO BAG PINK POLKADOT", "cat": "Office & Storage", "base_price": 2.08},
    {"code": "85099B", "desc": "JUMBO BAG RED RETROSPOT", "cat": "Office & Storage", "base_price": 2.08},
    {"code": "21931", "desc": "JUMBO STORAGE BAG SUKI", "cat": "Office & Storage", "base_price": 2.08},
    {"code": "22411", "desc": "JUMBO SHOPPER VINTAGE RED PAISLEY", "cat": "Office & Storage", "base_price": 2.08},
    {"code": "23203", "desc": "JUMBO BAG DOILEY PATTERNS", "cat": "Office & Storage", "base_price": 2.08},
    {"code": "84880", "desc": "WHITE WIRE EGG HOLDER", "cat": "Home & Kitchen", "base_price": 7.50},
    {"code": "82484", "desc": "WOOD BLACK BOARD ANT WHITE FINISH", "cat": "Home & Kitchen", "base_price": 6.45},
    {"code": "21108", "desc": "FAIRY CAKE FLANNEL ASSORTED COLOUR", "cat": "Beauty & Personal Care", "base_price": 2.55},
    {"code": "22178", "desc": "VICTORIAN GLASS HANGING T-LIGHT", "cat": "Home & Kitchen", "base_price": 1.25},
    {"code": "21523", "desc": "DOORMAT FANCY FONT", "cat": "Home & Kitchen", "base_price": 7.95},
    {"code": "48138", "desc": "DOORMAT UNION FLAG", "cat": "Home & Kitchen", "base_price": 7.95},
    {"code": "22086", "desc": "PAPER CHAIN KIT 50'S CHRISTMAS", "cat": "Gifts & Novelties", "base_price": 2.95},
    {"code": "22492", "desc": "MINI PAINT SET VINTAGE", "cat": "Toys & Games", "base_price": 0.65},
    {"code": "22556", "desc": "PLASTERS IN TIN CIRCUS PARADE", "cat": "Beauty & Personal Care", "base_price": 1.65},
    {"code": "22554", "desc": "PLASTERS IN TIN WOODLAND ANIMALS", "cat": "Beauty & Personal Care", "base_price": 1.65},
    {"code": "22555", "desc": "PLASTERS IN TIN RETROSPOT", "cat": "Beauty & Personal Care", "base_price": 1.65},
    {"code": "POST", "desc": "POSTAGE EXPRESS", "cat": "Postage & Service", "base_price": 18.00},
    {"code": "MANUAL", "desc": "MANUAL OVERRIDE", "cat": "Postage & Service", "base_price": 25.00},
]

COUNTRIES = [
    ("United Kingdom", 0.85),
    ("Germany", 0.04),
    ("France", 0.035),
    ("Spain", 0.02),
    ("Netherlands", 0.015),
    ("Belgium", 0.01),
    ("Switzerland", 0.01),
    ("Portugal", 0.01),
    ("Australia", 0.005),
    ("USA", 0.005),
]


def generate_customer_profiles(n_customers: int, seed: int = RANDOM_SEED) -> pd.DataFrame:
    """Creates customer behavioral profiles with distinct archetype distributions."""
    np.random.seed(seed)
    random.seed(seed)

    customer_ids = [10000 + i for i in range(n_customers)]
    countries, weights = zip(*COUNTRIES)
    assigned_countries = np.random.choice(countries, size=n_customers, p=weights)

    archetype_probs = [0.10, 0.25, 0.20, 0.20, 0.10, 0.15]
    archetypes = np.random.choice(
        ["VIP", "Loyal", "Potential", "Occasional", "AtRisk", "Hibernating"],
        size=n_customers,
        p=archetype_probs,
    )

    profiles = pd.DataFrame({
        "CustomerID": customer_ids,
        "Country": assigned_countries,
        "Archetype": archetypes,
    })
    return profiles


def generate_synthetic_transactions(
    n_transactions: int = DEFAULT_N_TRANSACTIONS,
    n_customers: int = DEFAULT_N_CUSTOMERS,
    start_date: str = "2024-01-01",
    end_date: str = "2025-06-30",
    seed: int = RANDOM_SEED,
    output_path: Optional[Path] = RAW_DATA_FILE,
) -> pd.DataFrame:
    """Generates a realistic e-commerce transaction dataset with 50,000+ records."""
    np.random.seed(seed)
    random.seed(seed)

    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    total_days = (end_dt - start_dt).days

    customer_df = generate_customer_profiles(n_customers, seed=seed)
    customers_dict = customer_df.set_index("CustomerID").to_dict("index")
    customer_ids = customer_df["CustomerID"].tolist()

    cust_tx_weights = {
        "VIP": (18, 35),
        "Loyal": (8, 16),
        "Potential": (4, 9),
        "Occasional": (2, 5),
        "AtRisk": (5, 12),
        "Hibernating": (1, 3),
    }

    recency_windows = {
        "VIP": (1, 35),
        "Loyal": (10, 80),
        "Potential": (5, 60),
        "Occasional": (40, 220),
        "AtRisk": (160, 420),
        "Hibernating": (200, total_days),
    }

    records = []
    invoice_seq = 536365
    items_per_invoice_dist = [1, 2, 3, 4, 5, 6, 8, 10, 12]
    items_per_invoice_weights = [0.18, 0.24, 0.20, 0.14, 0.10, 0.06, 0.04, 0.02, 0.02]

    for cid in customer_ids:
        arch = customers_dict[cid]["Archetype"]
        country = customers_dict[cid]["Country"]
        min_orders, max_orders = cust_tx_weights[arch]
        n_orders = np.random.randint(min_orders, max_orders + 1)
        min_rec, max_rec = recency_windows[arch]

        last_order_days_ago = np.random.randint(min_rec, max(min_rec + 1, min(max_rec, total_days)))
        last_order_dt = end_dt - timedelta(days=int(last_order_days_ago))

        order_dates = [last_order_dt]
        for _ in range(n_orders - 1):
            prior_offset = np.random.randint(10, 180)
            prior_dt = last_order_dt - timedelta(days=int(prior_offset))
            if prior_dt >= start_dt:
                order_dates.append(prior_dt)

        order_dates = sorted(order_dates)

        for o_date in order_dates:
            hour = np.random.randint(8, 20)
            minute = np.random.randint(0, 60)
            second = np.random.randint(0, 60)
            invoice_dt = o_date.replace(hour=hour, minute=minute, second=second)

            invoice_no = str(invoice_seq)
            invoice_seq += 1
            is_cancellation = (np.random.random() < 0.025)

            n_items = np.random.choice(items_per_invoice_dist, p=items_per_invoice_weights)
            if arch == "VIP":
                n_items = min(20, n_items + np.random.randint(2, 6))

            selected_products = random.sample(PRODUCT_CATALOG, min(n_items, len(PRODUCT_CATALOG)))

            for prod in selected_products:
                if arch == "VIP":
                    qty = int(np.random.choice([6, 12, 24, 48, 72, 100], p=[0.3, 0.3, 0.2, 0.1, 0.07, 0.03]))
                else:
                    qty = int(np.random.choice([1, 2, 3, 4, 6, 12, 24], p=[0.40, 0.25, 0.15, 0.10, 0.06, 0.03, 0.01]))

                unit_price = round(prod["base_price"] * np.random.uniform(0.95, 1.05), 2)

                records.append({
                    "InvoiceNo": invoice_no,
                    "StockCode": prod["code"],
                    "Description": prod["desc"],
                    "Quantity": qty,
                    "InvoiceDate": invoice_dt.strftime("%Y-%m-%d %H:%M:%S"),
                    "UnitPrice": unit_price,
                    "CustomerID": cid,
                    "Country": country,
                    "Category": prod["cat"],
                })

            if is_cancellation:
                cancel_invoice_no = f"C{invoice_no}"
                cancel_dt = invoice_dt + timedelta(days=np.random.randint(1, 5))
                for prod in selected_products[:max(1, len(selected_products) // 2)]:
                    records.append({
                        "InvoiceNo": cancel_invoice_no,
                        "StockCode": prod["code"],
                        "Description": prod["desc"],
                        "Quantity": -int(np.random.choice([1, 2, 4])),
                        "InvoiceDate": cancel_dt.strftime("%Y-%m-%d %H:%M:%S"),
                        "UnitPrice": prod["base_price"],
                        "CustomerID": cid,
                        "Country": country,
                        "Category": prod["cat"],
                    })

    df = pd.DataFrame(records)

    # Introduce guest checkouts (~8% missing CustomerIDs)
    missing_mask = np.random.random(len(df)) < 0.08
    df.loc[missing_mask, "CustomerID"] = np.nan

    promo_indices = np.random.choice(df.index, size=int(len(df) * 0.002), replace=False)
    df.loc[promo_indices, "UnitPrice"] = 0.0

    if len(df) < n_transactions:
        extra_needed = n_transactions - len(df)
        sampled_rows = df.sample(extra_needed, replace=True).copy()
        for i in range(len(sampled_rows)):
            sampled_rows.iloc[i, sampled_rows.columns.get_loc("InvoiceNo")] = str(invoice_seq + i)
        df = pd.concat([df, sampled_rows], ignore_index=True)

    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"])
    df = df.sort_values("InvoiceDate").reset_index(drop=True)

    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"Generated {len(df):,} transactions across {df['CustomerID'].nunique():,} unique customers.")
        print(f"Saved raw transaction dataset to: {output_path}")

    return df


if __name__ == "__main__":
    generate_synthetic_transactions()
