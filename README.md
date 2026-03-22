# Finverse

Finverse is a full-stack Flask project for retail inventory intelligence. It helps teams detect dead stock, prioritize expiring inventory, generate offer actions, and monitor recovery potential from a visual dashboard.

## Highlights

- Product CRUD APIs
- Dead stock detection based on sales and unsold duration
- Offer recommendation engine (`BUY_1_GET_1`, `FLAT_40_OFF`, `BUY_2_GET_1`, `BUNDLE`, `NO_ACTION`)
- Bundle suggestion engine with keyword and category fallback logic
- Dashboard analytics for stock health and recovery potential
- Daily analysis snapshot generator for scheduled reporting

## Table of Contents

- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Data Model](#data-model)
- [Business Rules](#business-rules)
- [Quick Start](#quick-start)
- [Run the App](#run-the-app)
- [API Reference](#api-reference)
- [Frontend Dashboard](#frontend-dashboard)
- [Sample Data Generator](#sample-data-generator)
- [Daily Analysis Scheduler](#daily-analysis-scheduler)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Production Notes](#production-notes)

## Architecture

Finverse follows a clean layered structure:

- `routes/` handles HTTP request/response contracts
- `services/` contains business logic and recommendation rules
- `models.py` defines SQLAlchemy entities
- `static/` + `templates/` provide the UI

Core flow:

1. Product data is stored in SQLite.
2. APIs compute dead stock, urgency, offers, and pricing details.
3. Frontend consumes `GET /products` and renders product intelligence cards.
4. Scheduler can periodically persist analysis snapshots to JSON.

## Project Structure

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
|-- run.py
|-- requirements.txt
|-- seed_sample_products.py
|-- daily_analysis_scheduler.py
`-- instance/
    `-- daily_analysis_snapshot.json
```

## Data Model

`Product` (`app/models.py`) fields:

- `id` (int, primary key)
- `name` (string, required)
- `category` (string, required)
- `price` (float, required)
- `stock_quantity` (int, required)
- `last_sold_date` (date, optional)
- `expiry_date` (date, optional in schema, required by create API)
- `total_sales` (float, required)

Computed output fields are also returned in API responses, including `days_unsold`, `days_to_expire`, `status`, `offer_type`, and pricing breakdown metrics.

### Startup Schema Compatibility

On startup, the app checks if the `products` table is missing `expiry_date`. If missing, it applies:

```sql
ALTER TABLE products ADD COLUMN expiry_date DATE
```

## Business Rules

### Dead Stock Criteria

Product is marked dead stock when all are true:

- `total_sales < sales_threshold` (default `10`)
- `days_unsold > days_threshold` (default `15`)
- `last_sold_date` exists

### Discount Suggestion

`GET /dead-stock/discounts` rules:

- `days_unsold > 30` -> `30%`
- `15 <= days_unsold <= 30` -> `20%`
- otherwise -> `10%`
- if `stock_quantity > high_stock_threshold` (default `100`) -> `+5%`

### Offer Type Priority

Applied in this order:

1. dead stock and `days_to_expire <= 5` -> `BUY_1_GET_1`
2. dead stock and `days_to_expire <= 10` -> `FLAT_40_OFF`
3. dead stock and high stock -> `BUY_2_GET_1`
4. active but slow-moving -> `BUNDLE`
5. else -> `NO_ACTION`

### Pricing Breakdown

`compute_pricing_breakdown()` returns:

- `original_price`
- `discount_pct`
- `final_price`
- `effective_price`
- `savings`

## Quick Start

### Prerequisites

- Python `3.10+`
- `pip`

### Install Dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Seed Demo Data

```bash
python seed_sample_products.py --count 20 --reset
```

## Run the App

```bash
python run.py
```

Open:

- Dashboard: `http://127.0.0.1:5000/`

## API Reference

All responses are JSON.

### Base Product Routes

The same product handlers are available on both prefixes:

- `/api/products`
- `/products`

### Endpoints

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/products` or `/products` | Create product |
| `GET` | `/api/products` or `/products` | List products with computed intelligence |
| `PUT` | `/api/products/<id>` or `/products/<id>` | Update product |
| `DELETE` | `/api/products/<id>` or `/products/<id>` | Delete product |
| `GET` | `/dead-stock` | Dead stock status |
| `GET` | `/dead-stock/discounts` | Discount recommendations |
| `GET` | `/bundle-suggestions` | Bundle recommendations |
| `GET` | `/dashboard-analytics` | Aggregated dashboard metrics |

### Create Product Example

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

### Product Listing Example

```bash
curl "http://127.0.0.1:5000/products?sales_threshold=12&days_threshold=20&high_stock_threshold=100"
```

## Frontend Dashboard

Dashboard route `/` displays:

- top metric cards (total products, dead stock count, inventory value)
- category filters (`All`, `Grocery`, `Dairy`, `Cold Drinks`, `Namkeen`)
- urgency badges derived from `days_to_expire`
- offer and pricing breakdown sections per product

Data source for UI is `GET /products`.

## Sample Data Generator

Script: `seed_sample_products.py`

```bash
python seed_sample_products.py --count 30 --reset
```

Options:

- `--count`: number of products, minimum enforced as `20`
- `--reset`: clear existing records before insert

Seeder behavior:

- categories: `grocery`, `dairy`, `cold_drinks`, `namkeen`
- expiry distribution tiers: near (1-3), mid (7-15), safe (20-40)
- realistic sales and stock distributions for testing recommendations

## Daily Analysis Scheduler

Script: `daily_analysis_scheduler.py`

Run continuously (daily interval):

```bash
python daily_analysis_scheduler.py --interval-seconds 86400
```

Local simulation run:

```bash
python daily_analysis_scheduler.py --interval-seconds 5 --iterations 3
```

Arguments:

- `--interval-seconds`
- `--iterations`
- `--sales-threshold`
- `--days-threshold`
- `--high-stock-threshold`

Output snapshot file:

- `instance/daily_analysis_snapshot.json`

## Configuration

`config.py` defaults:

- `SQLALCHEMY_DATABASE_URI = "sqlite:///products.db"`
- `SQLALCHEMY_TRACK_MODIFICATIONS = False`

## Troubleshooting

- Empty dashboard/API output:
  - seed data with `python seed_sample_products.py --count 20 --reset`
- `400` on create/update:
  - date must be `YYYY-MM-DD`
  - `price`, `stock_quantity`, and `total_sales` must be numeric
  - include `expiry_date` in create payload
- Old local DB missing `expiry_date`:
  - restart app once to allow startup schema patch
- Frontend unable to load data:
  - verify backend is running on `127.0.0.1:5000`

## Production Notes

For production readiness:

- serve Flask with Gunicorn
- place behind Nginx reverse proxy
- move from SQLite to managed relational DB
- add environment-based configuration
- schedule analysis job via cron/worker
- add tests and CI pipeline
