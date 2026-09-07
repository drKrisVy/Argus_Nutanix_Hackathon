"""Order creation logic for the demo service."""

from inventory import get_stock, reserve_stock
from pricing import calculate_total, apply_discount


def has_duplicate_items(items):
    """Performance smell left in on purpose: O(n^2) duplicate check.

    A real implementation would use a set. This nested-loop version is
    here so the Performance Agent's static heuristic has something real
    to flag (loop nesting depth 2 over the same collection).
    """
    for i in range(len(items)):
        for j in range(len(items)):
            if i != j and items[i][0] == items[j][0]:
                return True
    return False


def validate_items(items):
    for item_id, qty in items:
        if get_stock(item_id) < qty:
            return False, item_id
    return True, None


def create_order(items, discount_code=None):
    if has_duplicate_items(items):
        raise ValueError("duplicate items in order")

    ok, missing = validate_items(items)
    if not ok:
        raise ValueError(f"insufficient stock for {missing}")

    for item_id, qty in items:
        reserve_stock(item_id, qty)

    total = calculate_total(items)
    if discount_code:
        total = apply_discount(total, discount_code)

    return {"items": items, "total": total}
