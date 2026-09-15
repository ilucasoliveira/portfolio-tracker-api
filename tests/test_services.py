from decimal import Decimal
from types import SimpleNamespace

from app.models import BuyOrSell
from app.services import calculate_position

def test_calculate_position():
    fake_transaction = [
        SimpleNamespace(operation=BuyOrSell.BUY, quantity=10, unitary_price=Decimal("30.00")),
        SimpleNamespace(operation=BuyOrSell.BUY, quantity=5, unitary_price=Decimal("40.00"))
        ]
    assert calculate_position(fake_transaction) == {"quantity": 15, "average_price": Decimal("500") / 15}

def test_sell_does_not_change_average_price():
    fake_transaction = [
        SimpleNamespace(operation=BuyOrSell.BUY, quantity=10, unitary_price=Decimal("30.00")),
        SimpleNamespace(operation=BuyOrSell.BUY, quantity=5, unitary_price=Decimal("40.00")),
        SimpleNamespace(operation=BuyOrSell.SELL, quantity=3, unitary_price=Decimal("38.00"))
        ]
    assert calculate_position(fake_transaction) == {"quantity": 12, "average_price": Decimal("500") / 15}

def test_selling_everything_returns_zero():
    fake_transaction = [
            SimpleNamespace(operation=BuyOrSell.BUY, quantity=10, unitary_price=Decimal("30.00")),
            SimpleNamespace(operation=BuyOrSell.SELL, quantity=10, unitary_price=Decimal("50.00"))
        ]
    assert calculate_position(fake_transaction) == {"quantity": 0, "average_price": Decimal("0")}

def test_empty_list_returns_zero():
    fake_transaction = []
    assert calculate_position(fake_transaction) == {"quantity": 0, "average_price": Decimal("0")}

def test_sell_without_position_is_ignored():
    fake_transaction = [
            SimpleNamespace(operation=BuyOrSell.SELL, quantity=10, unitary_price=Decimal("40.00")),
        ]
    assert calculate_position(fake_transaction) == {"quantity": 0, "average_price": Decimal("0")}