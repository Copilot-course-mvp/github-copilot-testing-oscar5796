"""Order processing service."""
from typing import Dict, List, Optional
from ..models.order import Order, OrderItem, OrderStatus
from ..models.customer import Customer
from ..models.product import Product
from .inventory_service import InventoryService
from .pricing_service import PricingService


class OrderService:
    """Handles order creation, management, and fulfilment."""

    def __init__(
        self,
        inventory: InventoryService,
        pricing: PricingService,
    ):
        self._inventory = inventory
        self._pricing = pricing
        self._orders: Dict[str, Order] = {}
        self._order_counter: int = 0

    def _generate_order_id(self) -> str:
        self._order_counter += 1
        return f"ORD-{self._order_counter:05d}"

    def create_order(self, customer: Customer) -> Order:
        """Create a new empty order for a customer."""
        order_id = self._generate_order_id()
        order = Order(id=order_id, customer_id=customer.id)
        self._orders[order_id] = order
        return order

    def add_item_to_order(
        self, order: Order, product_id: str, quantity: int
    ) -> None:
        """Add a product to the order and reserve inventory."""
        product = self._inventory.get_product_or_raise(product_id)
        if not product.is_available:
            raise ValueError(f"Product {product_id!r} is out of stock")
        if quantity > product.stock:
            raise ValueError(
                f"Requested quantity {quantity} exceeds available stock {product.stock}"
            )
        self._inventory.reserve_stock(product_id, quantity)
        item = OrderItem(
            product_id=product.id,
            product_name=product.name,
            quantity=quantity,
            unit_price=product.discounted_price,
        )
        order.add_item(item)

    def confirm_order(self, order: Order, customer: Customer, coupon_code: Optional[str] = None) -> None:
        """Apply pricing and confirm the order."""
        self._pricing.price_order(order, customer, coupon_code)
        order.confirm()
        order.coupon_code = coupon_code

    def get_order(self, order_id: str) -> Optional[Order]:
        """Retrieve an order by ID."""
        return self._orders.get(order_id)

    def get_order_or_raise(self, order_id: str) -> Order:
        """Retrieve an order by ID, raising an error if not found."""
        order = self.get_order(order_id)
        if order is None:
            raise KeyError(f"Order not found: {order_id!r}")
        return order

    def cancel_order(self, order_id: str) -> None:
        """Cancel an order and return items to inventory."""
        order = self.get_order_or_raise(order_id)
        order.cancel()
        for item in order.items:
            self._inventory.restock_product(item.product_id, item.quantity)

    def advance_order(self, order_id: str) -> None:
        """Advance order to the next status in the pipeline."""
        order = self.get_order_or_raise(order_id)
        order.advance_status()

    def list_orders_by_customer(self, customer_id: str) -> List[Order]:
        """Return all orders for a given customer."""
        return [o for o in self._orders.values() if o.customer_id == customer_id]

    def list_orders_by_status(self, status: OrderStatus) -> List[Order]:
        """Return all orders with a given status."""
        return [o for o in self._orders.values() if o.status == status]
