from datetime import date, datetime, timedelta

from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models import Product
from app.services.bundle_service import generate_bundle_suggestions
from app.services.offer_service import generate_offer_for_product
from app.services.pricing_service import compute_pricing_breakdown

product_bp = Blueprint("products", __name__)


def parse_date(date_str):
    if date_str in (None, ""):
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return None


def parse_number(value, cast_type):
    try:
        return cast_type(value)
    except (TypeError, ValueError):
        return None


def parse_threshold(value, default_value):
    if value is None:
        return default_value
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


@product_bp.route("", methods=["POST"])
def add_product():
    data = request.get_json() or {}

    required_fields = [
        "name",
        "category",
        "price",
        "stock_quantity",
        "total_sales",
        "expiry_date",
    ]
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        return (
            jsonify(
                {
                    "message": "Missing required fields.",
                    "missing_fields": missing_fields,
                }
            ),
            400,
        )

    last_sold_date = parse_date(data.get("last_sold_date"))
    if data.get("last_sold_date") and last_sold_date is None:
        return jsonify({"message": "Invalid date format. Use YYYY-MM-DD."}), 400
    expiry_date = parse_date(data.get("expiry_date"))
    if data.get("expiry_date") and expiry_date is None:
        return jsonify({"message": "Invalid expiry_date format. Use YYYY-MM-DD."}), 400

    price = parse_number(data.get("price"), float)
    stock_quantity = parse_number(data.get("stock_quantity"), int)
    total_sales = parse_number(data.get("total_sales"), float)
    if price is None or stock_quantity is None or total_sales is None:
        return jsonify({"message": "price, stock_quantity, and total_sales must be numeric."}), 400

    product = Product(
        name=data["name"],
        category=data["category"],
        price=price,
        stock_quantity=stock_quantity,
        last_sold_date=last_sold_date,
        expiry_date=expiry_date,
        total_sales=total_sales,
    )

    db.session.add(product)
    db.session.commit()

    return jsonify({"message": "Product added successfully.", "product": product.to_dict()}), 201


@product_bp.route("", methods=["GET"])
def get_all_products():
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

    today = date.today()
    products = Product.query.all()
    bundle_rows = generate_bundle_suggestions(products)
    bundle_by_product = {}
    for row in bundle_rows:
        suggestion = row.get("suggestion")
        product_a = row.get("product_a")
        product_b = row.get("product_b")
        if suggestion:
            if product_a and product_a not in bundle_by_product:
                bundle_by_product[product_a] = suggestion
            if product_b and product_b not in bundle_by_product:
                bundle_by_product[product_b] = suggestion

    response_data = []
    for product in products:
        days_unsold = None
        if product.last_sold_date:
            days_unsold = (today - product.last_sold_date).days
        effective_expiry_date = product.expiry_date or (today + timedelta(days=30))
        days_to_expire = (effective_expiry_date - today).days

        is_dead_stock = (
            product.total_sales < sales_threshold
            and days_unsold is not None
            and days_unsold > days_threshold
        )
        status = "Dead Stock" if is_dead_stock else "Active"
        is_high_stock = product.stock_quantity >= high_stock_threshold
        is_slow_moving = (
            not is_dead_stock
            and (
                product.total_sales < sales_threshold
                or (days_unsold is not None and days_unsold > (days_threshold / 2))
            )
        )
        offer = generate_offer_for_product(
            is_dead_stock=is_dead_stock,
            days_to_expire=days_to_expire,
            is_high_stock=is_high_stock,
            is_slow_moving=is_slow_moving,
        )
        offer_message = offer["message"]
        if offer["offer_type"] == "BUNDLE":
            offer_message = bundle_by_product.get(
                product.name, "Bundle with related product for better sales"
            )

        pricing = compute_pricing_breakdown(
            price=product.price,
            offer_type=offer["offer_type"],
        )

        product_data = product.to_dict()
        product_data.update(
            {
                "expiry_date": effective_expiry_date.isoformat(),
                "days_unsold": days_unsold,
                "days_to_expire": days_to_expire,
                "status": status,
                "offer_type": offer["offer_type"],
                "message": offer_message,
                "suggestion": offer_message,
                # Pricing breakdown
                "original_price":  pricing["original_price"],
                "discount_pct":    pricing["discount_pct"],
                "final_price":     pricing["final_price"],
                "effective_price": pricing["effective_price"],
                "savings":         pricing["savings"],
            }
        )
        response_data.append(product_data)

    return jsonify(response_data), 200


@product_bp.route("/<int:product_id>", methods=["PUT"])
def update_product(product_id):
    product = Product.query.get_or_404(product_id)
    data = request.get_json() or {}

    if "name" in data:
        product.name = data["name"]
    if "category" in data:
        product.category = data["category"]
    if "price" in data:
        price = parse_number(data["price"], float)
        if price is None:
            return jsonify({"message": "price must be numeric."}), 400
        product.price = price
    if "stock_quantity" in data:
        stock_quantity = parse_number(data["stock_quantity"], int)
        if stock_quantity is None:
            return jsonify({"message": "stock_quantity must be numeric."}), 400
        product.stock_quantity = stock_quantity
    if "total_sales" in data:
        total_sales = parse_number(data["total_sales"], float)
        if total_sales is None:
            return jsonify({"message": "total_sales must be numeric."}), 400
        product.total_sales = total_sales
    if "last_sold_date" in data:
        last_sold_date = parse_date(data["last_sold_date"])
        if data["last_sold_date"] and last_sold_date is None:
            return jsonify({"message": "Invalid date format. Use YYYY-MM-DD."}), 400
        product.last_sold_date = last_sold_date
    if "expiry_date" in data:
        expiry_date = parse_date(data["expiry_date"])
        if data["expiry_date"] and expiry_date is None:
            return jsonify({"message": "Invalid expiry_date format. Use YYYY-MM-DD."}), 400
        product.expiry_date = expiry_date

    db.session.commit()

    return jsonify({"message": "Product updated successfully.", "product": product.to_dict()}), 200


@product_bp.route("/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)

    db.session.delete(product)
    db.session.commit()

    return jsonify({"message": "Product deleted successfully."}), 200
