from flask import Flask
from sqlalchemy import inspect, text

from config import Config
from app.extensions import db
from app.routes.bundle_routes import bundle_bp
from app.routes.dashboard_routes import dashboard_bp
from app.routes.dead_stock_routes import dead_stock_bp
from app.routes.product_routes import product_bp
from app.routes.ui_routes import ui_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    with app.app_context():
        db.create_all()
        _ensure_products_table_columns()

    app.register_blueprint(product_bp, url_prefix="/api/products")
    app.register_blueprint(product_bp, url_prefix="/products", name="products_public")
    app.register_blueprint(dead_stock_bp)
    app.register_blueprint(bundle_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(ui_bp)

    return app


def _ensure_products_table_columns():
    inspector = inspect(db.engine)
    table_names = set(inspector.get_table_names())
    if "products" not in table_names:
        return

    columns = {column["name"] for column in inspector.get_columns("products")}
    if "expiry_date" not in columns:
        db.session.execute(text("ALTER TABLE products ADD COLUMN expiry_date DATE"))
        db.session.commit()
