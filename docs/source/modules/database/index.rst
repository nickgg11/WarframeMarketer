Database Reference
=================

This section covers the database operations and configuration for the Warframe Market API client.

.. toctree::
   :maxdepth: 2

   operations
   config

Database Operations
-----------------

.. automodule:: src.database.operations
   :members:
   :undoc-members:
   :show-inheritance:

Schema Overview
-------------

known_warframes
~~~~~~~~~~~~~

Stores information about known warframe sets:

.. code-block:: sql

    CREATE TABLE known_warframes (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) UNIQUE NOT NULL
    );

order_history
~~~~~~~~~~~

Tracks the history of orders:

.. code-block:: sql

    CREATE TABLE order_history (
        id SERIAL PRIMARY KEY,
        item_id INTEGER REFERENCES known_warframes(id),
        user_id VARCHAR(100),
        order_id VARCHAR(100) UNIQUE,
        initial_price INTEGER,
        final_price INTEGER,
        quantity INTEGER,
        side market_side,
        first_seen TIMESTAMP WITH TIME ZONE,
        last_seen TIMESTAMP WITH TIME ZONE,
        price_changes INTEGER DEFAULT 0,
        visibility_duration INTERVAL,
        listing_type listing_type DEFAULT 'new'
    );

item_prices
~~~~~~~~~

Records price points for market analysis:

.. code-block:: sql

    CREATE TABLE item_prices (
        id SERIAL PRIMARY KEY,
        item_id INTEGER REFERENCES known_warframes(id),
        recorded_at TIMESTAMP WITH TIME ZONE,
        price INTEGER,
        quantity INTEGER,
        side market_side
    );

Custom Types
----------

The database uses several custom ENUM types:

market_side
~~~~~~~~~
.. code-block:: sql

    CREATE TYPE market_side AS ENUM ('buy', 'sell');

order_status
~~~~~~~~~~
.. code-block:: sql

    CREATE TYPE order_status AS ENUM ('active', 'fulfilled', 'dead');

listing_type
~~~~~~~~~~
.. code-block:: sql

    CREATE TYPE listing_type AS ENUM ('new', 'relist');

Configuration
-----------

Database connection settings are configured in ``src/database/config.py``:

.. code-block:: python

    def connect():
        return psycopg2.connect(
            dbname="warframe_market",
            user="your_username",
            password="your_password",
            host="localhost",
            port="5432"
        )

Common Operations
--------------

Creating Tables
~~~~~~~~~~~~

.. code-block:: python

    from src.database.operations import DatabaseOperations

    db = DatabaseOperations()
    db.create_tables()

Inserting Data
~~~~~~~~~~~~

.. code-block:: python

    # Insert a warframe
    db.insert_warframe("volt_prime_set")

    # Update order status
    db.update_order_status()

Maintenance
---------

The database includes maintenance operations:

.. code-block:: python

    # Purge old data (older than 12 months by default)
    db.purge_old_data(months=12)

    # Test database connection
    if db.test_database():
        print("Database connection successful!")

See Also
--------

- :doc:`../getting_started/index`
- :doc:`../models/index`