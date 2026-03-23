"""Unit tests for app/services/offer_service.py"""
import pytest
from app.services.offer_service import generate_offer_for_product


def _offer(**kwargs):
    defaults = dict(is_dead_stock=False, days_to_expire=None, is_high_stock=False, is_slow_moving=False)
    defaults.update(kwargs)
    return generate_offer_for_product(**defaults)


# ── Rule 1: dead stock + expiry <= 5 days ──────────────────────────────────

def test_buy_1_get_1_on_near_expiry_dead_stock():
    result = _offer(is_dead_stock=True, days_to_expire=5)
    assert result["offer_type"] == "BUY_1_GET_1"

def test_buy_1_get_1_not_triggered_at_6_days():
    # 6 days → falls to Rule 2 (<=10)
    result = _offer(is_dead_stock=True, days_to_expire=6)
    assert result["offer_type"] == "FLAT_40_OFF"


# ── Rule 2: dead stock + expiry <= 10 days ─────────────────────────────────

def test_flat_40_off_on_10_days():
    result = _offer(is_dead_stock=True, days_to_expire=10)
    assert result["offer_type"] == "FLAT_40_OFF"

def test_flat_40_off_not_triggered_beyond_10_days():
    # > 10 days and no high_stock → BUY_2_GET_1 only if high_stock, else NO_ACTION
    result = _offer(is_dead_stock=True, days_to_expire=11, is_high_stock=False)
    assert result["offer_type"] == "NO_ACTION"


# ── Rule 3: dead stock + high stock ────────────────────────────────────────

def test_buy_2_get_1_dead_and_high_stock():
    result = _offer(is_dead_stock=True, is_high_stock=True, days_to_expire=None)
    assert result["offer_type"] == "BUY_2_GET_1"


# ── Rule 4: active but slow-moving ─────────────────────────────────────────

def test_bundle_for_slow_moving_active():
    result = _offer(is_dead_stock=False, is_slow_moving=True)
    assert result["offer_type"] == "BUNDLE"


# ── Rule 5: healthy product ─────────────────────────────────────────────────

def test_no_action_for_healthy_product():
    result = _offer()
    assert result["offer_type"] == "NO_ACTION"


# ── Priority: Rule 1 wins over Rule 3 ──────────────────────────────────────

def test_rule1_takes_priority_over_rule3():
    result = _offer(is_dead_stock=True, days_to_expire=3, is_high_stock=True)
    assert result["offer_type"] == "BUY_1_GET_1"


# ── days_to_expire=None with dead stock falls through to Rule 3 or NO_ACTION

def test_dead_stock_no_expiry_no_high_stock():
    result = _offer(is_dead_stock=True, days_to_expire=None, is_high_stock=False)
    assert result["offer_type"] == "NO_ACTION"

def test_dead_stock_no_expiry_with_high_stock():
    result = _offer(is_dead_stock=True, days_to_expire=None, is_high_stock=True)
    assert result["offer_type"] == "BUY_2_GET_1"
