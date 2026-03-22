from flask import Blueprint, jsonify, request

from app.models import Product
from app.services.analytics_service import calculate_dashboard_analytics

dashboard_bp = Blueprint("dashboard_analytics", __name__)


def parse_threshold(value, default_value):
    if value is None:
        return default_value
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


@dashboard_bp.route("/dashboard-analytics", methods=["GET"])
def get_dashboard_analytics():
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
    analytics = calculate_dashboard_analytics(
        products=products,
        sales_threshold=sales_threshold,
        days_threshold=days_threshold,
        high_stock_threshold=high_stock_threshold,
    )
    return jsonify(analytics), 200
