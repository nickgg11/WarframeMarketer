GUI Components
=============

This section documents the graphical user interface components of the Warframe Market API application.

Overview
--------

The GUI is built using PyQt6 and provides an interactive way to access the Warframe Market data and analysis tools.

Key Features:
  * Real-time warframe price tracking
  * Data update management with progress tracking
  * Market trend analysis visualization
  * Three main tabs: Warframes, Update Data, and Trends

Component Structure
------------------

WarframeMarketGUI
~~~~~~~~~~~~~~~~

The main GUI class that sets up the application window and manages the interaction between
the different components of the system.

.. code-block:: python

   class WarframeMarketGUI(QMainWindow):
       def __init__(self):
           # Initializes the GUI with tabs and components

Key methods:
  * ``setup_warframes_tab`` - Sets up the Warframes tab with price information
  * ``setup_update_tab`` - Sets up the Update tab for data management
  * ``setup_trends_tab`` - Sets up the Trends tab for market analysis
  * ``fetch_items`` - Initiates the asynchronous fetching of items
  * ``update_prices`` - Initiates the asynchronous updating of prices
  * ``update_orders`` - Initiates the asynchronous updating of orders
  * ``load_warframe_data`` - Populates the warframes table with data
  * ``load_trend_data`` - Populates the trends table with market analysis

ProgressSignal
~~~~~~~~~~~~

A helper class for thread-safe progress updates in the GUI.

.. code-block:: python

   class ProgressSignal(QObject):
       updated = pyqtSignal(int)

Usage Examples
-------------

Starting the GUI Application
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from src.gui import main
   
   if __name__ == "__main__":
       main()

Alternatively, run directly from the command line:

.. code-block:: bash

   python src/gui.py