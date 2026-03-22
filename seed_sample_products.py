"""seed_sample_products.py

Realistic product data generator for Finverse.

Expiry tiers (guaranteed representation per batch):
  - Near  : 1–3 days   (~20 % of products)
  - Mid   : 7–15 days  (~30 % of products)
  - Safe  : 20–40 days (~50 % of products)

All expiry offsets, days_unsold values, and stock quantities are unique
within a single seed run to prevent identical rows.
"""

import argparse
import math
import random
from datetime import date, timedelta

from app import create_app
from app.extensions import db
from app.models import Product


# ---------------------------------------------------------------------------
# Product name pools
# ---------------------------------------------------------------------------

CATEGORIES = [
    "grocery",
    "dairy",
    "cold_drinks",
    "namkeen",
]

NAME_POOL = {
    "grocery": [
        "Aashirvaad Atta 5kg",
        "India Gate Basmati Rice",
        "Tata Salt 1kg",
        "Madhur Sugar 1kg",
        "Fortune Sunflower Oil 1L",
        "Toor Dal Premium 1kg",
        "Moong Dal 500g",
        "Everest Turmeric Powder",
        "MDH Garam Masala",
        "Suhana Paneer Tikka Masala",
        "Chana Dal 1kg",
        "Brooke Bond Red Label Tea",
        "Tata Agni Tea",
        "Nescafe Classic Coffee",
        "Maggi 2-Minute Noodles",
        "Parle-G Biscuits",
        "Good Day Cashew Cookies",
        "Kissan Mixed Fruit Jam",
        "Saffola Gold Oil 5L",
        "Dawat Rozana Rice",
    ],
    "dairy": [
        "Amul Taaza Milk 500ml",
        "Amul Gold Milk 500ml",
        "Mother Dairy Milk",
        "Amul Butter 100g",
        "Amul Cheese Slices",
        "Gowardhan Ghee 1L",
        "Amul Masti Dahi",
        "Mother Dairy Mishti Doi",
        "Britannia Cheese Block",
        "Epigamia Greek Yogurt",
        "Malai Paneer 200g",
        "Amul Fresh Cream",
        "Yakult Probiotic Drink",
        "Flavored Milk Bottle",
    ],
    "cold_drinks": [
        "Coca-Cola 2L",
        "Thums Up 750ml",
        "Sprite 600ml",
        "Pepsi 1.25L",
        "Limca 600ml",
        "Maaza Mango Drink 1.2L",
        "Slice Mango Drink 600ml",
        "Fanta Orange 750ml",
        "Mountain Dew 600ml",
        "Red Bull Energy Drink",
        "Monster Energy Drink",
        "Sting Energy 250ml",
        "Paper Boat Aamras",
        "Kinley Soda Water",
    ],
    "namkeen": [
        "Haldiram's Bhujia Sev",
        "Haldiram's Moong Dal",
        "Haldiram's Khatta Meetha",
        "Balaji Ratlami Sev",
        "Balaji Chataka Pataka",
        "Bikano Aloo Bhujia",
        "Haldiram's Navrattan",
        "Bingo Mad Angles",
        "Kurkure Masala Munch",
        "Lays Classic Salted",
        "Lays Magic Masala",
        "Balaji Wafers Cream & Onion",
        "Diet Chivda 500g",
        "Banana Chips 200g",
        "Bakarwadi 250g",
    ],
}


# ---------------------------------------------------------------------------
# Expiry tier definitions
# ---------------------------------------------------------------------------

EXPIRY_TIERS = {
    "near": (1, 3),    # critical urgency
    "mid":  (7, 15),   # high urgency
    "safe": (20, 40),  # low urgency
}


def _tier_weights(count: int) -> list[tuple[str, int]]:
    """Return (tier_name, slots) pairs that sum to *count*.

    Distribution: 20 % near, 30 % mid, 50 % safe.
    At least 1 slot per tier when count >= 3.
    """
    near_n = max(1, math.floor(count * 0.20))
    mid_n  = max(1, math.floor(count * 0.30))
    safe_n = max(1, count - near_n - mid_n)
    return [("near", near_n), ("mid", mid_n), ("safe", safe_n)]


def _build_expiry_offsets(count: int) -> list[int]:
    """Return *count* unique expiry offsets respecting tier distribution."""
    tiers = _tier_weights(count)
    used: set[int] = set()
    offsets: list[int] = []

    for tier_name, slots in tiers:
        lo, hi = EXPIRY_TIERS[tier_name]
        for _ in range(slots):
            available = [d for d in range(lo, hi + 1) if d not in used]
            if not available:
                # Overflow into full 1-40 range if tier pool runs dry.
                available = [d for d in range(1, 41) if d not in used] or list(range(1, 41))
            offset = random.choice(available)
            used.add(offset)
            offsets.append(offset)

    # Shuffle so tier order isn't preserved in the insert sequence.
    random.shuffle(offsets)
    return offsets


# ---------------------------------------------------------------------------
# Individual field generators
# ---------------------------------------------------------------------------

def _unique_pool(lo: int, hi: int, count: int) -> list[int]:
    """Return *count* unique integers drawn from [lo, hi].

    If the range is narrower than *count*, values wrap (repeat minimally).
    """
    population = list(range(lo, hi + 1))
    if count <= len(population):
        return random.sample(population, count)
    # More products than available unique values: fill + top up with extras.
    result = population[:]
    random.shuffle(result)
    while len(result) < count:
        result.extend(random.sample(population, min(len(population), count - len(result))))
    return result[:count]


def _logical_total_sales(
    days_unsold: int,
    stock_quantity: int,
    category: str,
) -> float:
    """Compute a realistic total_sales figure.

    Logic:
    - Products unsold for 1-10 days  → higher sales (30–200)
    - Products unsold for 11-40 days → medium sales  (10–80)
    - Products unsold for 41+ days   → low sales     (0–20)
    - Electronics get a 1.5× multiplier (higher unit value)
    - High stock (>70) suggest slower movement → gentle downward nudge
    """
    if days_unsold <= 10:
        base = random.uniform(30, 200)
    elif days_unsold <= 40:
        base = random.uniform(10, 80)
    else:
        base = random.uniform(0, 20)

    multiplier = 1.0
    if category in ("cold_drinks", "dairy"):
        multiplier = random.uniform(1.2, 1.8)

    if stock_quantity > 70:
        multiplier *= random.uniform(0.6, 0.9)

    return round(base * multiplier, 2)


def _price_for_category(category: str) -> float:
    if category == "grocery":
        return round(random.uniform(50, 450), 2)
    if category == "dairy":
        return round(random.uniform(30, 250), 2)
    if category == "cold_drinks":
        return round(random.uniform(40, 150), 2)
    return round(random.uniform(10, 200), 2)


# ---------------------------------------------------------------------------
# Product builder
# ---------------------------------------------------------------------------

def _build_product(index: int, expiry_offset: int, days_unsold: int, stock: int) -> Product:
    category = random.choice(CATEGORIES)
    base_name = random.choice(NAME_POOL[category])
    name = f"{base_name} #{index}"

    today = date.today()
    expiry_date   = today + timedelta(days=expiry_offset)
    last_sold_date = today - timedelta(days=days_unsold)
    total_sales   = _logical_total_sales(days_unsold, stock, category)

    return Product(
        name=name,
        category=category,
        price=_price_for_category(category),
        stock_quantity=stock,
        last_sold_date=last_sold_date,
        expiry_date=expiry_date,
        total_sales=total_sales,
    )


# ---------------------------------------------------------------------------
# Main insert function
# ---------------------------------------------------------------------------

def insert_sample_products(count: int, reset: bool = False) -> None:
    app = create_app()
    with app.app_context():
        db.create_all()

        if reset:
            Product.query.delete()
            db.session.commit()

        start_index   = Product.query.count() + 1
        expiry_offsets = _build_expiry_offsets(count)          # unique, tiered
        unsold_days    = _unique_pool(1, 120, count)           # unique 1-120
        stock_qtys     = _unique_pool(5, 100, count)           # unique 5-100
        # Shuffle unsold/stock so they're not sorted.
        random.shuffle(unsold_days)
        random.shuffle(stock_qtys)

        products = [
            _build_product(
                index=start_index + i,
                expiry_offset=expiry_offsets[i],
                days_unsold=unsold_days[i],
                stock=stock_qtys[i],
            )
            for i in range(count)
        ]

        db.session.add_all(products)
        db.session.commit()

        total = Product.query.count()
        near  = sum(1 for p in products if (p.expiry_date - date.today()).days <= 3)
        mid   = sum(1 for p in products if 7 <= (p.expiry_date - date.today()).days <= 15)
        safe  = sum(1 for p in products if (p.expiry_date - date.today()).days >= 20)

        print(f"Inserted {len(products)} products (total in DB: {total})")
        print(f"  Expiry distribution → near (1-3d): {near} | mid (7-15d): {mid} | safe (20+d): {safe}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate and insert realistic sample product data into SQLite."
    )
    parser.add_argument(
        "--count",
        type=int,
        default=20,
        help="Number of products to generate (minimum: 20).",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing products before inserting new sample data.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    count = max(args.count, 20)
    insert_sample_products(count=count, reset=args.reset)


if __name__ == "__main__":
    main()
