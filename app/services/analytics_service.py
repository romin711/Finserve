from datetime import date

from app.services.discount_service import suggest_discount_percentage


def calculate_dashboard_analytics(
    products,
    sales_threshold=10,
    days_threshold=15,
    high_stock_threshold=100,
    today=None,
):
    if today is None:
        today = date.today()

    total_products = len(products)
    dead_stock_count = 0
    total_dead_stock_value = 0.0
    recovery_potential = 0.0

    for product in products:
        if not product.last_sold_date:
            continue

        days_unsold = (today - product.last_sold_date).days
        is_dead_stock = product.total_sales < sales_threshold and days_unsold > days_threshold
        if not is_dead_stock:
            continue

        dead_stock_count += 1
        dead_stock_value = product.price * product.stock_quantity
        total_dead_stock_value += dead_stock_value

        discount = suggest_discount_percentage(
            days_unsold=days_unsold,
            stock_quantity=product.stock_quantity,
            high_stock_threshold=high_stock_threshold,
        )
        discounted_value = dead_stock_value * (1 - discount / 100)
        recovery_potential += discounted_value

    return {
        "total_products": total_products,
        "dead_stock_count": dead_stock_count,
        "total_dead_stock_value": round(total_dead_stock_value, 2),
        "recovery_potential": round(recovery_potential, 2),
    }
