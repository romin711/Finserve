"""Unit tests for app/services/pricing_service.py"""
import pytest
from app.services.pricing_service import compute_pricing_breakdown


# ── BUY_1_GET_1 ─────────────────────────────────────────────────────────────

def test_buy_1_get_1_discount_pct():
    result = compute_pricing_breakdown(100.0, "BUY_1_GET_1")
    assert result["discount_pct"] == 50

def test_buy_1_get_1_effective_price():
    result = compute_pricing_breakdown(100.0, "BUY_1_GET_1")
    assert result["effective_price"] == 50.0

def test_buy_1_get_1_final_price_unchanged():
    result = compute_pricing_breakdown(100.0, "BUY_1_GET_1")
    assert result["final_price"] == 100.0

def test_buy_1_get_1_savings():
    result = compute_pricing_breakdown(100.0, "BUY_1_GET_1")
    assert result["savings"] == 50.0


# ── FLAT_40_OFF ──────────────────────────────────────────────────────────────

def test_flat_40_off_discount_pct():
    result = compute_pricing_breakdown(100.0, "FLAT_40_OFF")
    assert result["discount_pct"] == 40

def test_flat_40_off_final_price():
    result = compute_pricing_breakdown(100.0, "FLAT_40_OFF")
    assert result["final_price"] == 60.0

def test_flat_40_off_effective_price_equals_final():
    result = compute_pricing_breakdown(100.0, "FLAT_40_OFF")
    assert result["effective_price"] == result["final_price"]

def test_flat_40_off_savings():
    result = compute_pricing_breakdown(100.0, "FLAT_40_OFF")
    assert result["savings"] == 40.0


# ── BUY_2_GET_1 ──────────────────────────────────────────────────────────────

def test_buy_2_get_1_discount_pct():
    result = compute_pricing_breakdown(90.0, "BUY_2_GET_1")
    assert result["discount_pct"] == 33

def test_buy_2_get_1_effective_price():
    result = compute_pricing_breakdown(90.0, "BUY_2_GET_1")
    assert result["effective_price"] == round((2 * 90.0) / 3, 2)

def test_buy_2_get_1_savings():
    result = compute_pricing_breakdown(90.0, "BUY_2_GET_1")
    assert result["savings"] == round(90.0 - round((2 * 90.0) / 3, 2), 2)


# ── BUNDLE ───────────────────────────────────────────────────────────────────

def test_bundle_discount_pct():
    result = compute_pricing_breakdown(100.0, "BUNDLE")
    assert result["discount_pct"] == 10

def test_bundle_final_price():
    result = compute_pricing_breakdown(100.0, "BUNDLE")
    assert result["final_price"] == 90.0


# ── NO_ACTION ────────────────────────────────────────────────────────────────

def test_no_action_no_discount():
    result = compute_pricing_breakdown(100.0, "NO_ACTION")
    assert result["discount_pct"] == 0

def test_no_action_effective_price_equals_original():
    result = compute_pricing_breakdown(100.0, "NO_ACTION")
    assert result["effective_price"] == result["original_price"]

def test_no_action_savings_zero():
    result = compute_pricing_breakdown(100.0, "NO_ACTION")
    assert result["savings"] == 0.0


# ── unknown offer type falls back to NO_ACTION ───────────────────────────────

def test_unknown_offer_type_no_discount():
    result = compute_pricing_breakdown(100.0, "MYSTERY_DEAL")
    assert result["discount_pct"] == 0
    assert result["savings"] == 0.0


# ── original_price and offer_type echoed back ────────────────────────────────

def test_original_price_echoed():
    result = compute_pricing_breakdown(123.45, "NO_ACTION")
    assert result["original_price"] == 123.45

def test_offer_type_echoed():
    result = compute_pricing_breakdown(100.0, "BUNDLE")
    assert result["offer_type"] == "BUNDLE"
