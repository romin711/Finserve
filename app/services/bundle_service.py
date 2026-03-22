from collections import defaultdict


FREQUENTLY_BOUGHT_TOGETHER = [
    ("bread", "butter"),
    ("pasta", "sauce"),
    ("shampoo", "conditioner"),
]


def _normalize(value):
    return str(value or "").strip().lower()


def _pick_low_sales_match(products, keyword):
    keyword = _normalize(keyword)
    matches = [product for product in products if keyword in _normalize(product.name)]
    if not matches:
        return None
    return min(matches, key=lambda product: (product.total_sales, product.name.lower()))


def _pick_high_sales_match(products, keyword):
    keyword = _normalize(keyword)
    matches = [product for product in products if keyword in _normalize(product.name)]
    if not matches:
        return None
    return max(matches, key=lambda product: (product.total_sales, product.name.lower()))


def generate_bundle_suggestions(products):
    suggestions = []
    seen_pairs = set()

    # Rule path 1: Frequent co-purchase style pairing by keyword intent.
    for first_keyword, second_keyword in FREQUENTLY_BOUGHT_TOGETHER:
        first_product = _pick_low_sales_match(products, first_keyword)
        second_product = _pick_high_sales_match(products, second_keyword)
        if not first_product or not second_product or first_product.id == second_product.id:
            continue

        pair_key = tuple(sorted((first_product.id, second_product.id)))
        if pair_key in seen_pairs:
            continue
        seen_pairs.add(pair_key)

        suggestions.append(
            {
                "category": (
                    first_product.category
                    if _normalize(first_product.category) == _normalize(second_product.category)
                    else "Cross-Sell"
                ),
                "product_a": first_product.name,
                "product_b": second_product.name,
                "reason": "Frequently bought together",
                "suggestion": (
                    f"Bundle {first_product.name} with {second_product.name} for better sales"
                ),
            }
        )

    # Rule path 2: Same-category fallback pairing.
    products_by_category = defaultdict(list)
    for product in products:
        products_by_category[product.category].append(product)

    for category, category_products in products_by_category.items():
        if len(category_products) < 2:
            continue

        sorted_products = sorted(
            category_products,
            key=lambda product: (product.total_sales, product.name.lower()),
        )

        slow_product = sorted_products[0]
        fast_product = sorted_products[-1]

        if slow_product.id == fast_product.id:
            continue

        pair_key = tuple(sorted((slow_product.id, fast_product.id)))
        if pair_key in seen_pairs:
            continue
        seen_pairs.add(pair_key)

        suggestions.append(
            {
                "category": category,
                "product_a": slow_product.name,
                "product_b": fast_product.name,
                "reason": "Same category",
                "suggestion": (
                    f"Bundle {slow_product.name} with {fast_product.name} for better sales"
                ),
            }
        )

    return suggestions
