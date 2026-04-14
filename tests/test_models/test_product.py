"""Unit tests for the Product model.

NOTE FOR STUDENTS: Several test cases are missing from this file.
Use GitHub Copilot to identify and fill in the gaps.
"""
import pytest
from src.models.product import Product


class TestProductCreation:
    """Tests for product creation and validation."""

    def test_create_valid_product(self):
        product = Product(
            id="P001",
            name="Laptop",
            price=999.99,
            stock=10,
            category="Electronics",
        )
        assert product.id == "P001"
        assert product.name == "Laptop"
        assert product.price == 999.99
        assert product.stock == 10
        assert product.category == "Electronics"

    def test_create_product_with_description(self):
        product = Product(
            id="P002",
            name="Phone",
            price=499.99,
            stock=5,
            category="Electronics",
            description="A great smartphone",
        )
        assert product.description == "A great smartphone"

    def test_negative_price_raises_error(self):
        with pytest.raises(ValueError, match="Price cannot be negative"):
            Product(id="P001", name="Item", price=-1.0, stock=5, category="General")

    def test_negative_stock_raises_error(self):
        with pytest.raises(ValueError, match="Stock cannot be negative"):
            Product(id="P001", name="Item", price=10.0, stock=-1, category="General")

    def test_empty_name_raises_error(self):
        with pytest.raises(ValueError, match="Product name cannot be empty"):
            Product(id="P001", name="", price=10.0, stock=5, category="General")

    def test_discount_percent_over_hundred_raises_error(self):
        with pytest.raises(ValueError, match="Discount percent must be between 0 and 100"):
            Product(id="P001", name="Item", price=10.0, stock=5, category="General", discount_percent=150.0)

    def test_discount_percent_negative_raises_error(self):
        with pytest.raises(ValueError, match="Discount percent must be between 0 and 100"):
            Product(id="P001", name="Item", price=10.0, stock=5, category="General", discount_percent=-10.0)


class TestProductProperties:
    """Tests for product computed properties."""

    def test_discounted_price_with_no_discount(self):
        product = Product(id="P001", name="Item", price=100.0, stock=5, category="X")
        assert product.discounted_price == 100.0

    def test_discounted_price_with_discount(self):
        product = Product(
            id="P001", name="Item", price=100.0, stock=5, category="X",
            discount_percent=20.0
        )
        assert product.discounted_price == 80.0

    def test_is_available_when_in_stock(self):
        product = Product(id="P001", name="Item", price=10.0, stock=3, category="X")
        assert product.is_available is True

    def test_is_available_when_out_of_stock(self):
        product = Product(id="P001", name="Item", price=10.0, stock=0, category="X")
        assert product.is_available is False


class TestProductStockManagement:
    """Tests for stock reduction and restocking."""

    def test_reduce_stock_successfully(self):
        product = Product(id="P001", name="Item", price=10.0, stock=10, category="X")
        product.reduce_stock(3)
        assert product.stock == 7

    def test_reduce_stock_to_zero(self):
        product = Product(id="P001", name="Item", price=10.0, stock=5, category="X")
        product.reduce_stock(5)
        assert product.stock == 0

    def test_reduce_stock_insufficient_raises_error(self):
        product = Product(id="P001", name="Item", price=10.0, stock=3, category="X")
        with pytest.raises(ValueError, match="Insufficient stock"):
            product.reduce_stock(10)

    def test_reduce_stock_zero_quantity_raises_error(self):
        product = Product(id="P001", name="Item", price=10.0, stock=5, category="X")
        with pytest.raises(ValueError, match="Quantity must be positive"):
            product.reduce_stock(0)

    def test_restock_product(self):
        product = Product(id="P001", name="Item", price=10.0, stock=5, category="X")
        product.restock(10)
        assert product.stock == 15

    def test_restock_with_zero_quantity_raises_error(self):
        product = Product(id="P001", name="Item", price=10.0, stock=5, category="X")
        with pytest.raises(ValueError, match="Quantity must be positive"):
            product.restock(0)

    def test_restock_with_negative_quantity_raises_error(self):
        product = Product(id="P001", name="Item", price=10.0, stock=5, category="X")
        with pytest.raises(ValueError, match="Quantity must be positive"):
            product.restock(-1)


class TestProductRepr:
    """Tests for product string representation."""

    def test_repr_basic_product(self):
        product = Product(id="P001", name="Laptop", price=999.99, stock=10, category="Electronics")
        repr_str = repr(product)
        assert "P001" in repr_str
        assert "Laptop" in repr_str
        assert "999.99" in repr_str
        assert "10" in repr_str
        assert repr_str.startswith("Product(")

    def test_repr_product_with_special_characters(self):
        product = Product(id="P002", name="Phone's Case", price=29.99, stock=5, category="Accessories")
        repr_str = repr(product)
        assert "P002" in repr_str
        assert "Phone's Case" in repr_str
        assert "29.99" in repr_str
        assert "5" in repr_str

    def test_repr_product_out_of_stock(self):
        product = Product(id="P003", name="Widget", price=15.0, stock=0, category="General")
        repr_str = repr(product)
        assert "P003" in repr_str
        assert "Widget" in repr_str
        assert "15.0" in repr_str
        assert "stock=0" in repr_str

    def test_repr_product_with_decimal_price(self):
        product = Product(id="P004", name="Item", price=123.45, stock=100, category="Test")
        repr_str = repr(product)
        assert "123.45" in repr_str
        assert "100" in repr_str
