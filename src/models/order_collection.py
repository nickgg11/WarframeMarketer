from typing import Dict, List
from collections import defaultdict
from dataclasses import dataclass

@dataclass
class OrderEntry:
    price: int
    quantity: int
    order_type: str

class OrderCollection:
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
        for order_type in self.orders:
            for price, entry in self.orders[order_type].items():
                if entry.quantity > 0:
                    all_orders.append(OrderEntry(price, entry.quantity, order_type))
        return all_orders

    def clear(self):
        """Clear all orders from the collection"""
        self.orders = {
            'buy': defaultdict(lambda: OrderEntry(0, 0, 'buy')),
            'sell': defaultdict(lambda: OrderEntry(0, 0, 'sell'))
        }