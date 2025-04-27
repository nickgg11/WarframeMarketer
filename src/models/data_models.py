"""
Data model classes for the Warframe Market API.
Contains Enum classes and dataclasses representing market data and analysis results.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict
from enum import Enum

class TimeRange(Enum):
    """Time range options for market data analysis."""
    WEEK = "1 week"
    MONTH = "1 month"
    THREE_MONTHS = "3 months"
    SIX_MONTHS = "6 months"
    ALL_TIME = "all time"

class OrderStatus(Enum):
    """Status of an order in the market."""
    ACTIVE = "active"
    FULFILLED = "fulfilled"
    DEAD = "dead"

class ListingType(Enum):
    """Type of listing for an order."""
    NEW = "new"
    RELIST = "relist"

@dataclass
class OrderEntry:
    """Basic representation of a market order."""
    price: int
    quantity: int
    order_type: str

@dataclass
class MarketTrend:
    """Snapshot of market trend data at a point in time."""
    avg_price: float
    min_price: float
    max_price: float
    volatility: float
    volume: int
    market_spread: float
    best_buy_price: float
    best_sell_price: float
    timestamp: datetime

@dataclass
class MarketAnalysis:
    """Comprehensive market analysis results."""
    # pylint: disable=too-many-instance-attributes
    price_trends: List[MarketTrend]
    avg_daily_volume: float
    price_volatility: float
    market_spread_trend: List[float]
    best_buy_time: str
    best_sell_time: str
    demand_strength: float
    seasonal_patterns: Dict[str, float]

@dataclass
class OrderMetrics:
    """Metrics and statistical analysis for a specific order."""
    # pylint: disable=too-many-instance-attributes
    outlier_score: float
    is_outlier: bool
    moving_avg_7d: float
    moving_avg_30d: float
    price_volatility: float
    listing_type: ListingType