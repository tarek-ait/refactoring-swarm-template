"""
Tests for the buggy inventory module.
These tests define the CORRECT expected behavior.
"""

import pytest
from bad_inventory import (
    calculate_stock_value,
    is_low_stock,
    apply_bulk_pricing,
    find_item_by_sku,
    update_quantity,
    get_items_below_threshold,
    calculate_reorder_amount,
    merge_inventory,
)


def test_calculate_stock_value():
    items = [
        {"name": "Widget", "price": 10.0, "quantity": 5},
        {"name": "Gadget", "price": 20.0, "quantity": 3},
    ]
    # 10*5 + 20*3 = 50 + 60 = 110
    assert calculate_stock_value(items) == 110.0


def test_calculate_stock_value_empty():
    assert calculate_stock_value([]) == 0.0


def test_is_low_stock_below():
    assert is_low_stock(5, threshold=10) is True


def test_is_low_stock_equal():
    # Equal to threshold should also be considered low
    assert is_low_stock(10, threshold=10) is True


def test_is_low_stock_above():
    assert is_low_stock(15, threshold=10) is False


def test_apply_bulk_pricing_100_plus():
    # 100+ units = 15% off
    assert apply_bulk_pricing(100.0, 100) == 85.0


def test_apply_bulk_pricing_50_plus():
    # 50-99 units = 10% off
    assert apply_bulk_pricing(100.0, 50) == 90.0


def test_apply_bulk_pricing_20_plus():
    # 20-49 units = 5% off
    assert apply_bulk_pricing(100.0, 25) == 95.0


def test_apply_bulk_pricing_no_discount():
    # Under 20 units = no discount
    assert apply_bulk_pricing(100.0, 10) == 100.0


def test_find_item_by_sku_found():
    inventory = [
        {"sku": "ABC123", "name": "Widget", "quantity": 10},
        {"sku": "DEF456", "name": "Gadget", "quantity": 5},
    ]
    result = find_item_by_sku(inventory, "ABC123")
    assert result is not None
    assert result["name"] == "Widget"


def test_find_item_by_sku_not_found():
    inventory = [
        {"sku": "ABC123", "name": "Widget", "quantity": 10},
    ]
    result = find_item_by_sku(inventory, "XYZ999")
    assert result is None


def test_update_quantity_add():
    inventory = [
        {"sku": "ABC123", "name": "Widget", "quantity": 10},
    ]
    result = update_quantity(inventory, "ABC123", 5)
    assert result[0]["quantity"] == 15  # 10 + 5


def test_update_quantity_subtract():
    inventory = [
        {"sku": "ABC123", "name": "Widget", "quantity": 10},
    ]
    result = update_quantity(inventory, "ABC123", -3)
    assert result[0]["quantity"] == 7  # 10 - 3


def test_get_items_below_threshold():
    inventory = [
        {"sku": "A", "quantity": 5},
        {"sku": "B", "quantity": 15},
        {"sku": "C", "quantity": 8},
    ]
    result = get_items_below_threshold(inventory, 10)
    assert len(result) == 2
    skus = [item["sku"] for item in result]
    assert "A" in skus
    assert "C" in skus


def test_calculate_reorder_amount_needed():
    # Current 30, target 100, need 70
    assert calculate_reorder_amount(30, 100) == 70


def test_calculate_reorder_amount_below_minimum():
    # Current 95, target 100, need 5 but min is 10
    assert calculate_reorder_amount(95, 100, min_order=10) == 10


def test_calculate_reorder_amount_not_needed():
    # Current already at or above target
    assert calculate_reorder_amount(100, 50) == 0


def test_merge_inventory_no_overlap():
    inv1 = [{"sku": "A", "quantity": 10}]
    inv2 = [{"sku": "B", "quantity": 20}]
    result = merge_inventory(inv1, inv2)
    assert len(result) == 2
    # Original should not be modified
    assert len(inv1) == 1


def test_merge_inventory_with_overlap():
    inv1 = [{"sku": "A", "quantity": 10}]
    inv2 = [{"sku": "A", "quantity": 5}]
    result = merge_inventory(inv1, inv2)
    assert len(result) == 1
    assert result[0]["quantity"] == 15
    # Original should not be modified (deep copy needed)
    assert inv1[0]["quantity"] == 10