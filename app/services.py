from decimal import Decimal

from app.models import Transaction, BuyOrSell

def calculate_position(transactions: list[Transaction]) -> dict:
    quantity = 0
    total_cost = Decimal("0")
    
    for transaction in transactions:
            
        if transaction.operation == BuyOrSell.BUY:
            quantity += transaction.quantity
            total_cost += transaction.quantity * transaction.unitary_price
            
        elif transaction.operation == BuyOrSell.SELL:
            if quantity == 0: 
                continue
            average_price = total_cost / quantity
            total_cost -= transaction.quantity * average_price
            quantity -= transaction.quantity
    
    if quantity == 0:
        return {"quantity": 0, "average_price": Decimal("0")}
    
    return {
        "quantity": quantity,
        "average_price": total_cost / quantity
        }