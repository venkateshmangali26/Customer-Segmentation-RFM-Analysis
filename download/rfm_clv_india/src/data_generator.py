"""
Indian E-Commerce Transaction Data Generator
=============================================
Generates 50,000+ realistic Indian e-commerce transactions with:
- Authentic Indian product catalog (Electronics, Fashion, Mobile Accessories,
  Grocery, Home Decor, Beauty, Ayurveda, Books, Toys)
- INR pricing typical of Indian D2C / marketplace sellers
- Customer distribution across major Indian states & metros
- Indian first/last names
- Festival-season spikes: Diwali (Oct-Nov), Holi (Mar), Raksha Bandhan (Aug),
  Independence Day (Aug 15), Republic Day (Jan 26)
- Cancellations (~2.5%) and guest checkouts (~8%)
- Behavioral archetypes: VIP, Loyal, Potential, Occasional, AtRisk, Hibernating
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

# ============================================================================
# Indian product catalog — realistic SKUs across 8 categories
# Prices in INR (₹), typical of Indian D2C / Flipkart / Amazon.in sellers
# ============================================================================

PRODUCT_CATALOG = [
    # --- Mobile & Electronics (₹99–₹2499) ---
    {"code": "MBL01", "desc": "USB-C Fast Charging Cable 3M", "cat": "Mobile Accessories", "base_price": 249.00},
    {"code": "MBL02", "desc": "Bluetooth Earbuds with Mic", "cat": "Mobile Accessories", "base_price": 1299.00},
    {"code": "MBL03", "desc": "20W USB-C Wall Charger", "cat": "Mobile Accessories", "base_price": 449.00},
    {"code": "MBL04", "desc": "Phone Tempered Glass Pack of 2", "cat": "Mobile Accessories", "base_price": 199.00},
    {"code": "MBL05", "desc": "Power Bank 20000mAh", "cat": "Mobile Accessories", "base_price": 1499.00},
    {"code": "MBL06", "desc": "Phone Cover Designer Print", "cat": "Mobile Accessories", "base_price": 299.00},
    {"code": "MBL07", "desc": "USB OTG Adapter Type-C", "cat": "Mobile Accessories", "base_price": 199.00},

    # --- Fashion & Apparel (₹199–₹1999) ---
    {"code": "FSH01", "desc": "Cotton Round Neck T-Shirt", "cat": "Fashion", "base_price": 399.00},
    {"code": "FSH02", "desc": "Women Anarkali Kurti Set", "cat": "Fashion", "base_price": 999.00},
    {"code": "FSH03", "desc": "Men Slim Fit Jeans", "cat": "Fashion", "base_price": 1199.00},
    {"code": "FSH04", "desc": "Cotton Saree with Blouse", "cat": "Fashion", "base_price": 899.00},
    {"code": "FSH05", "desc": "Sports Running Shoes", "cat": "Fashion", "base_price": 1499.00},
    {"code": "FSH06", "desc": "Cotton Bedsheet Double Bed", "cat": "Home Decor", "base_price": 699.00},
    {"code": "FSH07", "desc": "Men Wallet Leather", "cat": "Fashion", "base_price": 449.00},
    {"code": "FSH08", "desc": "Women Handbag Faux Leather", "cat": "Fashion", "base_price": 999.00},
    {"code": "FSH09", "desc": "Analog Wrist Watch", "cat": "Fashion", "base_price": 799.00},
    {"code": "FSH10", "desc": "Sunglasses UV Protection", "cat": "Fashion", "base_price": 349.00},

    # --- Home & Kitchen (₹99–₹1499) ---
    {"code": "HMN01", "desc": "Stainless Steel Thali Set 6pc", "cat": "Home & Kitchen", "base_price": 599.00},
    {"code": "HMN02", "desc": "Non-Stick Tawa 28cm", "cat": "Home & Kitchen", "base_price": 449.00},
    {"code": "HMN03", "desc": "Brass Diya Pack of 12", "cat": "Home Decor", "base_price": 349.00},
    {"code": "HMN04", "desc": "Mandir Wall Hanging Decor", "cat": "Home Decor", "base_price": 799.00},
    {"code": "HMN05", "desc": "Plastic Storage Container Set 9pc", "cat": "Home & Kitchen", "base_price": 499.00},
    {"code": "HMN06", "desc": "Cotton Floor Cushion Cover", "cat": "Home Decor", "base_price": 399.00},
    {"code": "HMN07", "desc": "Glass Tea Cup Set of 6", "cat": "Home & Kitchen", "base_price": 299.00},
    {"code": "HMN08", "desc": "Incense Stick Holder Brass", "cat": "Home Decor", "base_price": 249.00},
    {"code": "HMN09", "desc": "Wooden Wall Clock", "cat": "Home Decor", "base_price": 699.00},
    {"code": "HMN10", "desc": "Stainless Steel Water Bottle 1L", "cat": "Home & Kitchen", "base_price": 199.00},

    # --- Grocery & Staples (₹49–₹599) ---
    {"code": "GRC01", "desc": "Basmati Rice 5kg Premium", "cat": "Grocery", "base_price": 449.00},
    {"code": "GRC02", "desc": "Sunflower Oil 1L", "cat": "Grocery", "base_price": 199.00},
    {"code": "GRC03", "desc": "Mixed Pickles Bottle 400g", "cat": "Grocery", "base_price": 149.00},
    {"code": "GRC04", "desc": "Masala Tea Gift Box", "cat": "Grocery", "base_price": 399.00},
    {"code": "GRC05", "desc": "Pure Ghee 500ml", "cat": "Grocery", "base_price": 349.00},
    {"code": "GRC06", "desc": "Premium Saffron 1g Pack", "cat": "Grocery", "base_price": 299.00},
    {"code": "GRC07", "desc": "Atta Whole Wheat 10kg", "cat": "Grocery", "base_price": 449.00},
    {"code": "GRC08", "desc": "Cashew Premium 200g", "cat": "Grocery", "base_price": 299.00},

    # --- Beauty & Personal Care (₹99–₹699) ---
    {"code": "BTY01", "desc": "Ayurvedic Face Wash 100ml", "cat": "Beauty", "base_price": 199.00},
    {"code": "BTY02", "desc": "Coconut Hair Oil 200ml", "cat": "Beauty", "base_price": 149.00},
    {"code": "BTY03", "desc": "Herbal Shampoo 340ml", "cat": "Beauty", "base_price": 249.00},
    {"code": "BTY04", "desc": "Henna Powder Natural 100g", "cat": "Beauty", "base_price": 99.00},
    {"code": "BTY05", "desc": "Ayurvedic Skin Cream 50g", "cat": "Ayurveda", "base_price": 299.00},
    {"code": "BTY06", "desc": "Rose Water Toner 200ml", "cat": "Beauty", "base_price": 149.00},
    {"code": "BTY07", "desc": "Neem Soap Pack of 3", "cat": "Beauty", "base_price": 129.00},

    # --- Books & Toys (₹99–₹699) ---
    {"code": "BOK01", "desc": "Bhagavad Gita Pocket Edition", "cat": "Books", "base_price": 199.00},
    {"code": "BOK02", "desc": "Yoga Manual Illustrated", "cat": "Books", "base_price": 299.00},
    {"code": "BOK03", "desc": "Indian Cookery Recipes", "cat": "Books", "base_price": 349.00},
    {"code": "BOK04", "desc": "Children Panchatantra Tales", "cat": "Books", "base_price": 199.00},

    {"code": "TOY01", "desc": "Wooden Rattle Toy Handmade", "cat": "Toys", "base_price": 199.00},
    {"code": "TOY02", "desc": "Brass Puzzle Set 6pc", "cat": "Toys", "base_price": 349.00},
    {"code": "TOY03", "desc": "Chess Set Wooden Magnetic", "cat": "Toys", "base_price": 599.00},
    {"code": "TOY04", "desc": "Clay Diya Painting Kit", "cat": "Toys", "base_price": 249.00},

    # --- Ayurveda (₹199–₹999) ---
    {"code": "AYR01", "desc": "Ashwagandha Capsules 60ct", "cat": "Ayurveda", "base_price": 349.00},
    {"code": "AYR02", "desc": "Triphala Powder 200g", "cat": "Ayurveda", "base_price": 199.00},
    {"code": "AYR03", "desc": "Chyawanprash 1kg", "cat": "Ayurveda", "base_price": 549.00},
    {"code": "AYR04", "desc": "Tulsi Drops 30ml", "cat": "Ayurveda", "base_price": 199.00},

    # --- Festival Specials (Diwali/Rakhi/Sankranti) ---
    {"code": "FST01", "desc": "Diwali Gift Hamper Premium", "cat": "Festival Specials", "base_price": 999.00},
    {"code": "FST02", "desc": "Rakhi Set with Sweets 12pc", "cat": "Festival Specials", "base_price": 599.00},
    {"code": "FST03", "desc": "Rangoli Color Powder Pack", "cat": "Festival Specials", "base_price": 199.00},
    {"code": "FST04", "desc": "Diwali Diya Decoration Set", "cat": "Festival Specials", "base_price": 349.00},
    {"code": "FST05", "desc": "Kite Flying Set Sankranti", "cat": "Festival Specials", "base_price": 249.00},
    {"code": "FST06", "desc": "Holi Color Powder Pack 6", "cat": "Festival Specials", "base_price": 299.00},
    {"code": "FST07", "desc": "Pooja Thali Complete Set", "cat": "Festival Specials", "base_price": 899.00},
    {"code": "FST08", "desc": "Festive Sweets Assorted Box", "cat": "Festival Specials", "base_price": 699.00},
]

# ============================================================================
# Indian customer geography — major Indian states with population weights
# (Approximate population share of Indian e-commerce buyers)
# ============================================================================

INDIAN_STATES = [
    ("Maharashtra", 0.155),         # Mumbai, Pune
    ("Delhi", 0.085),
    ("Karnataka", 0.090),           # Bangalore
    ("Tamil Nadu", 0.085),          # Chennai
    ("Telangana", 0.060),           # Hyderabad
    ("Gujarat", 0.070),             # Ahmedabad, Surat
    ("Uttar Pradesh", 0.090),      # Lucknow, Noida
    ("West Bengal", 0.060),         # Kolkata
    ("Rajasthan", 0.045),           # Jaipur
    ("Madhya Pradesh", 0.040),
    ("Haryana", 0.040),             # Gurgaon
    ("Kerala", 0.045),
    ("Punjab", 0.035),
    ("Andhra Pradesh", 0.040),
    ("Bihar", 0.030),
    ("Odisha", 0.025),
    ("Jharkhand", 0.020),
    ("Uttarakhand", 0.020),
    ("Chhattisgarh", 0.015),
    ("Assam", 0.015),
    ("Himachal Pradesh", 0.010),
    ("Goa", 0.005),
    ("Tripura", 0.005),
    ("Manipur", 0.005),
]

# ============================================================================
# Indian customer names — common first names across regions
# ============================================================================

FIRST_NAMES_MALE = [
    "Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Reyansh", "Ayaan",
    "Krishna", "Ishaan", "Rohan", "Aryan", "Rahul", "Karan", "Sameer", "Vikram",
    "Sanjay", "Anil", "Amit", "Rajesh", "Suresh", "Mahesh", "Deepak", "Rakesh",
    "Pradeep", "Vijay", "Ashok", "Manoj", "Vinod", "Dinesh", "Mohan", "Gopal",
    "Harish", "Narayan", "Srinivas", "Venkatesh", "Ganesh", "Murthy", "Anand",
    "Suresh", "Karthik", "Vignesh", "Prashant", "Ramesh", "Anil", "Arun",
    "Sunil", "Dinesh", "Sandeep", "Jitendra",
]

FIRST_NAMES_FEMALE = [
    "Saanvi", "Aanya", "Aadhya", "Anaya", "Diya", "Kiara", "Pari", "Myra",
    "Anika", "Navya", "Aarohi", "Riya", "Sara", "Ira", "Ishita", "Aditi",
    "Pooja", "Priya", "Neha", "Kavya", "Shreya", "Divya", "Anjali", "Meera",
    "Sneha", "Lakshmi", "Saraswati", "Parvati", "Radha", "Sita", "Geeta",
    "Anita", "Sunita", "Kavita", "Rekha", "Madhuri", "Sridevi", "Jaya",
    "Hema", "Sushma", "Swati", "Pallavi", "Bhavana", "Anu", "Veena",
    "Manju", "Vidya", "Shobha", "Lata", "Asha", "Usha",
]

LAST_NAMES_NORTH = [
    "Sharma", "Verma", "Gupta", "Singh", "Kumar", "Agarwal", "Jain", "Mittal",
    "Goel", "Saxena", "Bhatia", "Kapoor", "Khanna", "Malhotra", "Chopra",
    "Mehta", "Shah", "Bansal", "Tiwari", "Pandey", "Mishra", "Shukla",
    "Agarwal", "Goyal", "Agrawal", "Bhardwaj", "Dwivedi", "Tripathi",
]

LAST_NAMES_SOUTH = [
    "Iyer", "Iyengar", "Nair", "Menon", "Pillai", "Nair", "Reddy", "Rao",
    "Naidu", "Shetty", "Hegde", "Gowda", "Murthy", "Rao", "Krishnan",
    "Subramanian", "Venkatesan", "Chandran", "Raman", "Anand", "Varma",
    "Pillai", "Nambiar", "Panicker", "Kurup", "Potty", "Thampi", "Das",
]

LAST_NAMES_WEST = [
    "Patel", "Shah", "Desai", "Mehta", "Joshi", "Kothari", "Doshi", "Gandhi",
    "Modi", "Gandhi", "Vora", "Dalal", "Sanghvi", "Gada", "Bhandari", "Patil",
    "Desai", "Deshmukh", "Jadhav", "Powar", "Kulkarni", "Pawar",
]

LAST_NAMES_EAST = [
    "Das", "Banerjee", "Bhattacharya", "Mukherjee", "Chatterjee", "Ghosh",
    "Sengupta", "Roy", "Saha", "Bose", "Mitra", "Dutta", "Pal", "Dey",
    "Sarkar", "Dasgupta", "Lahiri", "Bandyopadhyay", "Chowdhury",
]


def _pick_indian_name(rng: random.Random) -> tuple[str, str]:
    """Pick a random Indian full name, regionally biased by first-letter
    distribution."""
    # 50/50 male/female split
    if rng.random() < 0.5:
        first = rng.choice(FIRST_NAMES_MALE)
    else:
        first = rng.choice(FIRST_NAMES_FEMALE)

    # Pick a regional last name at random
    region = rng.choices(
        ["North", "South", "West", "East"],
        weights=[0.40, 0.25, 0.25, 0.10],
        k=1,
    )[0]
    last_pool = {
        "North": LAST_NAMES_NORTH,
        "South": LAST_NAMES_SOUTH,
        "West": LAST_NAMES_WEST,
        "East": LAST_NAMES_EAST,
    }[region]
    last = rng.choice(last_pool)
    return first, last


# ============================================================================
# Festival seasonality — boost sales during Indian festival windows
# ============================================================================

# Major Indian festivals with approximate month + magnitude of sales boost
INDIAN_FESTIVALS = [
    # (month, boost_factor, name) — month is 1-12
    (1, 1.25, "Republic Day Sale"),       # Jan 26
    (3, 1.20, "Holi Festival Sale"),       # March
    (8, 1.30, "Independence Day + Raksha Bandhan"),  # Aug 15 + mid-Aug
    (10, 1.45, "Navratri & Dussehra Sale"),  # Oct
    (11, 1.80, "Diwali Mega Sale"),         # Nov — biggest e-commerce week of the year
    (12, 1.30, "Christmas & Year-End Sale"), # Dec
]


def _festival_boost(date: datetime) -> float:
    """Return a multiplicative boost factor for the given date based on
    Indian festival calendar. November gets the biggest boost (Diwali)."""
    month = date.month
    for fm, factor, _name in INDIAN_FESTIVALS:
        if fm == month:
            return factor
    return 1.0


# ============================================================================
# Customer profile + transaction generation
# ============================================================================

def generate_customer_profiles(n_customers: int, seed: int = RANDOM_SEED) -> pd.DataFrame:
    """Creates customer behavioral profiles with distinct archetype distributions
    across Indian states."""
    np.random.seed(seed)
    random.seed(seed)

    customer_ids = [10000 + i for i in range(n_customers)]
    states, weights = zip(*INDIAN_STATES)
    assigned_states = np.random.choice(states, size=n_customers, p=weights)

    # Use a Python-level RNG for name picking (numpy doesn't handle string picks well)
    name_rng = random.Random(seed)
    names = [_pick_indian_name(name_rng) for _ in range(n_customers)]
    first_names = [n[0] for n in names]
    last_names = [n[1] for n in names]

    # Behavioral archetype distribution (Indian e-commerce:
    # more Hibernating/Occasional, fewer VIP, compared to mature UK markets)
    archetype_probs = [0.07, 0.18, 0.22, 0.28, 0.15, 0.10]
    archetypes = np.random.choice(
        ["VIP", "Loyal", "Potential", "Occasional", "AtRisk", "Hibernating"],
        size=n_customers,
        p=archetype_probs,
    )

    return pd.DataFrame({
        "CustomerID": customer_ids,
        "CustomerName": [f"{f} {l}" for f, l in zip(first_names, last_names)],
        "State": assigned_states,
        "Archetype": archetypes,
    })


def generate_synthetic_transactions(
    n_transactions: int = DEFAULT_N_TRANSACTIONS,
    n_customers: int = DEFAULT_N_CUSTOMERS,
    start_date: str = "2024-01-01",
    end_date: str = "2025-06-30",
    seed: int = RANDOM_SEED,
    output_path: Optional[Path] = RAW_DATA_FILE,
) -> pd.DataFrame:
    """Generates a realistic Indian e-commerce transaction dataset with 50,000+ records.

    Includes:
    - Festival-season sales boosts (Diwali in Nov is +80%, etc.)
    - Behavioral archetypes (VIP customers buy 18-35 orders/yr, Hibernating 1-3)
    - Cancellations (~2.5% — Indian e-commerce has higher return rates than West)
    - Guest checkouts (~8% — many Indian shoppers still checkout as guest)
    - Cash-on-Delivery (COD) flag (~25% of orders in India use COD)
    """
    np.random.seed(seed)
    random.seed(seed)

    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    total_days = (end_dt - start_dt).days

    customer_df = generate_customer_profiles(n_customers, seed=seed)
    customers_dict = customer_df.set_index("CustomerID").to_dict("index")
    customer_ids = customer_df["CustomerID"].tolist()

    # Indian e-commerce order patterns per archetype
    # (Generally lower than mature markets, but VIPs buy frequently)
    cust_tx_weights = {
        "VIP": (15, 30),
        "Loyal": (6, 14),
        "Potential": (3, 8),
        "Occasional": (2, 4),
        "AtRisk": (4, 10),
        "Hibernating": (1, 2),
    }

    # Recency windows in days
    recency_windows = {
        "VIP": (1, 30),
        "Loyal": (10, 70),
        "Potential": (5, 55),
        "Occasional": (40, 200),
        "AtRisk": (150, 380),
        "Hibernating": (200, total_days),
    }

    records = []
    invoice_seq = 536365
    items_dist = [1, 2, 3, 4, 5, 6, 8, 10, 12]
    items_weights = [0.20, 0.25, 0.20, 0.13, 0.09, 0.05, 0.04, 0.02, 0.02]

    # Indian payment methods (with approx prevalence)
    PAYMENT_METHODS = [
        ("UPI", 0.45),         # PhonePe, GPay, Paytm — dominant in India
        ("Credit/Debit Card", 0.20),
        ("COD", 0.25),          # Cash on Delivery — still prevalent in Tier-2/3
        ("Net Banking", 0.05),
        ("Wallet", 0.05),
    ]
    payment_methods, payment_weights = zip(*PAYMENT_METHODS)

    for cid in customer_ids:
        arch = customers_dict[cid]["Archetype"]
        state = customers_dict[cid]["State"]
        customer_name = customers_dict[cid]["CustomerName"]

        min_orders, max_orders = cust_tx_weights[arch]
        n_orders = np.random.randint(min_orders, max_orders + 1)
        min_rec, max_rec = recency_windows[arch]

        last_order_days_ago = np.random.randint(min_rec, max(min_rec + 1, min(max_rec, total_days)))
        last_order_dt = end_dt - timedelta(days=int(last_order_days_ago))

        order_dates = [last_order_dt]
        for _ in range(n_orders - 1):
            prior_offset = np.random.randint(10, 150)
            prior_dt = last_order_dt - timedelta(days=int(prior_offset))
            if prior_dt >= start_dt:
                order_dates.append(prior_dt)

        order_dates = sorted(order_dates)

        for o_date in order_dates:
            hour = np.random.randint(8, 23)  # Indian shopping peaks 8 AM–11 PM
            minute = np.random.randint(0, 60)
            second = np.random.randint(0, 60)
            invoice_dt = o_date.replace(hour=hour, minute=minute, second=second)

            invoice_no = str(invoice_seq)
            invoice_seq += 1
            is_cancellation = (np.random.random() < 0.025)
            is_cod = (np.random.random() < 0.25)

            # Festival boost: orders during festival months have more items
            boost = _festival_boost(invoice_dt)
            n_items = int(np.random.choice(items_dist, p=items_weights) * (1 + (boost - 1) * 0.5))
            if arch == "VIP":
                n_items = min(20, n_items + np.random.randint(2, 6))

            # Festival-month customers more likely to buy festival specials
            festival_catalog_bias = []
            if boost > 1.2 and np.random.random() < 0.4:
                # 40% of festival-month orders include at least one festival item
                festival_catalog_bias = [p for p in PRODUCT_CATALOG if p["cat"] == "Festival Specials"]

            available_pool = PRODUCT_CATALOG + festival_catalog_bias
            selected_products = random.sample(available_pool, min(n_items, len(available_pool)))

            for prod in selected_products:
                # Indian e-commerce: smaller quantities (1-6 typically, 12 for bulk)
                if arch == "VIP":
                    qty = int(np.random.choice([2, 4, 6, 12, 24], p=[0.35, 0.30, 0.20, 0.10, 0.05]))
                else:
                    qty = int(np.random.choice([1, 2, 3, 4, 6, 12], p=[0.45, 0.25, 0.15, 0.08, 0.05, 0.02]))

                # Small ±5% price variation (Indian pricing is more rigid than Western)
                unit_price = round(prod["base_price"] * np.random.uniform(0.95, 1.05), 2)

                records.append({
                    "InvoiceNo": invoice_no,
                    "StockCode": prod["code"],
                    "Description": prod["desc"],
                    "Quantity": qty,
                    "InvoiceDate": invoice_dt.strftime("%Y-%m-%d %H:%M:%S"),
                    "UnitPrice": unit_price,
                    "CustomerID": cid,
                    "CustomerName": customer_name,
                    "State": state,
                    "Country": "India",
                    "Category": prod["cat"],
                    "PaymentMethod": np.random.choice(payment_methods, p=payment_weights),
                    "IsCOD": is_cod,
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
                        "CustomerName": customer_name,
                        "State": state,
                        "Country": "India",
                        "Category": prod["cat"],
                        "PaymentMethod": np.random.choice(payment_methods, p=payment_weights),
                        "IsCOD": is_cod,
                    })

    df = pd.DataFrame(records)

    # Guest checkouts (~8% missing CustomerIDs — common in Indian e-commerce
    # where many users still prefer not to create accounts)
    missing_mask = np.random.random(len(df)) < 0.08
    df.loc[missing_mask, "CustomerID"] = np.nan

    # ~0.2% promo orders with UnitPrice = 0 (free samples / deep discounts)
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
        print(f"Generated {len(df):,} Indian e-commerce transactions across "
              f"{df['CustomerID'].nunique():,} unique customers.")
        print(f"Saved raw transaction dataset to: {output_path}")

    return df


if __name__ == "__main__":
    generate_synthetic_transactions()
