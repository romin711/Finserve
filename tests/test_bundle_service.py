"""Unit tests for app/services/bundle_service.py"""
import pytest
from app.services.bundle_service import generate_bundle_suggestions


class _FakeProduct:
    _next_id = 1

    def __init__(self, name, category, total_sales):
        self.id = _FakeProduct._next_id
        _FakeProduct._next_id += 1
        self.name = name
        self.category = category
        self.total_sales = total_sales


def setup_function():
    """Reset auto-increment id counter before each test function."""
    _FakeProduct._next_id = 1


# ── keyword-based pairing ────────────────────────────────────────────────────

def test_keyword_pair_bread_butter():
    products = [
        _FakeProduct("Whole Grain Bread", "Bakery", 5),
        _FakeProduct("Salted Butter", "Dairy", 50),
    ]
    suggestions = generate_bundle_suggestions(products)
    names = [(s["product_a"], s["product_b"]) for s in suggestions]
    assert ("Whole Grain Bread", "Salted Butter") in names


def test_keyword_pair_pasta_sauce():
    products = [
        _FakeProduct("Penne Pasta", "Grocery", 3),
        _FakeProduct("Tomato Pasta Sauce", "Grocery", 30),
    ]
    suggestions = generate_bundle_suggestions(products)
    product_names_flat = [name for s in suggestions for name in (s["product_a"], s["product_b"])]
    assert "Penne Pasta" in product_names_flat


# ── same-category fallback pairing ──────────────────────────────────────────

def test_same_category_pairing():
    products = [
        _FakeProduct("Widget A", "Electronics", 2),
        _FakeProduct("Widget B", "Electronics", 100),
    ]
    suggestions = generate_bundle_suggestions(products)
    categories = [s["category"] for s in suggestions]
    assert "Electronics" in categories


def test_same_category_reason():
    products = [
        _FakeProduct("Gadget X", "Electronics", 1),
        _FakeProduct("Gadget Y", "Electronics", 99),
    ]
    suggestions = generate_bundle_suggestions(products)
    same_cat = [s for s in suggestions if s["category"] == "Electronics"]
    assert any(s["reason"] == "Same category" for s in same_cat)


# ── no duplicate pairs ───────────────────────────────────────────────────────

def test_no_duplicate_pairs():
    # Both a keyword hit and same-category could match the same pair;
    # the second encounter should be skipped.
    products = [
        _FakeProduct("Pasta Tubes", "Grocery", 2),
        _FakeProduct("Pasta Sauce", "Grocery", 80),
    ]
    suggestions = generate_bundle_suggestions(products)
    seen = set()
    for s in suggestions:
        key = tuple(sorted((s["product_a"], s["product_b"])))
        assert key not in seen, f"Duplicate pair found: {key}"
        seen.add(key)


# ── single product per category does not pair ────────────────────────────────

def test_single_product_category_not_paired():
    products = [
        _FakeProduct("Lonely Item", "Unique", 10),
    ]
    suggestions = generate_bundle_suggestions(products)
    unique_pairs = [s for s in suggestions if s["category"] == "Unique"]
    assert unique_pairs == []


# ── empty product list ───────────────────────────────────────────────────────

def test_empty_product_list():
    suggestions = generate_bundle_suggestions([])
    assert suggestions == []
