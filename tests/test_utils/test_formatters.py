"""Unit tests for formatter utilities."""
import pytest
from src.models.order import Order, OrderItem, OrderStatus
from src.models.customer import Customer, CustomerTier
from src.utils.formatters import (
    format_currency,
    format_order_summary,
    format_customer_info,
    format_item_list,
)


class TestFormatCurrency:
    """Tests for currency formatting."""

    def test_format_usd(self):
        assert format_currency(1234.56) == "$1,234.56"

    def test_format_usd_zero(self):
        assert format_currency(0.0) == "$0.00"

    def test_format_eur(self):
        assert format_currency(100.0, "EUR") == "€100.00"

    def test_format_gbp(self):
        assert format_currency(50.0, "GBP") == "£50.00"

    def test_format_unknown_currency(self):
        assert format_currency(100.0, "XYZ") == "100.00 XYZ"

    def test_format_large_amount(self):
        assert format_currency(1234567890.12) == "$1,234,567,890.12"


class TestFormatOrderSummary:
    """Tests for order summary formatting."""

    def test_summary_contains_order_id(self):
        order = Order(id="ORD-00001", customer_id="C001")
        summary = format_order_summary(order)
        assert "ORD-00001" in summary

    def test_summary_contains_status(self):
        order = Order(id="ORD-00001", customer_id="C001")
        summary = format_order_summary(order)
        assert "PENDING" in summary

    def test_summary_contains_discount_line(self):
        order = Order(id="ORD-00001", customer_id="C001", discount_amount=5.0)
        summary = format_order_summary(order)
        assert "Discount: -$5.00" in summary

    def test_summary_contains_shipping_line(self):
        order = Order(id="ORD-00001", customer_id="C001", shipping_cost=9.99)
        summary = format_order_summary(order)
        assert "Shipping: $9.99" in summary

    def test_summary_with_multiple_items(self):
        order = Order(id="ORD-00001", customer_id="C001")
        order.items.append(OrderItem(product_id="P001", product_name="Widget", quantity=2, unit_price=10.0))
        order.items.append(OrderItem(product_id="P002", product_name="Gadget", quantity=1, unit_price=25.0))
        summary = format_order_summary(order)
        assert "Order ID: ORD-00001\nStatus:   PENDING\nItems:    3\nSubtotal: $45.00\nTotal:    $45.00" in summary
        assert "Order ID: ORD-00001\nStatus:   PENDING\nItems:    3\nSubtotal: $45.00\nTotal:    $45.00" in summary


class TestFormatCustomerInfo:
    """Tests for customer info formatting."""

    def test_customer_info_contains_name(self):
        customer = Customer(id="C001", name="Alice Smith", email="alice@example.com")
        info = format_customer_info(customer)
        assert "Alice Smith" in info

    def test_customer_info_contains_email(self):
        customer = Customer(id="C001", name="Alice Smith", email="alice@example.com")
        info = format_customer_info(customer)
        assert "alice@example.com" in info

    def test_customer_info_contains_tier(self):
        customer = Customer(id="C001", name="Alice Smith", email="alice@example.com", tier=CustomerTier.GOLD)
        info = format_customer_info(customer)
        assert "GOLD" in info

    def test_customer_info_contains_total_spent(self):
        customer = Customer(id="C001", name="Alice Smith", email="alice@example.com", total_spent=1000.0)
        info = format_customer_info(customer)
        assert "$1,000.00" in info


class TestFormatItemList:
    """Tests for item list formatting."""

    def test_format_empty_item_list(self):
        items = []
        result = format_item_list(items)
        assert result == "  (no items)"

    def test_format_single_item(self):
        items = [OrderItem(product_id="P001", product_name="Widget", quantity=2, unit_price=10.0)]
        result = format_item_list(items)
        assert "Widget x2 @ $10.00 = $20.00" in result

    def test_format_multiple_items(self):
        items = [
            OrderItem(product_id="P001", product_name="Widget", quantity=2, unit_price=10.0),
            OrderItem(product_id="P002", product_name="Gadget", quantity=1, unit_price=25.0),
        ]
        result = format_item_list(items)
        assert "Widget x2 @ $10.00 = $20.00" in result
        assert "Gadget x1 @ $25.00 = $25.00" in result
        assert "\n" in result  # Should have multiple lines

