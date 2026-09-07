# Demo target repo

A tiny, self-contained order-processing service used only as something
for Argus to analyze -- it is fixture data, not part of Argus itself.

- `inventory.py` -- stock tracking. Contains a seeded bug: `reserve_stock`
  never checks that `qty` is positive or that the resulting stock would
  stay non-negative.
- `pricing.py` -- price and discount calculation.
- `orders.py` -- ties inventory + pricing together. Contains a seeded
  performance smell: `has_duplicate_items` is an O(n^2) nested-loop check
  where a `set` would do.
- `notifications.py` -- formats and "sends" an order confirmation.
- `main.py` -- entry point.

These two seeded issues exist so the Reviewer Agent and Performance Agent
have something real to find during a demo.
