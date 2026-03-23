"""Unit tests for app/services/discount_service.py"""
import pytest
from app.services.discount_service import suggest_discount_percentage, get_dead_stock_discount_suggestions
from datetime import date


# ── suggest_discount_percentage ──────────────────────────────────────────────

def test_discount_more_than_30_days():
    assert suggest_discount_percentage(days_unsold=31, stock_quantity=50) == 30

def test_discount_exactly_30_days():
    assert suggest_discount_percentage(days_unsold=30, stock_quantity=50) == 20

def test_discount_between_15_and_30_days():
    assert suggest_discount_percentage(days_unsold=20, stock_quantity=50) == 20

def test_discount_exactly_15_days():
    assert suggest_discount_percentage(days_unsold=15, stock_quantity=50) == 20

def test_discount_less_than_15_days():
    assert suggest_discount_percentage(days_unsold=10, stock_quantity=50) == 10

def test_high_stock_adds_5_percent():
    base = suggest_discount_percentage(days_unsold=10, stock_quantity=50)
    high = suggest_discount_percentage(days_unsold=10, stock_quantity=101)
    assert high == base + 5

def test_high_stock_threshold_custom():
    # stock_quantity == threshold → not high stock
    assert suggest_discount_percentage(days_unsold=10, stock_quantity=200, high_stock_threshold=200) == 10
    # stock_quantity > threshold → high stock
    assert suggest_discount_percentage(days_unsold=10, stock_quantity=201, high_stock_threshold=200) == 15


# ── get_dead_stock_discount_suggestions ─────────────────────────────────────

class _FakeProduct:
    def __init__(self, name, total_sales, last_sold_date, stock_quantity):
        self.name = name
        self.total_sales = total_sales
        self.last_sold_date = last_sold_date
        self.stock_quantity = stock_quantity


def test_dead_stock_suggestion_returned():
    today = date(2026, 3, 22)
    products = [
        _FakeProduct("Stale Item", total_sales=2, last_sold_date=date(2026, 2, 28), stock_quantity=50),
    ]
    suggestions = get_dead_stock_discount_suggestions(products, today=today)
    assert len(suggestions) == 1
    assert suggestions[0]["product_name"] == "Stale Item"
    assert "%" in suggestions[0]["recommended_discount"]


def test_active_product_not_suggested():
    today = date(2026, 3, 22)
    products = [
        _FakeProduct("Fresh Item", total_sales=50, last_sold_date=date(2026, 3, 20), stock_quantity=20),
    ]
    suggestions = get_dead_stock_discount_suggestions(products, today=today)
    assert suggestions == []


def test_no_last_sold_date_skipped():
    today = date(2026, 3, 22)
    products = [
        _FakeProduct("Unknown Item", total_sales=2, last_sold_date=None, stock_quantity=50),
    ]
    suggestions = get_dead_stock_discount_suggestions(products, today=today)
    assert suggestions == []
