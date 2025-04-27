"""Update tab for data management"""
import asyncio
import datetime
import threading
import logging
import traceback  # Add for detailed error logging
from datetime import datetime, timezone

# pylint: disable=no-name-in-module
from PyQt6.QtWidgets import (QWidget, QGridLayout, QPushButton, QLabel, 
                            QProgressBar)
from PyQt6.QtCore import pyqtSignal  # Add import for signal

from ..signals import ProgressSignal
from src.api.warframe_market_client import WarframeMarketClient

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UpdateTab(QWidget):
    """Tab for updating data from the Warframe Market API.
    
    Provides UI components to fetch items, update prices, and refresh orders.
    Uses progress bars to show update status.
    """
    # Signal to notify that data update has completed
    update_complete = pyqtSignal()
    
    def __init__(self, parent=None, db_ops=None):
        """Initialize the update tab.
        
        Args:
            parent: Parent widget
            db_ops: Database operations instance
        """
        super().__init__(parent)
        self.db_ops = db_ops
        
        # Create signals for progress updates
        self.fetch_signal = ProgressSignal()
        self.prices_signal = ProgressSignal()
        self.orders_signal = ProgressSignal()
        self.market_data_signal = ProgressSignal()
        
        # Connect progress signals to update methods
        self.fetch_signal.updated.connect(self.update_fetch_progress)
        self.prices_signal.updated.connect(self.update_prices_progress)
        self.orders_signal.updated.connect(self.update_orders_progress)
        self.market_data_signal.updated.connect(self.update_market_data_progress)
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface components."""
        layout = QGridLayout(self)
        
        # Create buttons for different update operations
        fetch_items_btn = QPushButton("Fetch Items")
        fetch_items_btn.clicked.connect(self.fetch_items)
        
        update_market_data_btn = QPushButton("Update Market Data")
        update_market_data_btn.clicked.connect(self.update_market_data)
        
        # Add status label
        self.status_label = QLabel("Ready")
        
        # Add progress bars
        self.fetch_progress = QProgressBar()
        self.market_data_progress = QProgressBar()
        
        # Add widgets to layout
        layout.addWidget(fetch_items_btn, 0, 0)
        layout.addWidget(update_market_data_btn, 0, 1)
        layout.addWidget(self.status_label, 2, 0, 1, 2)
        layout.addWidget(self.fetch_progress, 3, 0, 1, 2)
        layout.addWidget(self.market_data_progress, 4, 0, 1, 2)
        
        # Add stretching space
        layout.setRowStretch(6, 1)
    
    def fetch_items(self):
        """Start the async task to fetch items."""
        self.status_label.setText("Fetching items...")
        self.fetch_progress.setValue(0)
        
        # Use asyncio in a way that doesn't block the UI
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Run the async task in a separate thread to prevent UI blocking
        def run_async_task():
            loop.run_until_complete(self.async_fetch_items())
            loop.close()
            
        # Start the async task in a separate thread
        threading.Thread(target=run_async_task, daemon=True).start()
    
    def update_market_data(self):
        """Start the async task to update both prices and orders."""
        self.status_label.setText("Updating market data (prices and orders)...")
        self.market_data_progress.setValue(0)
        
        # Use asyncio in a way that doesn't block the UI
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Run the async task in a separate thread to prevent UI blocking
        def run_async_task():
            loop.run_until_complete(self.async_update_market_data())
            loop.close()
            
        # Start the async task in a separate thread
        threading.Thread(target=run_async_task, daemon=True).start()
    
    async def async_fetch_items(self):
        """Asynchronously fetch items from the API."""
        # Reset progress bar
        self.fetch_signal.updated.emit(0)
        
        client = WarframeMarketClient()
        await client.create_session()
        try:
            # Set up progress callback
            await client.fetch_items(progress_callback=self.fetch_signal.updated.emit)
            self.fetch_signal.updated.emit(100)  # Ensure we reach 100%
            self.status_label.setText("Items fetched successfully")
        except (ConnectionError, asyncio.TimeoutError) as e:
            self.status_label.setText(f"Error: {str(e)}")
        finally:
            await client.close_session()
    
    async def async_update_market_data(self):
        """Asynchronously update both prices and orders from the API."""
        # Reset progress bar
        self.market_data_signal.updated.emit(0)
        
        client = WarframeMarketClient()
        await client.create_session()
        try:
            # Get item names from database
            items_data = self.db_ops.get_all_items()
            items = [item[1] for item in items_data]  # Use name instead of ID
            if not items:
                self.status_label.setText("No items found in database. Fetch items first.")
                return
            
            # Step 1: Update prices (0-40% of total progress)
            def price_progress_callback(value):
                # Map the 0-100 price progress to 0-40 of total progress
                self.market_data_signal.updated.emit(int(value * 0.4))
                
            self.status_label.setText("Fetching price data...")
            price_data = await client.fetch_prices_batch(items, progress_callback=price_progress_callback)
            
            # Save price data to database (40-50% of total progress)
            self.status_label.setText("Processing price data...")
            price_count = 0
            price_errors = 0
            total_price_items = len(price_data)
            
            for idx, (item_name, data) in enumerate(price_data.items()):
                try:
                    if 'orders' not in data:
                        continue
                        
                    # Find the item ID from our items_data
                    item_id = next((id_val for id_val, name in items_data if name == item_name), None)
                    if not item_id:
                        logger.warning(f"Item ID not found for {item_name}")
                        continue
                        
                    for order in data['orders']:
                        try:
                            last_seen = client.parse_timestamp(order['user'].get('last_seen'))
                            current_time = datetime.now(timezone.utc)
                            
                            if last_seen is None or (current_time - last_seen).days > 30:
                                logger.debug(f"Skipping outdated order: {order}")
                                continue
                                
                            self.db_ops.insert_price(
                                item_id=item_id,
                                price=float(order.get('platinum', 0)),
                                quantity=int(order.get('quantity', 0)),
                                side=order.get('order_type', 'sell'),
                                recorded_at=current_time
                            )
                            price_count += 1
                        except Exception as e:
                            price_errors += 1
                            logger.error(f"Error saving price for {item_name}: {e}\n{traceback.format_exc()}")
                            
                except Exception as outer_e:
                    price_errors += 1
                    logger.error(f"Error processing price data for {item_name}: {outer_e}\n{traceback.format_exc()}")
                    
            self.status_label.setText(f"Prices updated - {price_count} records saved ({price_errors} errors). Fetching order data...")
            
            # Step 2: Update orders (50-90% of total progress)
            def orders_progress_callback(value):
                # Map the 0-100 orders progress to 50-90 of total progress
                self.market_data_signal.updated.emit(50 + int(value * 0.4))
                
            orders_data = await client.fetch_orders_batch(items, progress_callback=orders_progress_callback)
            
            order_count = 0
            order_errors = 0
            total_order_items = len(orders_data)
            
            for idx, (item_name, data) in enumerate(orders_data.items()):
                try:
                    if 'orders' not in data:
                        continue
                        
                    item_id = next((id_val for id_val, name in items_data if name == item_name), None)
                    if not item_id:
                        logger.warning(f"Item ID not found for {item_name}")
                        continue
                        
                    for order in data['orders']:
                        try:
                            last_seen = client.parse_timestamp(order.get('last_seen'))
                            current_time = datetime.now(timezone.utc)
                            
                            if last_seen is None or (current_time - last_seen).days > 30:
                                logger.debug(f"Skipping outdated order: {order}")
                                continue
                                
                            self.db_ops.insert_order(
                                item_id=item_id,
                                order_id=order.get('id'),
                                price=int(order.get('platinum', 0)),
                                quantity=int(order.get('quantity', 0)),
                                side=order.get('order_type', 'sell'),
                                last_seen=last_seen
                            )
                            order_count += 1
                        except Exception as e:
                            order_errors += 1
                            logger.error(f"Error saving order for {item_name}: {e}\n{traceback.format_exc()}")
                            
                except Exception as outer_e:
                    order_errors += 1
                    logger.error(f"Error processing order data for {item_name}: {outer_e}\n{traceback.format_exc()}")
                    
            self.status_label.setText(f"Orders updated - {order_count} records saved ({order_errors} errors).")
            
        except Exception as e:
            logger.error(f"Unhandled exception during market data update: {e}\n{traceback.format_exc()}")
            self.status_label.setText(f"Error: {str(e)}")
            
        finally:
            await client.close_session()
    
    async def async_update_prices(self):
        """Asynchronously update prices from the API."""
        # This method is kept for backward compatibility
        # Reset progress bar
        self.prices_signal.updated.emit(0)
        
        client = WarframeMarketClient()
        await client.create_session()
        try:
            # Get item names from database - use the name (second element) instead of the ID
            items_data = self.db_ops.get_all_items()
            items = [item[1] for item in items_data]  # Changed to use name instead of ID
            if not items:
                self.status_label.setText("No items found in database. Fetch items first.")
                return
                
            # Update prices using batch function
            price_data = await client.fetch_prices_batch(items, progress_callback=self.prices_signal.updated.emit)
            self.prices_signal.updated.emit(100)  # Ensure we reach 100%
            
            # Save the price data to the database
            item_count = 0
            for item_name, data in price_data.items():
                if 'orders' not in data:
                    continue
                    
                # Find the item ID from our items_data
                item_id = None
                for id_val, name in items_data:
                    if name == item_name:
                        item_id = id_val
                        break
                
                if not item_id:
                    continue
                    
                # Save price data to the database
                for order in data['orders']:
                    # Skip orders that aren't active or recent
                    if order.get('user', {}).get('status') != 'ingame' or order.get('order_type') not in ['sell', 'buy']:
                        continue
                        
                    try:
                        # Parse the timestamp
                        timestamp = client.parse_timestamp(order.get('last_update'))
                        if not timestamp:
                            continue
                            
                        # Insert into item_prices table
                        self.db_ops.insert_price(
                            item_id=item_id,
                            price=float(order.get('platinum', 0)),
                            quantity=int(order.get('quantity', 0)),
                            side=order.get('order_type', 'sell'),
                            recorded_at=timestamp
                        )
                        item_count += 1
                    except Exception as e:
                        logging.error(f"Error saving price for {item_name}: {e}")
                        
            self.status_label.setText(f"Prices updated successfully - {item_count} orders saved")
        except (ConnectionError, asyncio.TimeoutError, KeyError) as e:
            self.status_label.setText(f"Error: {str(e)}")
        finally:
            await client.close_session()
    
    async def async_update_orders(self):
        """Asynchronously update orders from the API."""
        # This method is kept for backward compatibility
        # Reset progress bar
        self.orders_signal.updated.emit(0)
        
        client = WarframeMarketClient()
        await client.create_session()
        try:
            # Get item names from database - use the name (second element) instead of the ID
            items_data = self.db_ops.get_all_items()
            items = [item[1] for item in items_data]  # Changed to use name instead of ID
            if not items:
                self.status_label.setText("No items found in database. Fetch items first.")
                return
                
            # Update orders using batch function
            orders_data = await client.fetch_orders_batch(items, progress_callback=self.orders_signal.updated.emit)
            self.orders_signal.updated.emit(100)  # Ensure we reach 100%
            
            # Save the orders data to the database
            order_count = 0
            for item_name, data in orders_data.items():
                if 'orders' not in data:
                    continue
                    
                # Find the item ID from our items_data
                item_id = None
                for id_val, name in items_data:
                    if name == item_name:
                        item_id = id_val
                        break
                
                if not item_id:
                    continue
                    
                # Save orders to the database
                for order in data['orders']:
                    try:
                        # Parse timestamps
                        last_updated = client.parse_timestamp(order.get('last_update'))
                        if not last_updated:
                            continue
                            
                        # Insert into order_history table
                        self.db_ops.insert_order(
                            item_id=item_id,
                            user_id=order.get('user', {}).get('id'),
                            order_id=order.get('id'),
                            price=float(order.get('platinum', 0)),
                            quantity=int(order.get('quantity', 0)),
                            side=order.get('order_type', 'sell'),
                            user_status=order.get('user', {}).get('status'),
                            last_seen=last_updated
                        )
                        order_count += 1
                    except Exception as e:
                        logging.error(f"Error saving order for {item_name}: {e}")
                        
            self.status_label.setText(f"Orders updated successfully - {order_count} orders saved")
        except (ConnectionError, asyncio.TimeoutError, KeyError) as e:
            self.status_label.setText(f"Error: {str(e)}")
        finally:
            await client.close_session()
    
    def update_fetch_progress(self, value):
        """Update the fetch progress bar with the given value."""
        self.fetch_progress.setValue(value)
        self.fetch_progress.repaint()  # Force immediate visual update
    
    def update_prices_progress(self, value):
        """Update the prices progress bar with the given value."""
        # This method is kept for backward compatibility but doesn't update UI
        pass
    
    def update_orders_progress(self, value):
        """Update the orders progress bar with the given value."""
        # This method is kept for backward compatibility but doesn't update UI
        pass
        
    def update_market_data_progress(self, value):
        """Update the market data progress bar with the given value."""
        self.market_data_progress.setValue(value)
        self.market_data_progress.repaint()  # Force immediate visual update