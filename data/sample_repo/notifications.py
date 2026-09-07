"""Order confirmation notifications for the demo service."""

from orders import create_order


def format_confirmation(order):
    lines = [f"{item_id} x{qty}" for item_id, qty in order["items"]]
    return "Order confirmed:\n" + "\n".join(lines) + f"\nTotal: {order['total']}"


def send_confirmation(items, discount_code=None):
    order = create_order(items, discount_code=discount_code)
    message = format_confirmation(order)
    print(message)
    return message
