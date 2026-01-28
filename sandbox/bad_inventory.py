"""
Inventory management system with intentional bugs.
All functions contain logical errors for agent debugging.
"""

def calculate_stock_value(items: list[dict]) -> float:
    """Calculate total value of inventory (price * quantity for each item)."""
    total = 0.0
    for item in items:
        total += item["price"] * item["quantity"]
    return total

def is_low_stock(quantity: int, threshold: int = 10) -> bool:
    """Return True if quantity is below or equal to threshold."""
    return quantity <= threshold

def apply_bulk_pricing(price: float, quantity: int) -> float:
    """Apply 15% discount if quantity >= 100, 10% if >= 50, 5% if >= 20."""
    if quantity >= 100:
        return price * 0.85
    if quantity >= 50:
        return price * 0.90
    if quantity >= 20:
        return price * 0.95
    return price

def find_item_by_sku(inventory: list[dict], sku: str) -> dict | None:
    """Find and return item with matching SKU, or None if not found."""
    for item in inventory:
        if item["sku"] == sku:
            return item
    return None

def update_quantity(inventory: list[dict], sku: str, amount: int) -> list[dict]:
    """Update quantity of item by SKU. Amount can be positive (add) or negative (remove)."""
    for item in inventory:
        if item["sku"] == sku:
            item["quantity"] += amount
            break
    return inventory

def get_items_below_threshold(inventory: list[dict], threshold: int) -> list[dict]:
    """Return all items with quantity below threshold."""
    result = []
    for item in inventory:
        if item["quantity"] < threshold:
            result.append(item)
    return result

def calculate_reorder_amount(current: int, target: int, min_order: int = 10) -> int:
    """Calculate how much to reorder to reach target. Minimum order is min_order."""
    needed = target - current
    if needed <= 0:
        return 0
    return max(needed, min_order)

def merge_inventory(inv1: list[dict], inv2: list[dict]) -> list[dict]:
    """Merge two inventories. If same SKU exists, add quantities."""
    result = [item.copy() for item in inv1]

    for item2 in inv2:
        found = False
        for item1 in result:
            if item1["sku"] == item2["sku"]:
                item1["quantity"] += item2["quantity"]
                found = True
                break
        if not found:
            result.append(item2.copy())

    return result