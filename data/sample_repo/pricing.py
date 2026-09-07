"""Pricing helpers for the demo order service."""

_DISCOUNT_CODES = {
    "SAVE10": 0.10,
    "SAVE20": 0.20,
}

_PRICES = {
    "sku-1": 499,
    "sku-2": 999,
    "sku-3": 199,
}


def price_of(item_id):
    return _PRICES.get(item_id, 0)


def calculate_total(items):
    """items: list of (item_id, qty) tuples."""
    total = 0
    for item_id, qty in items:
        total += price_of(item_id) * qty
    return total


def apply_discount(total, code):
    rate = _DISCOUNT_CODES.get(code, 0)
    return round(total * (1 - rate), 2)
