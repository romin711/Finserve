from datetime import date

from flask import Blueprint, jsonify, request

from app.models import Product
from app.services.discount_service import get_dead_stock_discount_suggestions

dead_stock_bp = Blueprint("dead_stock", __name__)


def parse_threshold(value, default_value):
    if value is None:
        return default_value
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


@dead_stock_bp.route("/dead-stock", methods=["GET"])
def get_dead_stock_status():
    sales_threshold = parse_threshold(request.args.get("sales_threshold"), 10)
    days_threshold = parse_threshold(request.args.get("days_threshold"), 15)

    if sales_threshold is None or days_threshold is None:
        return (
            jsonify(
                {
                    "message": "sales_threshold and days_threshold must be numeric.",
                }
            ),
            400,
        )

    today = date.today()
    products = Product.query.all()

    response_data = []
    for product in products:
        days_unsold = None
        if product.last_sold_date:
            days_unsold = (today - product.last_sold_date).days

        is_dead_stock = (
            product.total_sales < sales_threshold
            and days_unsold is not None
            and days_unsold > days_threshold
        )

        response_data.append(
            {
                "product_name": product.name,
                "days_unsold": days_unsold,
                "status": "Dead Stock" if is_dead_stock else "Active",
            }
        )

    return jsonify(response_data), 200


@dead_stock_bp.route("/dead-stock/discounts", methods=["GET"])
def get_dead_stock_discounts():
    sales_threshold = parse_threshold(request.args.get("sales_threshold"), 10)
    days_threshold = parse_threshold(request.args.get("days_threshold"), 15)
    high_stock_threshold = parse_threshold(request.args.get("high_stock_threshold"), 100)

    if sales_threshold is None or days_threshold is None or high_stock_threshold is None:
        return (
            jsonify(
                {
                    "message": (
                        "sales_threshold, days_threshold, and high_stock_threshold "
                        "must be numeric."
                    ),
                }
            ),
            400,
        )

    products = Product.query.all()
    suggestions = get_dead_stock_discount_suggestions(
        products=products,
        sales_threshold=sales_threshold,
        days_threshold=days_threshold,
        high_stock_threshold=high_stock_threshold,
    )
    return jsonify(suggestions), 200
