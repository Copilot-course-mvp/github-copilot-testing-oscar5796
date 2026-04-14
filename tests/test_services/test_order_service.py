"""Unit tests for OrderService.

NOTE FOR STUDENTS: This file has significant gaps in test coverage.
Use GitHub Copilot to complete the test suite.
"""
import pytest
from src.models.customer import Customer
from src.models.product import Product
from src.models.order import OrderStatus
from src.services.inventory_service import InventoryService
from src.services.pricing_service import PricingService
from src.services.order_service import OrderService


@pytest.fixture
def inventory():
    svc = InventoryService()
    svc.add_product(Product(id="P001", name="Widget", price=25.0, stock=20, category="Tools"))
    svc.add_product(Product(id="P002", name="Gadget", price=50.0, stock=5, category="Electronics"))
    svc.add_product(Product(id="P003", name="OutOfStock", price=10.0, stock=0, category="Tools"))
    return svc


@pytest.fixture
def pricing():
    return PricingService()


@pytest.fixture
def order_service(inventory, pricing):
    return OrderService(inventory=inventory, pricing=pricing)


@pytest.fixture
def customer():
    return Customer(id="C001", name="Alice", email="alice@example.com")


class TestOrderCreation:
    """Tests for order creation."""

    def test_create_order_returns_order(self, order_service, customer):
        order = order_service.create_order(customer)
        assert order is not None
        assert order.customer_id == customer.id
        assert order.status == OrderStatus.PENDING

    def test_order_ids_are_unique(self, order_service, customer):
        order1 = order_service.create_order(customer)
        order2 = order_service.create_order(customer)
        assert order1.id != order2.id

    def test_create_order_generates_sequential_ids(self, order_service, customer):
        order1 = order_service.create_order(customer)
        order2 = order_service.create_order(customer)
        assert order1.id == "ORD-00001"
        assert order2.id == "ORD-00002"


class TestAddItemToOrder:
    """Tests for adding items to orders."""

    def test_add_item_to_order_updates_stock(self, order_service, customer, inventory):
        order = order_service.create_order(customer)
        order_service.add_item_to_order(order, "P001", 3)
        assert inventory.get_product("P001").stock == 17

    def test_add_item_creates_order_item(self, order_service, customer):
        order = order_service.create_order(customer)
        order_service.add_item_to_order(order, "P001", 2)
        assert len(order.items) == 1
        assert order.items[0].quantity == 2

    def test_add_nonexistent_product_raises_error(self, order_service, customer):
        order = order_service.create_order(customer)
        with pytest.raises(KeyError):
            order_service.add_item_to_order(order, "NOTEXIST", 1)

    def test_add_out_of_stock_product_raises_error(self, order_service, customer):
        order = order_service.create_order(customer)
        with pytest.raises(ValueError, match="Requested quantity 10 exceeds available stock 5"):
            order_service.add_item_to_order(order, "P002", 10)

    def test_add_more_than_available_stock_raises_error(self, order_service, customer):
        order = order_service.create_order(customer)
        with pytest.raises(ValueError, match="Requested quantity 25 exceeds available stock 20"):
            order_service.add_item_to_order(order, "P001", 25)

    def test_add_out_of_stock_product_raises_error(self, order_service, customer):
        order = order_service.create_order(customer)
        with pytest.raises(ValueError, match="Product 'P003' is out of stock"):
            order_service.add_item_to_order(order, "P003", 1)


class TestConfirmAndCancel:
    """Tests for confirming and cancelling orders."""

    def test_confirm_order_changes_status(self, order_service, customer):
        order = order_service.create_order(customer)
        order_service.add_item_to_order(order, "P001", 1)
        order_service.confirm_order(order, customer)
        assert order.status == OrderStatus.CONFIRMED

    def test_cancel_order_restores_stock(self, order_service, customer, inventory):
        order = order_service.create_order(customer)
        order_service.add_item_to_order(order, "P001", 5)
        order_service.cancel_order(order.id)
        # stock should be restored to original 20
        assert inventory.get_product("P001").stock == 20

    def test_cancel_order_changes_status_to_cancelled(self, order_service, customer):
        order = order_service.create_order(customer)
        order_service.add_item_to_order(order, "P001", 1)
        order_service.confirm_order(order, customer)
        assert order.status == OrderStatus.CONFIRMED
        order_service.cancel_order(order.id)
        assert order.status == OrderStatus.CANCELLED

    def test_cancel_nonexistent_order_raises_key_error(self, order_service):
        with pytest.raises(KeyError):
            order_service.cancel_order("ORD-99999")

    def test_advance_order_statuses(self, order_service, customer):
        order = order_service.create_order(customer)
        order_service.add_item_to_order(order, "P001", 1)
        order_service.confirm_order(order, customer)
        assert order.status == OrderStatus.CONFIRMED
        order_service.advance_order(order.id)
        assert order.status == OrderStatus.PROCESSING
        order_service.advance_order(order.id)
        assert order.status == OrderStatus.SHIPPED
        order_service.advance_order(order.id)
        assert order.status == OrderStatus.DELIVERED


class TestOrderListing:
    """Tests for order listing functionality."""

    def test_list_orders_by_customer(self, order_service):
        customer1 = Customer(id="C001", name="Alice", email="alice@example.com")
        customer2 = Customer(id="C002", name="Bob", email="bob@example.com")
        
        order1 = order_service.create_order(customer1)
        order2 = order_service.create_order(customer1)
        order3 = order_service.create_order(customer2)
        
        orders_for_customer1 = order_service.list_orders_by_customer("C001")
        orders_for_customer2 = order_service.list_orders_by_customer("C002")
        
        assert len(orders_for_customer1) == 2
        assert len(orders_for_customer2) == 1
        assert order1 in orders_for_customer1
        assert order2 in orders_for_customer1
        assert order3 in orders_for_customer2

    def test_list_orders_by_status(self, order_service, customer):
        order1 = order_service.create_order(customer)
        order2 = order_service.create_order(customer)
        order3 = order_service.create_order(customer)
        
        order_service.add_item_to_order(order1, "P001", 1)
        order_service.add_item_to_order(order2, "P001", 1)
        order_service.add_item_to_order(order3, "P001", 1)
        
        order_service.confirm_order(order1, customer)
        order_service.confirm_order(order2, customer)
        # order3 remains PENDING
        
        pending_orders = order_service.list_orders_by_status(OrderStatus.PENDING)
        confirmed_orders = order_service.list_orders_by_status(OrderStatus.CONFIRMED)
        
        assert len(pending_orders) == 1
        assert len(confirmed_orders) == 2
        assert order3 in pending_orders
        assert order1 in confirmed_orders
        assert order2 in confirmed_orders
