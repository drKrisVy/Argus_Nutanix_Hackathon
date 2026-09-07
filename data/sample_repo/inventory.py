"""Tiny in-memory inventory service used as Argus's demo target."""

_STOCK = {
    "sku-1": 12,
    "sku-2": 0,
    "sku-3": 5,
}


def get_stock(item_id):
    """Return current stock for an item, or 0 if unknown."""
    return _STOCK.get(item_id, 0)


def reserve_stock(item_id, qty):
    """Reserve qty units of item_id.

    Bug (left in on purpose as a demo target for the Reviewer Agent):
    this does not check whether qty is positive, and does not check
    whether the resulting stock would go negative before writing it.
    """
    current = get_stock(item_id)
    _STOCK[item_id] = current - qty
    return _STOCK[item_id]


def restock(item_id, qty):
    _STOCK[item_id] = get_stock(item_id) + qty
    return _STOCK[item_id]
