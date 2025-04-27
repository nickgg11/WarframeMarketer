"""
Order collection model for grouping and managing market orders.
Provides functionality to aggregate and organize orders by type and price.
"""

from typing import Dict, List
from collections import defaultdict
from dataclasses import dataclass

@dataclass
class OrderEntry:
    """Basic representation of a market order.
    
    This is a duplicate of the class in data_models.py and could be
    consolidated in a future refactoring.
    """
    price: int
    quantity: int
    order_type: str

class OrderCollection:
    """Collection class for organizing and aggregating market orders.
    
    Manages collections of buy and sell orders, tracking quantity at each price point.
    """
    def __init__(self):
        self.orders: Dict[str, Dict[int, OrderEntry]] = {
            'buy': defaultdict(lambda: OrderEntry(0, 0, 'buy')),
            'sell': defaultdict(lambda: OrderEntry(0, 0, 'sell'))
        }

    def add_order(self, price: int, quantity: int, order_type: str):
        """Add or update an order in the collection"""
        existing_order = self.orders[order_type][price]
        existing_order.quantity += quantity

    def get_all_orders(self) -> List[OrderEntry]:
        """Get all orders in the collection"""
        all_orders = []
        for order_type, price_map in self.orders.items():
            for price, entry in price_map.items():
                if entry.quantity > 0:
                    all_orders.append(OrderEntry(price, entry.quantity, order_type))
        return all_orders

    def clear(self):
        """Clear all orders from the collection"""
        self.orders = {
            'buy': defaultdict(lambda: OrderEntry(0, 0, 'buy')),
            'sell': defaultdict(lambda: OrderEntry(0, 0, 'sell'))
        }
