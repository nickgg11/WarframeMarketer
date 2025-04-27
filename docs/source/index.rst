.. Warframe Market API documentation master file, created by
   sphinx-quickstart on Sat Apr 26 23:42:04 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Warframe Market API's documentation!
=========================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   modules/installation
   modules/getting_started
   modules/api/index
   modules/database/index
   modules/models/index
   modules/utils/index

Overview
--------

Warframe Market API is a Python-based asynchronous client for tracking and analyzing Warframe Market data. It provides tools for market analysis, price tracking, and historical data management.

Quick Start
----------

Installation
~~~~~~~~~~~

.. code-block:: bash

   pip install -r requirements.txt

Basic Usage
~~~~~~~~~~

.. code-block:: python

   from src.main import WarframeMarketApp

   async def main():
       app = WarframeMarketApp()
       await app.initialize()
       await app.fetch_and_store_items()
       await app.process_warframe_orders()

   if __name__ == '__main__':
       asyncio.run(main())

Features
--------

- Asynchronous API client with rate limiting
- PostgreSQL database integration
- Market analysis tools
- Historical order tracking
- Price trend analysis

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

