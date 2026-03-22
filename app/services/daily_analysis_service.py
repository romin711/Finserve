import json
from datetime import date, datetime
from pathlib import Path

from flask import current_app

from app.models import Product
from app.services.discount_service import get_dead_stock_discount_suggestions


def run_dead_stock_analysis(
    sales_threshold=10,
    days_threshold=15,
    high_stock_threshold=100,
):
    today = date.today()
    products = Product.query.all()

    discount_rows = get_dead_stock_discount_suggestions(
        products=products,
        sales_threshold=sales_threshold,
        days_threshold=days_threshold,
        high_stock_threshold=high_stock_threshold,
        today=today,
    )
    discount_map = {
        row["product_name"]: row["recommended_discount"] for row in discount_rows
    }

    rows = []
    dead_stock_count = 0
    for product in products:
        days_unsold = None
        if product.last_sold_date:
            days_unsold = (today - product.last_sold_date).days

        is_dead_stock = (
            product.total_sales < sales_threshold
            and days_unsold is not None
            and days_unsold > days_threshold
        )

        if is_dead_stock:
            dead_stock_count += 1
            suggestion = f"Offer {discount_map.get(product.name, '10%')} discount"
            status = "Dead Stock"
        else:
            suggestion = "No action needed"
            status = "Active"

        rows.append(
            {
                "product_name": product.name,
                "days_unsold": days_unsold,
                "status": status,
                "suggestion": suggestion,
            }
        )

    result = {
        "analyzed_at": datetime.now().isoformat(timespec="seconds"),
        "total_products": len(products),
        "dead_stock_count": dead_stock_count,
        "rows": rows,
    }

    _save_analysis_snapshot(result)
    return result


def _save_analysis_snapshot(data):
    Path(current_app.instance_path).mkdir(parents=True, exist_ok=True)
    output_file = Path(current_app.instance_path) / "daily_analysis_snapshot.json"
    output_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
