Installation Guide
==================

Requirements
-----------

Before installing the Warframe Market API client, ensure you have:

1. Python 3.7 or higher
2. PostgreSQL database server
3. pip (Python package manager)

Installation Steps
----------------

1. Clone the Repository
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   git clone https://github.com/yourusername/WarframeMarketApi.git
   cd WarframeMarketApi

2. Install Dependencies
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   pip install -r requirements.txt

3. Configure Database
~~~~~~~~~~~~~~~~~~~

1. Create a PostgreSQL database for the application
2. Copy the example configuration file:

   .. code-block:: bash

      cp src/database/config.example.py src/database/config.py

3. Edit ``src/database/config.py`` with your database credentials:

   .. code-block:: python

      def connect():
          return psycopg2.connect(
              dbname="your_database_name",
              user="your_username",
              password="your_password",
              host="localhost",
              port="5432"
          )

Verification
-----------

To verify the installation:

1. Run the database test:

   .. code-block:: python

      from src.database.operations import DatabaseOperations
      
      db = DatabaseOperations()
      if db.test_database():
          print("Database connection successful!")

2. Run the main application:

   .. code-block:: bash

      python src/main.py

   If no errors occur, the installation was successful.