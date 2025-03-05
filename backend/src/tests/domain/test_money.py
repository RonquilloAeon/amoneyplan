from decimal import Decimal

import pytest

from amoneyplan.domain.money import Currency, Money


def test_money_creation():
    """Test creating Money instances with different formats."""
    # Test with different input types
    assert Money(100).amount == Decimal("100.00")
    assert Money("100.50").amount == Decimal("100.50")
    assert Money(100.50).amount == Decimal("100.50")
    assert Money(Decimal("100.50")).amount == Decimal("100.50")

    # Test default currency is USD
    money = Money(100)
    assert money.currency.code == "USD"

    # Test explicit currency
    eur = Money(100, Currency("EUR"))
    assert eur.currency.code == "EUR"


def test_money_parse():
    """Test the parse class method."""
    # Test default USD currency
    usd = Money.parse(100)
    assert usd.amount == Decimal("100.00")
    assert usd.currency.code == "USD"

    # Test explicit currency
    eur = Money.parse(100, Currency("EUR"))
    assert eur.amount == Decimal("100.00")
    assert eur.currency.code == "EUR"


def test_money_operations():
    """Test arithmetic operations with Money."""
    usd1 = Money.parse(100)
    usd2 = Money.parse(50)
    eur = Money.parse(50, Currency("EUR"))

    # Test addition
    assert (usd1 + usd2).amount == Decimal("150.00")
    with pytest.raises(ValueError):
        _ = usd1 + eur

    # Test subtraction
    assert (usd1 - usd2).amount == Decimal("50.00")
    with pytest.raises(ValueError):
        _ = usd1 - eur

    # Test multiplication
    assert (usd1 * 2).amount == Decimal("200.00")

    # Test division
    assert (usd1 / 2).amount == Decimal("50.00")


def test_money_comparison():
    """Test comparison operations with Money."""
    usd1 = Money.parse(100)
    usd2 = Money.parse(50)
    eur = Money.parse(50, Currency("EUR"))

    # Test comparisons
    assert usd1 > usd2
    assert usd2 < usd1
    assert usd1 != usd2
    assert Money.parse(100) == usd1

    # Test cross-currency comparisons raise ValueError
    with pytest.raises(ValueError):
        _ = usd1 > eur
    with pytest.raises(ValueError):
        _ = usd1 < eur


def test_money_string_representation():
    """Test string representation of Money."""
    usd = Money.parse(100.50)
    eur = Money.parse(100.50, Currency("EUR"))

    assert str(usd) == "USD 100.50"
    assert str(eur) == "EUR 100.50"
    assert repr(usd) == "Money('100.50', Currency('USD'))"
    assert repr(eur) == "Money('100.50', Currency('EUR'))"
