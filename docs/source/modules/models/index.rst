Data Models
===========

This section covers the data models and structures used in the Warframe Market API client.

.. toctree::
   :maxdepth: 2

   data_models
   order_collection

Data Models
----------

.. automodule:: src.models.data_models
   :members:
   :undoc-members:
   :show-inheritance:

MarketAnalysis
~~~~~~~~~~~~

Contains market analysis results:

.. code-block:: python

    @dataclass
    class MarketAnalysis:
        price_trends: List[MarketTrend]
        avg_daily_volume: float
        price_volatility: float
        market_spread_trend: List[float]
        best_buy_time: str
        best_sell_time: str
        demand_strength: float
        seasonal_patterns: Dict[str, float]

OrderMetrics
~~~~~~~~~~

Stores metrics for individual orders:

.. code-block:: python

    @dataclass
    class OrderMetrics:
        outlier_score: float
        is_outlier: bool
        moving_avg_7d: float
        moving_avg_30d: float
        price_volatility: float
        listing_type: ListingType

Order Collection
--------------

.. automodule:: src.models.order_collection
   :members:
   :undoc-members:
   :show-inheritance:

The OrderCollection class provides functionality for:

- Grouping orders by type (buy/sell)
- Calculating price statistics
- Identifying outliers
- Tracking order changes
- Computing price trends

Example Usage
-----------

Creating and Using Models
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from src.models.data_models import MarketAnalysis, TimeRange
    from src.utils.market_analysis import analyze_market_data

    # Analyze market data for a specific item
    analysis = analyze_market_data(item_id, TimeRange.WEEK)
    if analysis:
        print(f"Price volatility: {analysis.price_volatility}")
        print(f"Best time to buy: {analysis.best_buy_time}")
        print(f"Best time to sell: {analysis.best_sell_time}")

Working with Order Collections
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from src.models.order_collection import OrderCollection
    
    # Create a new order collection
    orders = OrderCollection()
    
    # Add orders to the collection
    orders.add_order(order_data)
    
    # Get statistics
    stats = orders.get_statistics()
    print(f"Average price: {stats.average_price}")
    print(f"Price range: {stats.price_range}")

Enums and Constants
----------------

TimeRange
~~~~~~~~

Defines time ranges for analysis:

.. code-block:: python

    class TimeRange(Enum):
        DAY = "day"
        WEEK = "week"
        MONTH = "month"
        YEAR = "year"

ListingType
~~~~~~~~~

Defines types of order listings:

.. code-block:: python

    class ListingType(Enum):
        NEW = "new"
        RELIST = "relist"

See Also
--------

- :doc:`../utils/index`
- :doc:`../api/index`