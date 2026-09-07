"""Entry point tying the demo service together."""

from notifications import send_confirmation


def main():
    items = [("sku-1", 2), ("sku-3", 1)]
    send_confirmation(items, discount_code="SAVE10")


if __name__ == "__main__":
    main()
