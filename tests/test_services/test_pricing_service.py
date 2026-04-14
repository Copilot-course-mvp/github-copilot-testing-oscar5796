"""Unit tests for PricingService."""
import pytest
from src.models.customer import Customer, CustomerTier
from src.services.pricing_service import PricingService


@pytest.fixture
def pricing():
    return PricingService()


@pytest.fixture
def standard_customer():
    return Customer(id="C001", name="Alice", email="alice@example.com")


@pytest.fixture
def gold_customer():
    return Customer(
        id="C002", name="Bob", email="bob@example.com", tier=CustomerTier.GOLD
    )


class TestShippingCalculation:
    """Tests for shipping cost logic."""

    def test_free_shipping_above_threshold(self, pricing):
        assert pricing.calculate_shipping(75.0) == 0.0

    def test_free_shipping_above_threshold_large(self, pricing):
        assert pricing.calculate_shipping(200.0) == 0.0

    def test_shipping_cost_below_threshold(self, pricing):
        assert pricing.calculate_shipping(50.0) == pytest.approx(9.99)

    def test_shipping_cost_at_zero(self, pricing):
        assert pricing.calculate_shipping(0.0) == pytest.approx(9.99)

    def test_shipping_cost_negative_subtotal_raises_error(self, pricing):
        with pytest.raises(ValueError, match="Order subtotal cannot be negative"):
            pricing.calculate_shipping(-10.0)


class TestCustomerDiscount:
    """Tests for customer tier discount calculation."""

    def test_no_discount_for_standard_customer(self, pricing, standard_customer):
        discount = pricing.calculate_customer_discount(100.0, standard_customer)
        assert discount == 0.0

    def test_gold_customer_gets_ten_percent(self, pricing, gold_customer):
        discount = pricing.calculate_customer_discount(100.0, gold_customer)
        assert discount == 10.0

    def test_platinum_customer_gets_fifteen_percent(self, pricing):
        platinum_customer = Customer(
            id="C003", name="Charlie", email="charlie@example.com", tier=CustomerTier.PLATINUM
        )
        discount = pricing.calculate_customer_discount(100.0, platinum_customer)
        assert discount == 15.0

    def test_silver_customer_gets_five_percent(self, pricing):
        silver_customer = Customer(
            id="C004", name="Diana", email="diana@example.com", tier=CustomerTier.SILVER
        )
        discount = pricing.calculate_customer_discount(100.0, silver_customer)
        assert discount == 5.0



class TestCouponCode:
    """Tests for coupon code application."""

    def test_valid_coupon_save10(self, pricing):
        assert pricing.apply_coupon(100.0, "SAVE10") == 10.0

    def test_valid_coupon_halfoff(self, pricing):
        assert pricing.apply_coupon(200.0, "HALFOFF") == 100.0

    def test_invalid_coupon_returns_zero(self, pricing):
        assert pricing.apply_coupon(100.0, "BADCODE") == 0.0

    def test_coupon_is_case_insensitive(self, pricing):
        assert pricing.apply_coupon(100.0, "save10") == 10.0

    def test_welcome_coupon(self, pricing):
        assert pricing.apply_coupon(100.0, "WELCOME") == 5.0

    def test_save20_coupon(self, pricing):
        assert pricing.apply_coupon(100.0, "SAVE20") == 20.0


class TestBulkDiscount:
    """Tests for bulk purchase discounts."""

    def test_no_bulk_discount_below_threshold(self, pricing):
        assert pricing.calculate_bulk_discount(100.0, 4) == 0.0

    def test_bulk_discount_above_threshold(self, pricing):
        assert pricing.calculate_bulk_discount(100.0, 10) == 10.0

    def test_bulk_discount_with_negative_item_count_raises_error(self, pricing):
        with pytest.raises(ValueError, match="Item count cannot be negative"):
            pricing.calculate_bulk_discount(100.0, -1)

    def test_customer_discount_with_negative_subtotal_raises_error(self, pricing, standard_customer):
        with pytest.raises(ValueError, match="Subtotal cannot be negative"):
            pricing.calculate_customer_discount(-100.0, standard_customer)

    def test_bulk_discount_above_threshold(self, pricing):
        assert pricing.calculate_bulk_discount(100.0, 10) == 10.0
