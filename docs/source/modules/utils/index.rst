Utilities and Analysis Tools
===========================

This section covers the utility functions and market analysis tools provided by the Warframe Market API client.

.. toctree::
   :maxdepth: 2

   market_analysis

Market Analysis
--------------

.. automodule:: src.utils.market_analysis
   :members:
   :undoc-members:
   :show-inheritance:

Core Analysis Functions
----------------------

analyze_market_data
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    def analyze_market_data(
        item_id: int,
        time_range: TimeRange,
        include_outliers: bool = False
    ) -> Optional[MarketAnalysis]:
        """
        Perform comprehensive market analysis for an item.
        
        Args:
            item_id: ID of the warframe to analyze
            time_range: Time range for the analysis
            include_outliers: Whether to include outlier data points
            
        Returns:
            MarketAnalysis object containing analysis results
        """

detect_outliers
~~~~~~~~~~~~~~

.. code-block:: python

    def detect_outliers(
        prices: List[float],
        threshold: float = 2.0
    ) -> List[bool]:
        """
        Detect outliers in price data using statistical methods.
        
        Args:
            prices: List of price points to analyze
            threshold: Z-score threshold for outlier detection
            
        Returns:
            List of boolean values indicating outlier status
        """

detect_rapid_price_changes
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    def detect_rapid_price_changes(
        price_history: List[Tuple[datetime, float]],
        change_threshold: float = 0.1
    ) -> List[datetime]:
        """
        Detect sudden changes in price.
        
        Args:
            price_history: List of (timestamp, price) tuples
            change_threshold: Minimum price change to consider
            
        Returns:
            List of timestamps where rapid changes occurred
        """

Market Analysis Features
----------------------

Price Trend Analysis
~~~~~~~~~~~~~~~~~~

The system analyzes price trends using various methods:

- Moving averages (7-day and 30-day)
- Linear regression for trend direction
- Volatility calculation
- Seasonal pattern detection

Example:

.. code-block:: python

    from src.utils.market_analysis import analyze_market_data
    from src.models.data_models import TimeRange

    analysis = analyze_market_data(item_id, TimeRange.MONTH)
    if analysis:
        for trend in analysis.price_trends:
            print(f"Trend direction: {trend.direction}")
            print(f"Trend strength: {trend.strength}")
            print(f"Duration: {trend.duration}")

Market Spread Analysis
~~~~~~~~~~~~~~~~~~~

Tracks the difference between buy and sell orders:

.. code-block:: python

    # Get market spread trend
    analysis = analyze_market_data(item_id, TimeRange.WEEK)
    if analysis:
        spreads = analysis.market_spread_trend
        print(f"Current spread: {spreads[-1]}")
        print(f"Average spread: {sum(spreads) / len(spreads)}")

Trading Volume Analysis
~~~~~~~~~~~~~~~~~~~~

Analyzes trading activity patterns:

.. code-block:: python

    # Get trading volume metrics
    analysis = analyze_market_data(item_id, TimeRange.MONTH)
    if analysis:
        print(f"Average daily volume: {analysis.avg_daily_volume}")
        print(f"Best time to trade: {analysis.best_buy_time}")

Price Heatmap Generation
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from src.utils.market_analysis import calculate_price_heatmap

    heatmap = calculate_price_heatmap(
        item_id,
        TimeRange.MONTH
    )
    
    # Heatmap shows trading activity by hour/day
    for day, hours in heatmap.items():
        print(f"{day}: {hours}")

Configuration
------------

Analysis parameters can be configured:

.. code-block:: python

    # Configure analysis settings
    ANALYSIS_CONFIG = {
        'outlier_threshold': 2.0,
        'price_change_threshold': 0.1,
        'min_data_points': 10,
        'smoothing_factor': 0.2
    }

See Also
--------

- :doc:`../models/index`
- :doc:`../api/index`