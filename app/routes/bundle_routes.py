from flask import Blueprint, jsonify

from app.models import Product
from app.services.bundle_service import generate_bundle_suggestions

bundle_bp = Blueprint("bundle_suggestions", __name__)


@bundle_bp.route("/bundle-suggestions", methods=["GET"])
def get_bundle_suggestions():
    products = Product.query.all()
    suggestions = generate_bundle_suggestions(products)
    return jsonify(suggestions), 200
