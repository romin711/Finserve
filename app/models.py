from datetime import date

from app.extensions import db


class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock_quantity = db.Column(db.Integer, nullable=False)
    last_sold_date = db.Column(db.Date, nullable=True)
    expiry_date = db.Column(db.Date, nullable=True)
    total_sales = db.Column(db.Float, nullable=False, default=0.0)

    def to_dict(self):
        today = date.today()
        if self.expiry_date:
            days_to_expire = (self.expiry_date - today).days
            if days_to_expire < 0:
                expiry_label = "Expired"
            elif days_to_expire == 0:
                expiry_label = "Expires today"
            else:
                expiry_label = f"Expires in {days_to_expire} days"
        else:
            days_to_expire = None
            expiry_label = None

        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "price": self.price,
            "stock_quantity": self.stock_quantity,
            "last_sold_date": (
                self.last_sold_date.isoformat() if self.last_sold_date else None
            ),
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
            "days_to_expire": days_to_expire,
            "expiry_label": expiry_label,
            "total_sales": self.total_sales,
        }
