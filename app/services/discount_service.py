from datetime import date


def suggest_discount_percentage(days_unsold, stock_quantity, high_stock_threshold=100):
    if days_unsold > 30:
        discount = 30
    elif 15 <= days_unsold <= 30:
        discount = 20
    else:
        discount = 10

    if stock_quantity > high_stock_threshold:
        discount += 5

    return discount


def get_dead_stock_discount_suggestions(
    products,
    sales_threshold=10,
    days_threshold=15,
    high_stock_threshold=100,
    today=None,
):
    if today is None:
        today = date.today()

    suggestions = []
    for product in products:
        if not product.last_sold_date:
            continue

        days_unsold = (today - product.last_sold_date).days
        is_dead_stock = product.total_sales < sales_threshold and days_unsold > days_threshold
        if not is_dead_stock:
            continue

        discount = suggest_discount_percentage(
            days_unsold=days_unsold,
            stock_quantity=product.stock_quantity,
            high_stock_threshold=high_stock_threshold,
        )

        suggestions.append(
            {
                "product_name": product.name,
                "recommended_discount": f"{discount}%",
            }
        )

    return suggestions
