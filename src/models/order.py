"""Order model for the e-commerce system."""
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum
from datetime import datetime


class OrderStatus(Enum):
    """Possible statuses for an order."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


@dataclass
class OrderItem:
    """Represents a single item within an order."""

    product_id: str
    product_name: str
    quantity: int
    unit_price: float

    def __post_init__(self):
        if self.quantity <= 0:
            raise ValueError(f"Quantity must be positive: {self.quantity}")
        if self.unit_price < 0:
            raise ValueError(f"Unit price cannot be negative: {self.unit_price}")

    @property
    def subtotal(self) -> float:
        """Return the total price for this line item."""
        return self.unit_price * self.quantity


@dataclass
class Order:
    """Represents a customer order."""

    id: str
    customer_id: str
    items: List[OrderItem] = field(default_factory=list)
    status: OrderStatus = OrderStatus.PENDING
    discount_amount: float = 0.0
    shipping_cost: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)
    notes: Optional[str] = None
    coupon_code: Optional[str] = None

    @property
    def subtotal(self) -> float:
        """Return the sum of all item subtotals."""
        return sum(item.subtotal for item in self.items)

    @property
    def total(self) -> float:
        """Return the final order total including shipping and discounts."""
        return max(0.0, self.subtotal - self.discount_amount + self.shipping_cost)

    @property
    def item_count(self) -> int:
        """Return the total number of items in the order."""
        return sum(item.quantity for item in self.items)

    def add_item(self, item: OrderItem) -> None:
        """Add an item to the order."""
        if self.status != OrderStatus.PENDING:
            raise ValueError(
                f"Cannot add items to an order with status: {self.status.value}"
            )
        self.items.append(item)

    def cancel(self) -> None:
        """Cancel the order if it hasn't been shipped yet."""
        if self.status in (OrderStatus.SHIPPED, OrderStatus.DELIVERED):
            raise ValueError(
                f"Cannot cancel an order that has been {self.status.value}"
            )
        self.status = OrderStatus.CANCELLED

    def confirm(self) -> None:
        """Confirm a pending order."""
        if self.status != OrderStatus.PENDING:
            raise ValueError(
                f"Cannot confirm an order with status: {self.status.value}"
            )
        if not self.items:
            raise ValueError("Cannot confirm an empty order")
        self.status = OrderStatus.CONFIRMED

    def advance_status(self) -> None:
        """Advance order through processing pipeline."""
        transitions = {
            OrderStatus.CONFIRMED: OrderStatus.PROCESSING,
            OrderStatus.PROCESSING: OrderStatus.SHIPPED,
            OrderStatus.SHIPPED: OrderStatus.DELIVERED,
        }
        if self.status not in transitions:
            raise ValueError(
                f"Cannot advance order with status: {self.status.value}"
            )
        self.status = transitions[self.status]

    def __repr__(self) -> str:
        return f"Order(id={self.id!r}, status={self.status.value}, total={self.total:.2f})"
