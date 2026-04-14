"""Pricing and discount calculation service."""
from typing import Optional
from ..models.customer import Customer, CustomerTier
from ..models.order import Order


class PricingService:
    """Calculates prices, discounts, and shipping costs."""

    BASE_SHIPPING_COST = 9.99
    FREE_SHIPPING_THRESHOLD = 75.0
    BULK_DISCOUNT_THRESHOLD = 5
    BULK_DISCOUNT_PERCENT = 10.0

    def calculate_shipping(self, order_subtotal: float) -> float:
        """Return shipping cost based on order subtotal."""
        if order_subtotal < 0:
            raise ValueError(f"Order subtotal cannot be negative: {order_subtotal}")
        if order_subtotal >= self.FREE_SHIPPING_THRESHOLD:
            return 0.0
        return self.BASE_SHIPPING_COST

    def calculate_customer_discount(
        self, subtotal: float, customer: Customer
    ) -> float:
        """Return discount amount based on customer tier."""
        if subtotal < 0:
            raise ValueError(f"Subtotal cannot be negative: {subtotal}")
        discount_percent = customer.tier_discount_percent
        return round(subtotal * discount_percent / 100, 2)

    def calculate_bulk_discount(self, subtotal: float, item_count: int) -> float:
        """Return discount for bulk purchases (5+ items)."""
        if item_count < 0:
            raise ValueError(f"Item count cannot be negative: {item_count}")
        if item_count >= self.BULK_DISCOUNT_THRESHOLD:
            return round(subtotal * self.BULK_DISCOUNT_PERCENT / 100, 2)
        return 0.0

    def apply_coupon(self, subtotal: float, coupon_code: str) -> float:
        """Return discount amount for a given coupon code."""
        coupons = {
            "SAVE10": 10.0,
            "SAVE20": 20.0,
            "HALFOFF": 50.0,
            "WELCOME": 5.0,
        }
        percent = coupons.get(coupon_code.upper(), 0.0)
        return round(subtotal * percent / 100, 2)

    def calculate_total_discount(
        self,
        subtotal: float,
        customer: Customer,
        item_count: int,
        coupon_code: Optional[str] = None,
    ) -> float:
        """Return the total discount, taking the best applicable discount."""
        customer_discount = self.calculate_customer_discount(subtotal, customer)
        bulk_discount = self.calculate_bulk_discount(subtotal, item_count)
        coupon_discount = (
            self.apply_coupon(subtotal, coupon_code) if coupon_code else 0.0
        )
        # Use the best single discount (not stacked)
        return max(customer_discount, bulk_discount, coupon_discount)

    def price_order(self, order: Order, customer: Customer, coupon_code: Optional[str] = None) -> None:
        """Apply pricing (shipping and discount) to an order in-place."""
        subtotal = order.subtotal
        order.shipping_cost = self.calculate_shipping(subtotal)
        order.discount_amount = self.calculate_total_discount(
            subtotal, customer, order.item_count, coupon_code
        )
