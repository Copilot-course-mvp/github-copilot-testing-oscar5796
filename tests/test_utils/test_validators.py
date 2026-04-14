"""Unit tests for validator utilities."""
import pytest
from src.utils.validators import (
    validate_email,
    validate_price,
    validate_quantity,
    validate_product_id,
    validate_coupon_code,
    validate_customer_name,
)


class TestEmailValidator:
    """Tests for email validation."""

    def test_valid_email(self):
        assert validate_email("user@example.com") is True

    def test_valid_email_with_subdomain(self):
        assert validate_email("user@mail.example.co.uk") is True

    def test_missing_at_sign(self):
        assert validate_email("userexample.com") is False

    def test_missing_domain(self):
        assert validate_email("user@") is False

    def test_empty_string(self):
        assert validate_email("") is False

    def test_none_email(self):
        assert validate_email(None) is False

    def test_email_with_spaces(self):
        assert validate_email("user @example.com") is False

    def test_email_with_special_characters(self):
        assert validate_email("user+tag@example.com") is True

class TestPriceValidator:
    """Tests for price validation."""

    def test_valid_price_positive(self):
        assert validate_price(9.99) is True

    def test_valid_price_zero(self):
        assert validate_price(0.0) is True

    def test_invalid_price_negative(self):
        assert validate_price(-1.0) is False

    def test_invalid_price_string(self):
        assert validate_price("9.99") is False

    def test_invalid_price_none(self):
        assert validate_price(None) is False



class TestQuantityValidator:
    """Tests for quantity validation."""

    def test_valid_quantity(self):
        assert validate_quantity(5) is True

    def test_invalid_quantity_zero(self):
        assert validate_quantity(0) is False

    def test_invalid_quantity_negative(self):
        assert validate_quantity(-3) is False

    def test_invalid_quantity_float(self):
        assert validate_quantity(2.5) is False

    def test_valid_quantity_large(self):
        assert validate_quantity(1000000) is True


class TestProductIdValidator:
    """Tests for product ID validation."""

    def test_valid_product_id(self):
        assert validate_product_id("P001") is True

    def test_valid_product_id_with_dashes(self):
        assert validate_product_id("PROD-001-XL") is True

    def test_empty_product_id(self):
        assert validate_product_id("") is False

    def test_product_id_starting_with_special_character(self):
        assert validate_product_id("@P001") is False

    def test_product_id_too_long(self):
        long_id = "P" * 51
        assert validate_product_id(long_id) is False


class TestCouponCodeValidator:
    """Tests for coupon code validation."""

    def test_valid_coupon_code(self):
        assert validate_coupon_code("SAVE10") is True

    def test_valid_coupon_code_mixed_case(self):
        assert validate_coupon_code("save10") is True

    def test_coupon_code_too_short(self):
        assert validate_coupon_code("ABC") is False

    def test_coupon_code_too_long(self):
        assert validate_coupon_code("ABCDEFGHIJK") is False

    def test_coupon_code_with_lowercase_letters(self):
        assert validate_coupon_code("save10") is True

    def test_coupon_code_with_numbers(self):
        assert validate_coupon_code("SAVE20") is True

    def test_coupon_code_with_special_characters(self):
        assert validate_coupon_code("SAVE-10") is False

    def test_empty_coupon_code(self):
        assert validate_coupon_code("") is False

    def test_none_coupon_code(self):
        assert validate_coupon_code(None) is False


class TestCustomerNameValidator:
    """Tests for customer name validation."""

    def test_valid_customer_name(self):
        assert validate_customer_name("John Doe") is True

    def test_valid_customer_name_single_name(self):
        assert validate_customer_name("John") is True

    def test_customer_name_too_short(self):
        assert validate_customer_name("A") is False

    def test_customer_name_too_long(self):
        long_name = "A" * 101
        assert validate_customer_name(long_name) is False

    def test_customer_name_with_spaces(self):
        assert validate_customer_name("  John Doe  ") is True

    def test_customer_name_empty_after_strip(self):
        assert validate_customer_name("   ") is False

    def test_customer_name_with_numbers(self):
        assert validate_customer_name("John Doe 123") is True

    def test_customer_name_with_special_characters(self):
        assert validate_customer_name("John-Paul O'Connor") is True

    def test_empty_customer_name(self):
        assert validate_customer_name("") is False

    def test_none_customer_name(self):
        assert validate_customer_name(None) is False
