Getting Started
===============

This guide will help you get started with using the Warframe Market API client.

Basic Usage
----------

The main application class is ``WarframeMarketApp``, which provides all core functionality:

.. code-block:: python

    from src.main import WarframeMarketApp
    import asyncio

    async def main():
        # Initialize the application
        app = WarframeMarketApp()
        await app.initialize()
        
        try:
            # Fetch and process warframe data
            await app.fetch_and_store_items()
            await app.identify_warframes()
            await app.process_warframe_orders()
            
            # Update order statuses
            app.update_statuses()
            
        finally:
            # Clean up resources
            await app.cleanup()

    if __name__ == '__main__':
        asyncio.run(main())

Key Features
-----------

1. Warframe Data Collection
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Fetch all items and identify warframe sets
    await app.fetch_and_store_items()
    await app.identify_warframes()

2. Market Order Processing
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Process orders for all known warframes
    await app.process_warframe_orders()

3. Market Analysis
~~~~~~~~~~~~~~~~

.. code-block:: python

    from src.utils.market_analysis import analyze_market_data
    from src.models.data_models import TimeRange

    # Analyze market data for a specific warframe
    analysis = analyze_market_data(warframe_id, TimeRange.MONTH)
    if analysis:
        print(f"Average daily volume: {analysis.avg_daily_volume}")
        print(f"Best buy time: {analysis.best_buy_time}")
        print(f"Best sell time: {analysis.best_sell_time}")

Configuration
------------

Database Settings
~~~~~~~~~~~~~~~

Edit ``src/database/config.py`` to configure your database connection:

.. code-block:: python

    def connect():
        return psycopg2.connect(
            dbname="warframe_market",
            user="your_username",
            password="your_password",
            host="localhost"
        )

API Client Settings
~~~~~~~~~~~~~~~~

The API client is automatically configured with reasonable defaults:

- Rate limiting: 2 requests per second
- Automatic retries: 3 attempts
- Platform: PC
- Response format: JSON

You can customize these in ``src/api/warframe_market_client.py``.

Best Practices
------------

1. Resource Management
~~~~~~~~~~~~~~~~~~~

Always use async context managers or cleanup methods:

.. code-block:: python

    try:
        await app.initialize()
        # Your code here
    finally:
        await app.cleanup()

2. Error Handling
~~~~~~~~~~~~~~

Implement proper error handling:

.. code-block:: python

    try:
        await app.process_warframe_orders()
    except Exception as e:
        logger.error(f"Error processing orders: {e}")
        # Handle the error appropriately

3. Database Operations
~~~~~~~~~~~~~~~~~~~

Use the provided DatabaseOperations class for all database interactions:

.. code-block:: python

    from src.database.operations import DatabaseOperations

    db_ops = DatabaseOperations()
    db_ops.create_tables()  # Create required tables
    warframes = db_ops.get_all_warframes()  # Fetch data

Next Steps
---------

- Review the API documentation in the :doc:`../api/index` section
- Explore market analysis tools in the :doc:`../utils/index` section
- Learn about data models in the :doc:`../models/index` section