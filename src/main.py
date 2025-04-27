"""
Warframe Market API Application Module
--------------------------------------
Main application module for the Warframe Market API client.
Handles fetching, processing, and analyzing warframe market data.
"""

import asyncio
import logging
from typing import Dict, List
from datetime import datetime, timezone

import aiohttp
import psycopg2

from api.warframe_market_client import WarframeMarketClient
from database.operations import DatabaseOperations
from database.config import connect

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WarframeMarketApp:
    """Main application class for Warframe Market data processing.
    
    Handles the complete workflow of fetching items from the Warframe Market API,
    identifying warframe sets, processing orders, and maintaining database records.
    """
    def __init__(self):
        self.api_client = WarframeMarketClient()
        self.db_ops = DatabaseOperations()
        self.set_items: List[str] = []

async def main():
    """Main application function that runs the complete data processing workflow."""
    app = WarframeMarketApp()
    try:
        await app.initialize()
        # Step 1: Fetch all items and identify sets
        logger.info("Fetching all items...")
        await app.fetch_and_store_items()
        # Step 2: Check which sets are warframes and store them
        logger.info("Identifying and storing warframe sets...")
        await app.identify_warframes()
        # Step 3: Process orders for all known warframes
        logger.info("Processing orders for all warframes...")
        await app.process_warframe_orders()
        # Step 4: Update order statuses
        logger.info("Updating order statuses...")
        app.db_ops.update_order_status()
        logger.info("Data processing complete!")
    except (KeyError, aiohttp.ClientError, psycopg2.Error) as e:
        logger.error("Application error: %s", e)
    finally:
        await app.api_client.close_session()

if __name__ == '__main__':
    from gui import main as gui_main
    gui_main()