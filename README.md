# Finverse

Finverse is a Flask + SQLite retail intelligence project that helps identify dead stock, recommend tactical offers, suggest bundles, and visualize product urgency in a dashboard.

The app includes:

- CRUD APIs for product management
- rule-based dead stock detection
- dynamic offer generation (B1G1, flat discount, bundle, no action)
- pricing breakdown per offer type
- bundle suggestion engine
- dashboard analytics endpoints
- sample data seeding and scheduler-based daily analysis snapshots

## Table of Contents

1. Overview
2. Tech Stack
3. Project Structure
4. Data Model
5. Business Rules
6. Local Setup
7. Running the Application
8. API Reference
9. Frontend Behavior
10. Data Seeding
11. Daily Analysis Scheduler
12. Configuration
13. Troubleshooting
14. Deployment Notes

## 1. Overview

Finverse solves a common retail problem: inventory that is not moving fast enough, especially products close to expiry.

It evaluates each product using:

- sales and unsold-day thresholds
- stock pressure
- expiry urgency

Based on these signals, the system assigns status and offer actions such as:

- `BUY_1_GET_1`
- `FLAT_40_OFF`
- `BUY_2_GET_1`
- `BUNDLE`
- `NO_ACTION`

## 2. Tech Stack

- Backend: Flask 3
- ORM: Flask-SQLAlchemy
- Database: SQLite (`instance/products.db`)
- Frontend: HTML, CSS, vanilla JavaScript
- Automation: Python script loop for periodic daily analysis

Dependencies are pinned in `requirements.txt`.

## 3. Project Structure

```text
.
|-- app/
|   |-- __init__.py
|   |-- extensions.py
|   |-- models.py
|   |-- routes/
|   |   |-- product_routes.py
|   |   |-- dead_stock_routes.py
|   |   |-- bundle_routes.py
|   |   |-- dashboard_routes.py
|   |   `-- ui_routes.py
|   |-- services/
|   |   |-- analytics_service.py
|   |   |-- bundle_service.py
|   |   |-- daily_analysis_service.py
|   |   |-- discount_service.py
|   |   |-- offer_service.py
|   |   |-- prediction_service.py
|   |   `-- pricing_service.py
|   |-- static/
|   |   |-- css/styles.css
|   |   `-- js/app.js
|   `-- templates/
|       `-- index.html
|-- config.py
|-- daily_analysis_scheduler.py
|-- requirements.txt
|-- run.py
|-- seed_sample_products.py
`-- instance/
    `-- daily_analysis_snapshot.json
```

## 4. Data Model

`Product` model (`app/models.py`) fields:

- `id` (integer, primary key)
- `name` (string, required)
- `category` (string, required)
- `price` (float, required)
- `stock_quantity` (integer, required)
- `last_sold_date` (date, nullable)
- `expiry_date` (date, nullable)
- `total_sales` (float, required)

`to_dict()` also returns computed fields:

- `days_to_expire`
- `expiry_label`

### Schema evolution behavior

At startup, `create_app()` runs `db.create_all()` and also checks for missing `expiry_date` on existing `products` tables. If missing, it runs:

```sql
ALTER TABLE products ADD COLUMN expiry_date DATE
```

This enables lightweight backward compatibility for older local DB files.

## 5. Business Rules

### Dead stock rule

A product is dead stock when all conditions are true:

- `total_sales < sales_threshold` (default `10`)
- `days_unsold > days_threshold` (default `15`)
- `last_sold_date` is available

### Discount recommendation rule (`/dead-stock/discounts`)

- `days_unsold > 30` -> `30%`
- `15 <= days_unsold <= 30` -> `20%`
- otherwise -> `10%`
- if `stock_quantity > high_stock_threshold` (default `100`) -> add `5%`

### Offer generation rule (`/products`)

For each product, Finverse computes offer type in priority order:

1. dead stock and `days_to_expire <= 5` -> `BUY_1_GET_1`
2. dead stock and `days_to_expire <= 10` -> `FLAT_40_OFF`
3. dead stock and high stock -> `BUY_2_GET_1`
4. active but slow moving -> `BUNDLE`
5. otherwise -> `NO_ACTION`

If a product is slow-moving and marked `BUNDLE`, bundle text is sourced from bundle suggestion generation.

### Pricing breakdown rule

`compute_pricing_breakdown()` returns:

- `original_price`
- `discount_pct`
- `final_price`
- `effective_price`
- `savings`

Examples:

- `BUY_1_GET_1` -> effective per-unit `50%` savings
- `FLAT_40_OFF` -> direct `40%` off
- `BUY_2_GET_1` -> effective `33%` off
- `BUNDLE` -> indicative `10%` discount

## 6. Local Setup

### Prerequisites

- Python 3.10+
- `pip`

### Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 7. Running the Application

### Start server

```bash
python run.py
```

Default URL:

- Dashboard: `http://127.0.0.1:5000/`

### Quick first run flow

```bash
python seed_sample_products.py --count 20 --reset
python run.py
```

## 8. API Reference

All responses are JSON unless otherwise noted.

### 8.1 Product APIs

Product blueprint is mounted at two prefixes:

- `/api/products`
- `/products`

Both routes expose the same handlers.

#### Create product

- Method: `POST`
- Path: `/api/products` or `/products`

Required body fields:

- `name`
- `category`
- `price`
- `stock_quantity`
- `total_sales`
- `expiry_date` (format: `YYYY-MM-DD`)

Optional:

- `last_sold_date` (format: `YYYY-MM-DD`)

Example:

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

#### Get product list with computed intelligence

- Method: `GET`
- Path: `/api/products` or `/products`

Optional query params:

- `sales_threshold` (float, default `10`)
- `days_threshold` (float, default `15`)
- `high_stock_threshold` (float, default `100`)

Each product in response includes raw fields plus computed fields such as:

- `days_unsold`
- `days_to_expire`
- `status`
- `offer_type`
- `message`
- `suggestion`
- `original_price`
- `discount_pct`
- `final_price`
- `effective_price`
- `savings`

Example:

```bash
curl "http://127.0.0.1:5000/products?sales_threshold=12&days_threshold=20"
```

#### Update product

- Method: `PUT`
- Path: `/api/products/<product_id>` or `/products/<product_id>`

Example:

```bash
curl -X PUT http://127.0.0.1:5000/api/products/1 \
  -H "Content-Type: application/json" \
  -d '{"price": 49.0, "stock_quantity": 75, "expiry_date": "2026-04-03"}'
```

#### Delete product

- Method: `DELETE`
- Path: `/api/products/<product_id>` or `/products/<product_id>`

Example:

```bash
curl -X DELETE http://127.0.0.1:5000/api/products/1
```

### 8.2 Dead stock status

- Method: `GET`
- Path: `/dead-stock`

Query params:

- `sales_threshold` (float, default `10`)
- `days_threshold` (float, default `15`)

Response row format:

```json
{
  "product_name": "Amul Butter 100g",
  "days_unsold": 21,
  "status": "Dead Stock"
}
```

### 8.3 Dead stock discount suggestions

- Method: `GET`
- Path: `/dead-stock/discounts`

Query params:

- `sales_threshold` (float, default `10`)
- `days_threshold` (float, default `15`)
- `high_stock_threshold` (float, default `100`)

Response row format:

```json
{
  "product_name": "Amul Butter 100g",
  "recommended_discount": "25%"
}
```

### 8.4 Bundle suggestions

- Method: `GET`
- Path: `/bundle-suggestions`

Response row fields:

- `category`
- `product_a`
- `product_b`
- `reason`
- `suggestion`

Generation strategy:

- keyword intent pairs first (frequently bought together style)
- category-based fallback (lowest sales + highest sales in category)

### 8.5 Dashboard analytics

- Method: `GET`
- Path: `/dashboard-analytics`

Query params:

- `sales_threshold` (float, default `10`)
- `days_threshold` (float, default `15`)
- `high_stock_threshold` (float, default `100`)

Response format:

```json
{
  "total_products": 20,
  "dead_stock_count": 8,
  "total_dead_stock_value": 11435.0,
  "recovery_potential": 8720.25
}
```

## 9. Frontend Behavior

Route `/` renders `app/templates/index.html` and loads `app/static/js/app.js`.

Key behavior:

- fetches product intelligence from `GET /products`
- shows top metrics: total products, dead stock count, total inventory value
- renders category filters: `All`, `Grocery`, `Dairy`, `Cold Drinks`, `Namkeen`
- computes urgency badges from `days_to_expire`
- renders offer cards and pricing breakdown per product
- supports manual refresh from the UI button

Note: frontend total value currently uses all products from `/products`, not only dead stock.

## 10. Data Seeding

Use seeded products to quickly test scenarios.

```bash
python seed_sample_products.py --count 20 --reset
```

CLI arguments:

- `--count`: minimum enforced as `20`
- `--reset`: clears current `products` before insert

Seeder characteristics:

- categories: `grocery`, `dairy`, `cold_drinks`, `namkeen`
- expiry tiers: near (1-3 days), mid (7-15 days), safe (20-40 days)
- unique unsold-day and stock distributions in each run
- realistic sales logic based on unsold days and category multipliers

## 11. Daily Analysis Scheduler

Run simulated periodic analysis:

```bash
python daily_analysis_scheduler.py --interval-seconds 86400
```

Quick test run:

```bash
python daily_analysis_scheduler.py --interval-seconds 5 --iterations 3
```

Useful arguments:

- `--interval-seconds` (default `86400`)
- `--iterations` (default: run forever)
- `--sales-threshold`
- `--days-threshold`
- `--high-stock-threshold`

Each cycle:

- runs dead stock analysis
- writes snapshot JSON to `instance/daily_analysis_snapshot.json`
- prints a timestamped log message

Snapshot shape:

```json
{
  "analyzed_at": "2026-03-22T10:30:00",
  "total_products": 20,
  "dead_stock_count": 8,
  "rows": [
    {
      "product_name": "...",
      "days_unsold": 34,
      "status": "Dead Stock",
      "suggestion": "Offer 30% discount"
    }
  ]
}
```

## 12. Configuration

`config.py`:

- `SQLALCHEMY_DATABASE_URI = "sqlite:///products.db"`
- `SQLALCHEMY_TRACK_MODIFICATIONS = False`

By default, SQLite DB is created in Flask instance path.

## 13. Troubleshooting

- Server starts but no products visible:
  - Run `python seed_sample_products.py --count 20 --reset`
- `400` on product creation:
  - ensure required fields include `expiry_date`
  - ensure date format is `YYYY-MM-DD`
  - ensure `price`, `stock_quantity`, and `total_sales` are numeric
- Existing DB missing `expiry_date`:
  - restart app once; startup migration helper adds it
- Frontend fetch error:
  - verify backend is running at `http://127.0.0.1:5000`

## 14. Deployment Notes

For production-grade deployment, recommended upgrades are:

- run behind Gunicorn + reverse proxy (Nginx)
- move from SQLite to a managed relational DB
- externalize config via environment variables
- add structured logging + health checks
- schedule `daily_analysis_scheduler.py` via system scheduler/worker
