<div align="center">

# 🏦 Finserve

### Retail Inventory Intelligence Platform

[![CI](https://github.com/romin711/Finserve/actions/workflows/ci.yml/badge.svg)](https://github.com/romin711/Finserve/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0.3-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-3.1.1-D71F00?logo=sqlalchemy&logoColor=white)](https://flask-sqlalchemy.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

*Detect dead stock, prioritize expiring inventory, generate intelligent offer actions, and monitor recovery potential — all from a single visual dashboard.*

</div>

---

## 📑 Table of Contents

- [✨ Features](#-features)
- [🛠 Tech Stack](#-tech-stack)
- [🏗 Architecture](#-architecture)
- [📁 Project Structure](#-project-structure)
- [📊 Data Model](#-data-model)
- [📐 Business Rules](#-business-rules)
- [🚀 Quick Start](#-quick-start)
- [▶️ Run the App](#️-run-the-app)
- [📡 API Reference](#-api-reference)
- [🖥 Frontend Dashboard](#-frontend-dashboard)
- [🌱 Sample Data Generator](#-sample-data-generator)
- [⏰ Daily Analysis Scheduler](#-daily-analysis-scheduler)
- [⚙️ Configuration](#️-configuration)
- [🔧 Troubleshooting](#-troubleshooting)
- [🧪 Development & Testing](#-development--testing)
- [🏭 Production Notes](#-production-notes)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)

---

## ✨ Features

| Feature | Description |
|---|---|
| 📦 **Product CRUD APIs** | Full create / read / update / delete endpoints for product records |
| 🪦 **Dead Stock Detection** | Flags products based on low sales and extended unsold duration |
| 🏷 **Offer Recommendation Engine** | Automatically assigns `BUY_1_GET_1`, `FLAT_40_OFF`, `BUY_2_GET_1`, `BUNDLE`, or `NO_ACTION` |
| 🎁 **Bundle Suggestion Engine** | Keyword and category fallback logic to suggest complementary bundles |
| 📈 **Dashboard Analytics** | Aggregated metrics for stock health, recovery potential, and category distribution |
| 🕐 **Daily Snapshot Scheduler** | Scheduled job that persists analysis snapshots to JSON for trend reporting |

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.10+, Flask 3.0.3 |
| **ORM / DB** | Flask-SQLAlchemy 3.1.1, SQLite |
| **Frontend** | Vanilla JS, CSS (served via Flask templates) |
| **Testing** | pytest 8.0+ |
| **CI/CD** | GitHub Actions |

---

## 🏗 Architecture

Finserve follows a clean layered structure:

| Layer | Responsibility |
|---|---|
| `routes/` | HTTP request / response contracts |
| `services/` | Business logic and recommendation rules |
| `models.py` | SQLAlchemy entity definitions |
| `static/` + `templates/` | Frontend UI assets |

**Core data flow:**

```
HTTP Request
    │
    ▼
routes/          ← validates input, delegates to service
    │
    ▼
services/        ← applies business rules (dead stock, offers, pricing)
    │
    ▼
models.py        ← SQLAlchemy ORM ↔ SQLite
    │
    ▼
JSON Response    ← enriched with computed fields
```

> The daily scheduler runs independently, consuming the same service layer and writing snapshots to `instance/daily_analysis_snapshot.json`.

---

## 📁 Project Structure

```text
Finserve/
├── app/
│   ├── __init__.py               # App factory & startup schema patch
│   ├── extensions.py             # SQLAlchemy instance
│   ├── models.py                 # Product entity
│   ├── routes/
│   │   ├── product_routes.py
│   │   ├── dead_stock_routes.py
│   │   ├── bundle_routes.py
│   │   ├── dashboard_routes.py
│   │   └── ui_routes.py
│   ├── services/
│   │   ├── analytics_service.py
│   │   ├── bundle_service.py
│   │   ├── daily_analysis_service.py
│   │   ├── discount_service.py
│   │   ├── offer_service.py
│   │   ├── prediction_service.py
│   │   └── pricing_service.py
│   ├── static/
│   │   ├── css/styles.css
│   │   └── js/app.js
│   └── templates/
│       └── index.html
├── config.py
├── run.py
├── requirements.txt
├── requirements-dev.txt
├── seed_sample_products.py
├── daily_analysis_scheduler.py
├── conftest.py
├── tests/
└── instance/
    └── daily_analysis_snapshot.json
```

---

## 📊 Data Model

### `Product` — `app/models.py`

| Field | Type | Notes |
|---|---|---|
| `id` | `int` | Primary key, auto-increment |
| `name` | `string` | Required |
| `category` | `string` | Required |
| `price` | `float` | Required |
| `stock_quantity` | `int` | Required |
| `last_sold_date` | `date` | Optional |
| `expiry_date` | `date` | Optional in schema; required by create API |
| `total_sales` | `float` | Required |

**Computed fields** returned in API responses:

`days_unsold` · `days_to_expire` · `status` · `offer_type` · `discount_pct` · `final_price` · `savings`

### Startup Schema Compatibility

On startup, the app automatically patches older databases that are missing the `expiry_date` column:

```sql
ALTER TABLE products ADD COLUMN expiry_date DATE
```

---

## 📐 Business Rules

### 🪦 Dead Stock Criteria

A product is classified as dead stock when **all** of the following are true:

- `total_sales < sales_threshold` *(default: `10`)*
- `days_unsold > days_threshold` *(default: `15`)*
- `last_sold_date` is set

### 💸 Discount Suggestion — `GET /dead-stock/discounts`

| Condition | Discount |
|---|---|
| `days_unsold > 30` | **30%** |
| `15 ≤ days_unsold ≤ 30` | **20%** |
| Otherwise | **10%** |
| `stock_quantity > high_stock_threshold` *(default: 100)* | **+5% bonus** |

### 🏷 Offer Type Priority

Offers are assigned in the following priority order:

| Priority | Condition | Offer |
|---|---|---|
| 1 | Dead stock **and** `days_to_expire ≤ 5` | `BUY_1_GET_1` |
| 2 | Dead stock **and** `days_to_expire ≤ 10` | `FLAT_40_OFF` |
| 3 | Dead stock **and** high stock | `BUY_2_GET_1` |
| 4 | Active but slow-moving | `BUNDLE` |
| 5 | Otherwise | `NO_ACTION` |

### 💰 Pricing Breakdown — `compute_pricing_breakdown()`

Returns: `original_price` · `discount_pct` · `final_price` · `effective_price` · `savings`

---

## 🚀 Quick Start

### Prerequisites

- Python `3.10+`
- `pip`

### 1. Clone & Install

```bash
git clone https://github.com/romin711/Finserve.git
cd Finserve

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Seed Demo Data

```bash
python seed_sample_products.py --count 20 --reset
```

---

## ▶️ Run the App

```bash
python run.py
```

By default the app starts with `debug=False`. To enable debug mode:

```bash
FLASK_DEBUG=1 python run.py
```

Open the dashboard in your browser:

```
http://127.0.0.1:5000/
```

---

## 📡 API Reference

All responses are JSON.

> **Note:** Product endpoints are available on both `/api/products` and `/products` prefixes.

### Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/products` | Create a new product |
| `GET` | `/api/products` | List all products with computed intelligence |
| `PUT` | `/api/products/<id>` | Update an existing product |
| `DELETE` | `/api/products/<id>` | Delete a product |
| `GET` | `/dead-stock` | Dead stock status list |
| `GET` | `/dead-stock/discounts` | Discount recommendations |
| `GET` | `/bundle-suggestions` | Bundle pair recommendations |
| `GET` | `/dashboard-analytics` | Aggregated dashboard metrics |

### Example: Create a Product

```bash
curl -X POST http://127.0.0.1:5000/api/products \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Amul Butter 100g",
    "category": "dairy",
    "price": 58.0,
    "stock_quantity": 90,
    "last_sold_date": "2026-03-01",
    "expiry_date": "2026-03-28",
    "total_sales": 7.5
  }'
```

### Example: List Products with Custom Thresholds

```bash
curl "http://127.0.0.1:5000/products?sales_threshold=12&days_threshold=20&high_stock_threshold=100"
```

---

## 🖥 Frontend Dashboard

The dashboard at `http://127.0.0.1:5000/` provides:

- **Metric cards** — total products, dead stock count, total inventory value
- **Category filters** — All · Grocery · Dairy · Cold Drinks · Namkeen
- **Urgency badges** — derived from `days_to_expire`
- **Product cards** — offer type, pricing breakdown, and stock status per item

> Data source: `GET /products`

---

## 🌱 Sample Data Generator

```bash
python seed_sample_products.py --count 30 --reset
```

| Option | Description |
|---|---|
| `--count` | Number of products to generate *(minimum: 20)* |
| `--reset` | Clear existing records before insert |

The seeder generates products across `grocery`, `dairy`, `cold_drinks`, and `namkeen` categories with varied expiry tiers and realistic sales distributions.

---

## ⏰ Daily Analysis Scheduler

Run continuously with a daily interval:

```bash
python daily_analysis_scheduler.py --interval-seconds 86400
```

Run a quick local simulation:

```bash
python daily_analysis_scheduler.py --interval-seconds 5 --iterations 3
```

### Arguments

| Argument | Description |
|---|---|
| `--interval-seconds` | Seconds between analysis runs |
| `--iterations` | Total number of runs before exit *(omit for infinite)* |
| `--sales-threshold` | Override default sales threshold |
| `--days-threshold` | Override default days-unsold threshold |
| `--high-stock-threshold` | Override default high-stock threshold |

Output is written to `instance/daily_analysis_snapshot.json`.

---

## ⚙️ Configuration

`config.py` defaults:

| Key | Default |
|---|---|
| `SQLALCHEMY_DATABASE_URI` | `sqlite:///products.db` |
| `SQLALCHEMY_TRACK_MODIFICATIONS` | `False` |

---

## 🔧 Troubleshooting

| Symptom | Fix |
|---|---|
| Empty dashboard or blank API response | Run `python seed_sample_products.py --count 20 --reset` |
| `400 Bad Request` on create / update | Ensure dates are `YYYY-MM-DD`; `price`, `stock_quantity`, `total_sales` must be numeric; include `expiry_date` in create payload |
| Old DB missing `expiry_date` column | Restart the app once — the startup schema patch applies automatically |
| Frontend fails to load data | Confirm the backend is running on `127.0.0.1:5000` |

---

## 🧪 Development & Testing

Install dev dependencies and run the full test suite:

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Tests cover the service layer (`discount_service`, `offer_service`, `pricing_service`, `bundle_service`) and run without a live Flask app or database.

CI runs automatically on every push and pull request via [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

---

## 🏭 Production Notes

> The following steps are recommended before deploying Finserve to a production environment.

- **WSGI server** — serve Flask with [Gunicorn](https://gunicorn.org/)
- **Reverse proxy** — place behind Nginx for TLS termination and static file serving
- **Database** — migrate from SQLite to a managed relational database (PostgreSQL recommended)
- **Configuration** — use environment variables or a secrets manager instead of hardcoded config
- **Scheduling** — replace the standalone scheduler script with a cron job or a worker queue (e.g., Celery + Redis)

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/your-feature-name`
3. **Commit** your changes with clear messages: `git commit -m "feat: add your feature"`
4. **Push** to your fork: `git push origin feature/your-feature-name`
5. **Open** a Pull Request describing your changes

Please ensure all existing tests pass (`pytest tests/ -v`) before submitting.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

<div align="center">

Made by [romin711](https://github.com/romin711)

</div>
