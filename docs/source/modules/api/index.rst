API Reference
============

This section covers the API client implementation for interacting with the Warframe Market API.

.. toctree::
   :maxdepth: 2

   warframe_market_client

Core Components
--------------

WarframeMarketClient
~~~~~~~~~~~~~~~~~~~

The main API client class that handles all interactions with the Warframe Market API.

.. autoclass:: src.api.warframe_market_client.WarframeMarketClient
   :members:
   :undoc-members:
   :show-inheritance:

RateLimiter
~~~~~~~~~~~

A utility class that implements rate limiting for API requests.

.. autoclass:: src.api.warframe_market_client.RateLimiter
   :members:
   :undoc-members:
   :show-inheritance:

API Endpoints
------------

The client supports the following Warframe Market API endpoints:

* ``/items`` - Get all available items
* ``/items/{item_name}`` - Get details for a specific item
* ``/items/{item_name}/orders`` - Get orders for a specific item

Error Handling
-------------

The API client implements automatic error handling and retries:

* Rate limit handling with configurable delay
* Automatic retries for failed requests
* Connection error handling
* JSON parsing error handling

Configuration
------------

The API client can be configured through the following parameters:

* ``calls_per_second`` - Rate limit (default: 2.0)
* ``max_retries`` - Maximum retry attempts (default: 3)
* ``retry_delay`` - Delay between retries in seconds (default: 1.0)

Example Usage
------------

.. code-block:: python

    from src.api.warframe_market_client import WarframeMarketClient

    async def fetch_data():
        client = WarframeMarketClient()
        await client.create_session()
        
        try:
            # Fetch all items
            items = await client.fetch_items()
            
            # Fetch specific item details
            item_details = await client.fetch_item_details("volt_prime_set")
            
            # Fetch orders for an item
            orders = await client.fetch_orders("volt_prime_set")
            
        finally:
            await client.close_session()

See Also
--------

- :doc:`../models/index`
- :doc:`../database/index`