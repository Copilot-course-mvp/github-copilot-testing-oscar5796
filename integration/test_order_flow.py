"""Integration tests for the complete order processing flow.

These tests exercise multiple modules together to validate end-to-end behavior.

NOTE FOR STUDENTS: These integration tests cover the happy path.
Use GitHub Copilot to add tests for error conditions, edge cases,
and additional scenarios (e.g., order with multiple products,
discounts applied at various tiers, etc.).
"""
import pytest
from src.models.customer import Customer, CustomerTier
from src.models.product import Product
from src.services.inventory_service import InventoryService
from src.services.pricing_service import PricingService
from src.services.order_service import OrderService
from src.models.order import OrderStatus


@pytest.fixture
def inventory():
    svc = InventoryService()
    svc.add_product(Product(id="P001", name="Widget", price=30.0, stock=50, category="Tools"))
    svc.add_product(Product(id="P002", name="Gadget", price=80.0, stock=10, category="Electronics"))
    svc.add_product(Product(id="P003", name="Doohickey", price=15.0, stock=3, category="Misc"))
    return svc


@pytest.fixture
def pricing():
    return PricingService()


@pytest.fixture
def order_service(inventory, pricing):
    return OrderService(inventory=inventory, pricing=pricing)


@pytest.fixture
def standard_customer():
    return Customer(id="C001", name="Alice", email="alice@example.com")


@pytest.fixture
def gold_customer():
    return Customer(
        id="C002", name="Bob", email="bob@example.com",
        tier=CustomerTier.GOLD, total_spent=6000.0
    )


@pytest.fixture
def silver_customer():
    return Customer(
        id="C004", name="Diana", email="diana@example.com",
        tier=CustomerTier.SILVER, total_spent=1500.0
    )


@pytest.fixture
def platinum_customer():
    return Customer(
        id="C003", name="Charlie", email="charlie@example.com",
        tier=CustomerTier.PLATINUM, total_spent=10000.0
    )


class TestHappyPathOrderFlow:
    """Tests for the standard successful order flow."""

    def test_full_order_lifecycle(self, order_service, standard_customer, inventory):
        """Test creating, filling, confirming, and advancing an order."""
        # Create order
        order = order_service.create_order(standard_customer)
        assert order.status == OrderStatus.PENDING

        # Add items
        order_service.add_item_to_order(order, "P001", 2)
        assert len(order.items) == 1

        # Confirm order
        order_service.confirm_order(order, standard_customer)
        assert order.status == OrderStatus.CONFIRMED

        # Advance through pipeline
        order_service.advance_order(order.id)
        assert order.status == OrderStatus.PROCESSING

        order_service.advance_order(order.id)
        assert order.status == OrderStatus.SHIPPED

        order_service.advance_order(order.id)
        assert order.status == OrderStatus.DELIVERED

    def test_free_shipping_applied_on_large_order(
        self, order_service, standard_customer
    ):
        """Orders with subtotal >= $75 should get free shipping."""
        order = order_service.create_order(standard_customer)
        order_service.add_item_to_order(order, "P002", 1)  # $80 gadget
        order_service.confirm_order(order, standard_customer)
        assert order.shipping_cost == 0.0

    def test_shipping_cost_applied_on_small_order(
        self, order_service, standard_customer
    ):
        """Orders with subtotal < $75 should incur a shipping charge."""
        order = order_service.create_order(standard_customer)
        order_service.add_item_to_order(order, "P001", 1)  # $30 widget
        order_service.confirm_order(order, standard_customer)
        assert order.shipping_cost == pytest.approx(9.99)

    def test_gold_customer_gets_discount(self, order_service, gold_customer):
        """Gold tier customers should receive a 10% discount."""
        order = order_service.create_order(gold_customer)
        order_service.add_item_to_order(order, "P002", 1)  # $80 gadget
        order_service.confirm_order(order, gold_customer)
        # 10% of $80 = $8 discount, no shipping (>= $75)
        assert order.discount_amount == pytest.approx(8.0)
        assert order.total == pytest.approx(72.0)


class TestCancellationFlow:
    """Tests for order cancellation and inventory restoration."""

    def test_cancel_order_restores_inventory(
        self, order_service, standard_customer, inventory
    ):
        """Cancelling an order should restore reserved stock."""
        order = order_service.create_order(standard_customer)
        order_service.add_item_to_order(order, "P003", 2)
        # Stock should be 1 now (3 - 2)
        assert inventory.get_product("P003").stock == 1

        order_service.cancel_order(order.id)
        # Stock should be restored to 3
        assert inventory.get_product("P003").stock == 3
        assert order.status == OrderStatus.CANCELLED

    def test_cancel_after_confirm_restores_inventory(
        self, order_service, standard_customer, inventory
    ):        
        """Cancelling a confirmed order should still restore reserved stock."""
        order = order_service.create_order(standard_customer)
        order_service.add_item_to_order(order, "P003", 2)
        order_service.confirm_order(order, standard_customer)
        # Stock should be 1 now (3 - 2)
        assert inventory.get_product("P003").stock == 1

        order_service.cancel_order(order.id)
        # Stock should be restored to 3
        assert inventory.get_product("P003").stock == 3
        assert order.status == OrderStatus.CANCELLED        

    def test_cancel_shipped_order_raises_error(
        self, order_service, standard_customer
    ):
        """Attempting to cancel a shipped order should raise an error."""
        order = order_service.create_order(standard_customer)
        order_service.add_item_to_order(order, "P001", 1)
        order_service.confirm_order(order, standard_customer)
        order_service.advance_order(order.id)  # Processing
        order_service.advance_order(order.id)  # Shipped

        with pytest.raises(ValueError):
            order_service.cancel_order(order.id)    

    def test_multiple_orders_affect_stock_correctly(
        self, order_service, standard_customer, inventory
    ):
        """Placing multiple orders should correctly update stock levels."""
        # First order for 2 units of P001
        order1 = order_service.create_order(standard_customer)
        order_service.add_item_to_order(order1, "P001", 2)
        order_service.confirm_order(order1, standard_customer)

        # Stock should be 48 now (50 - 2)
        assert inventory.get_product("P001").stock == 48

        # Second order for 3 units of P001
        order2 = order_service.create_order(standard_customer)
        order_service.add_item_to_order(order2, "P001", 3)
        order_service.confirm_order(order2, standard_customer)

        # Stock should be 45 now (48 - 3)
        assert inventory.get_product("P001").stock == 45


class TestEdgeCases:
    """Edge case integration tests."""

    def test_order_with_multiple_products(
        self, order_service, standard_customer, inventory
    ):
        """Order with multiple different products should sum correctly."""
        order = order_service.create_order(standard_customer)
        order_service.add_item_to_order(order, "P001", 1)  # $30
        order_service.add_item_to_order(order, "P002", 1)  # $80
        assert order.subtotal == pytest.approx(110.0)

    def test_exhausting_stock_prevents_further_orders(
        self, order_service, standard_customer
    ):
        """After exhausting stock, further orders for that product should fail."""
        order1 = order_service.create_order(standard_customer)
        order_service.add_item_to_order(order1, "P003", 3)  # Uses all 3 in stock

        order2 = order_service.create_order(standard_customer)
        with pytest.raises(ValueError):
            order_service.add_item_to_order(order2, "P003", 1)

    @pytest.mark.parametrize("customer_fixture,tier_percent,coupon_code,coupon_percent,expected_discount_percent", [
        ("gold_customer", 10, "SAVE20", 20, 20),  # Coupon wins (larger)
        ("platinum_customer", 15, "SAVE10", 10, 15),  # Tier wins (larger)
        ("gold_customer", 10, "SAVE10", 10, 10),  # Ties at 10%
        ("silver_customer", 5, "HALFOFF", 50, 50),  # Coupon wins (extreme)
        ("standard_customer", 0, "SAVE10", 10, 10),  # Coupon wins (only option)
        ("gold_customer", 10, "INVALID", 0, 10),  # Tier wins (invalid coupon)
    ])
    def test_coupon_and_tier_discount_combination(
        self, order_service, request, customer_fixture, tier_percent, coupon_code, coupon_percent, expected_discount_percent
    ):
        """Test that the best discount (tier or coupon) is applied to orders."""
        # Get the customer fixture dynamically
        customer = request.getfixturevalue(customer_fixture)
        
        # Create order and add items for a realistic subtotal (~$160)
        order = order_service.create_order(customer)
        order_service.add_item_to_order(order, "P002", 2)  # 2x $80 = $160
        
        # Confirm order with coupon
        order_service.confirm_order(order, customer, coupon_code)
        
        # Calculate expected discount
        expected_discount = 160.0 * expected_discount_percent / 100
        
        # Verify discount amount
        assert order.discount_amount == pytest.approx(expected_discount)
        
        # Verify total (subtotal - discount + shipping, free shipping >= $75)
        expected_total = 160.0 - expected_discount + 0.0  # Free shipping
        assert order.total == pytest.approx(expected_total)
        
        # Verify coupon code is stored
        assert order.coupon_code == coupon_code

    def test_listing_orders_by_customer(self, order_service, standard_customer):
        """Test that we can retrieve all orders for a given customer."""
        # Create multiple orders for the same customer
        order1 = order_service.create_order(standard_customer)
        order_service.add_item_to_order(order1, "P001", 1)
        order_service.confirm_order(order1, standard_customer)

        order2 = order_service.create_order(standard_customer)
        order_service.add_item_to_order(order2, "P002", 1)
        order_service.confirm_order(order2, standard_customer)

        # Retrieve orders by customer ID
        orders = order_service.list_orders_by_customer(standard_customer.id)
        assert len(orders) == 2
        assert all(order.customer_id == standard_customer.id for order in orders)

    def test_listing_orders_by_status(self, order_service, standard_customer):
        """Test that we can retrieve all orders with a given status."""
        # Create orders with different statuses
        order1 = order_service.create_order(standard_customer)
        order_service.add_item_to_order(order1, "P001", 1)
        order_service.confirm_order(order1, standard_customer)  # Confirmed

        order2 = order_service.create_order(standard_customer)
        order_service.add_item_to_order(order2, "P002", 1)
        # Still pending

        order3 = order_service.create_order(standard_customer)
        order_service.add_item_to_order(order3, "P001", 2)
        order_service.confirm_order(order3, standard_customer)
        order_service.advance_order(order3.id)  # Processing

        # Retrieve orders by status
        confirmed_orders = order_service.list_orders_by_status(OrderStatus.CONFIRMED)
        processing_orders = order_service.list_orders_by_status(OrderStatus.PROCESSING)

        assert len(confirmed_orders) == 1
        assert confirmed_orders[0].id == order1.id

        assert len(processing_orders) == 1
        assert processing_orders[0].id == order3.id
