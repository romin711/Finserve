"""pricing_service.py

Computes a detailed pricing breakdown for a single product given its
original price and assigned offer type.

Offer type → pricing rules
──────────────────────────
BUY_1_GET_1  : customer pays for 1, gets 2 → effective_price = price / 2
               discount shown = 50 %
FLAT_40_OFF  : straight 40 % discount       → final_price = price * 0.60
               discount shown = 40 %
BUY_2_GET_1  : customer pays for 2, gets 3 → effective_price = (2 * price) / 3
               discount shown = 33 %
BUNDLE       : no fixed discount; 10 % indicative discount applied
NO_ACTION    : no discount
"""

from __future__ import annotations


def compute_pricing_breakdown(price: float, offer_type: str) -> dict:
    """Return a pricing breakdown dict for the given *price* and *offer_type*.

    Keys returned
    ─────────────
    original_price   – unchanged input price
    discount_pct     – integer percentage off (0 if no discount)
    final_price      – price after flat-rate discount (same as original when
                       the offer is unit-based, e.g. B1G1)
    effective_price  – per-unit cost the customer actually pays accounting for
                       free units (equals final_price for flat discounts)
    savings          – (original_price - effective_price) rounded to 2 dp
    offer_type       – echoed back for convenience
    """
    price = round(float(price), 2)

    if offer_type == "BUY_1_GET_1":
        # Pay for 1, receive 2 → 50 % effective saving per unit
        discount_pct    = 50
        final_price     = price                        # unit price unchanged
        effective_price = round(price / 2, 2)          # cost per item received

    elif offer_type == "FLAT_40_OFF":
        # Straight 40 % off the sticker price
        discount_pct    = 40
        final_price     = round(price * 0.60, 2)
        effective_price = final_price

    elif offer_type == "BUY_2_GET_1":
        # Pay for 2, receive 3 → ~33 % effective saving per unit
        discount_pct    = 33
        final_price     = price                        # unit price unchanged
        effective_price = round((2 * price) / 3, 2)

    elif offer_type == "BUNDLE":
        # Indicative 10 % discount when bundled
        discount_pct    = 10
        final_price     = round(price * 0.90, 2)
        effective_price = final_price

    else:
        # NO_ACTION or unknown
        discount_pct    = 0
        final_price     = price
        effective_price = price

    savings = round(price - effective_price, 2)

    return {
        "original_price":  price,
        "discount_pct":    discount_pct,
        "final_price":     final_price,
        "effective_price": effective_price,
        "savings":         savings,
        "offer_type":      offer_type,
    }
