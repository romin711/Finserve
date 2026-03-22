def generate_offer_for_product(
    *,
    is_dead_stock,
    days_to_expire,
    is_high_stock,
    is_slow_moving,
):
    # Rule 1: Dead stock + expiry <= 5 days
    if is_dead_stock and days_to_expire is not None and days_to_expire <= 5:
        return {
            "offer_type": "BUY_1_GET_1",
            "message": "Buy 1 Get 1 Free",
        }

    # Rule 2: Dead stock + expiry <= 10 days
    if is_dead_stock and days_to_expire is not None and days_to_expire <= 10:
        return {
            "offer_type": "FLAT_40_OFF",
            "message": "Flat 40% Off",
        }

    # Rule 3: Dead stock + high stock
    if is_dead_stock and is_high_stock:
        return {
            "offer_type": "BUY_2_GET_1",
            "message": "Buy 2 Get 1 Free",
        }

    # Rule 4: Active but slow-moving
    if (not is_dead_stock) and is_slow_moving:
        return {
            "offer_type": "BUNDLE",
            "message": "Bundle with related product",
        }

    # Rule 5: Healthy product
    return {
        "offer_type": "NO_ACTION",
        "message": "No action needed",
    }
