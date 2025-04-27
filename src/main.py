import asyncio
import logging
from typing import Dict, List
from datetime import datetime, timezone

from api.warframe_market_client import WarframeMarketClient
from database.operations import DatabaseOperations
from models.data_models import OrderStatus, TimeRange
from models.order_collection import OrderCollection
from utils.market_analysis import (
    analyze_market_data,
    detect_outliers,
    detect_rapid_price_changes,
    calculate_price_heatmap
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WarframeMarketApp:
    def __init__(self):
        self.api_client = WarframeMarketClient()
        self.db_ops = DatabaseOperations()
        self.set_items: List[str] = []

    async def initialize(self):
        """Initialize the application"""
        await self.api_client.create_session()
        self.db_ops.create_tables()

    async def cleanup(self):
        """Cleanup resources"""
        await self.api_client.close_session()

    async def fetch_and_store_items(self):
        """Fetch all items and store warframe sets"""
        try:
            data = await self.api_client.fetch_items()
            self.set_items = [
                item["url_name"]
                for item in data["payload"]["items"]
                if "url_name" in item and "set" in item["url_name"].lower()
            ]
            logger.info(f"Found {len(self.set_items)} set items")
        except Exception as e:
            logger.error(f"Error fetching items: {e}")
            self.set_items = []

    async def process_warframe_item(self, item_name: str):
        """Process a single warframe item"""
        try:
            data = await self.api_client.fetch_item_details(item_name)
            
            if "payload" in data and "item" in data["payload"]:
                items_in_set = data["payload"]["item"]["items_in_set"]
                for item in items_in_set:
                    if "tags" in item and "warframe" in item["tags"]:
                        self.db_ops.insert_warframe(item_name)
                        logger.info(f"Stored warframe: {item_name}")
                        break
        except Exception as e:
            logger.error(f"Error processing warframe {item_name}: {e}")

    async def identify_warframes(self):
        """Identify which sets are warframes"""
        tasks = [self.process_warframe_item(item) for item in self.set_items]
        await asyncio.gather(*tasks)
        self.set_items.clear()

    async def process_warframe_orders(self):
        """Process orders for all known warframes"""
        warframes = self.db_ops.get_all_warframes()
        tasks = [self.process_single_warframe(wf_id, name) for wf_id, name in warframes]
        await asyncio.gather(*tasks)

    async def process_single_warframe(self, wf_id: int, name: str):
        """Process orders for a single warframe"""
        try:
            data = await self.api_client.fetch_orders(name)
            current_time = datetime.now(timezone.utc)
            active_order_ids = set()
            
            for order in data['payload']['orders']:
                last_seen = self.api_client.parse_timestamp(order.get('last_seen'))
                if not last_seen:
                    logger.warning(f"Invalid timestamp for order in {name}")
                    continue
                
                if (current_time - last_seen).days > 30:
                    continue
                    
                # Process the order in database
                self.process_order(wf_id, order)
                active_order_ids.add(order['id'])
                
            # Mark orders as fulfilled if they're no longer visible
            if active_order_ids:
                self.db_ops.update_order_status()
                
        except Exception as e:
            logger.error(f"Error processing orders for {name}: {e}")

    def process_order(self, wf_id: int, order: Dict):
        """Process a single order in the database"""
        try:
            conn = self.db_ops.connect()
            cur = conn.cursor()

            try:
                # Check if order already exists
                cur.execute('''
                    SELECT id, initial_price, price_changes 
                    FROM order_history 
                    WHERE order_id = %s
                ''', (order['id'],))
                
                existing_order = cur.fetchone()
                current_price = int(order['platinum'])
                last_seen = self.api_client.parse_timestamp(order.get('last_seen'))
                
                if existing_order:
                    # Update existing order
                    order_id, initial_price, price_changes = existing_order
                    
                    if current_price != initial_price:
                        price_changes += 1
                    
                    cur.execute('''
                        UPDATE order_history 
                        SET final_price = %s,
                            last_seen = %s,
                            price_changes = %s,
                            visibility_duration = %s - first_seen
                        WHERE id = %s
                    ''', (
                        current_price,
                        last_seen,
                        price_changes,
                        last_seen,
                        order_id
                    ))
                else:
                    # Insert new order
                    cur.execute('''
                        INSERT INTO order_history (
                            item_id, user_id, order_id, initial_price, 
                            final_price, quantity, side, first_seen, 
                            last_seen, listing_type
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s::market_side, %s, %s, 
                                 CASE WHEN %s IN (
                                     SELECT order_id FROM order_history 
                                     WHERE user_id = %s AND item_id = %s
                                 ) THEN 'relist'::listing_type ELSE 'new'::listing_type END
                        )
                    ''', (
                        wf_id,
                        order['user']['id'],
                        order['id'],
                        current_price,
                        current_price,
                        order['quantity'],
                        order['order_type'],
                        last_seen,
                        last_seen,
                        order['id'],
                        order['user']['id'],
                        wf_id
                    ))

                    # Also insert into item_prices for trend analysis
                    cur.execute('''
                        INSERT INTO item_prices (item_id, recorded_at, price, quantity, side)
                        VALUES (%s, %s, %s, %s, %s::market_side)
                        ON CONFLICT (item_id, recorded_at, price, side) 
                        DO UPDATE SET quantity = item_prices.quantity + EXCLUDED.quantity
                    ''', (
                        wf_id,
                        last_seen,
                        current_price,
                        order['quantity'],
                        order['order_type']
                    ))
                
                conn.commit()
                logger.debug(f"Processed order {order['id']} successfully")
                
            except Exception as e:
                conn.rollback()
                logger.error(f"Database error processing order: {e}")
                raise
            finally:
                cur.close()
                conn.close()
                
        except Exception as e:
            logger.error(f"Error processing order: {e}")

    def update_statuses(self):
        """Update order statuses"""
        try:
            self.db_ops.update_order_status()
            logger.info("Updated order statuses")
        except Exception as e:
            logger.error(f"Error updating order statuses: {e}")

async def main():
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
        app.update_statuses()
        
        logger.info("Data processing complete!")
    except Exception as e:
        logger.error(f"Application error: {e}")
    finally:
        await app.cleanup()

if __name__ == '__main__':
    asyncio.run(main())