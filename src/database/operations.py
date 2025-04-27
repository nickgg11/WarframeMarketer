"""
Database operations for the Warframe Market API.
Provides a class for interacting with the database, including table creation,
data insertion, retrieval, and maintenance operations.
"""

from typing import List, Tuple, Dict, Any
from datetime import datetime, timezone, timedelta
import logging

import psycopg2
from src.database.config import connect

logger = logging.getLogger(__name__)

class DatabaseOperations:
    """Database operations handler for Warframe Market API.
    
    Manages all interactions with the PostgreSQL database, including schema creation,
    data insertion, querying, and maintenance operations.
    """
    def create_tables(self):
        """Create all necessary database tables if they don't exist"""
        conn = connect()
        cur = conn.cursor()
        
        try:
            # Create enum types first
            cur.execute('''
                DO $$ BEGIN
                    CREATE TYPE market_side AS ENUM ('buy', 'sell');
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
                
                DO $$ BEGIN
                    CREATE TYPE order_status AS ENUM ('active', 'fulfilled', 'dead');
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
                
                DO $$ BEGIN
                    CREATE TYPE listing_type AS ENUM ('new', 'relist');
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
            ''')

            # Create tables
            cur.execute('''
                CREATE TABLE IF NOT EXISTS known_warframes (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) UNIQUE NOT NULL
                );

                CREATE TABLE IF NOT EXISTS order_history (
                    id SERIAL PRIMARY KEY,
                    item_id INTEGER REFERENCES known_warframes(id),
                    user_id VARCHAR(100) NOT NULL,
                    order_id VARCHAR(100) UNIQUE NOT NULL,
                    initial_price NUMERIC(10,2) NOT NULL,
                    final_price NUMERIC(10,2) NOT NULL,
                    quantity INTEGER NOT NULL,
                    side market_side NOT NULL,
                    first_seen TIMESTAMP WITH TIME ZONE NOT NULL,
                    last_seen TIMESTAMP WITH TIME ZONE NOT NULL,
                    status order_status DEFAULT 'active',
                    visibility_duration INTERVAL,
                    price_changes INTEGER DEFAULT 0,
                    listing_type listing_type DEFAULT 'new',
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    fulfilled_at TIMESTAMP WITH TIME ZONE
                );

                CREATE TABLE IF NOT EXISTS item_prices (
                    id SERIAL PRIMARY KEY,
                    item_id INTEGER REFERENCES known_warframes(id),
                    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
                    price NUMERIC(10,2) NOT NULL,
                    quantity INTEGER NOT NULL,
                    side market_side NOT NULL,
                    UNIQUE(item_id, recorded_at, price, side)
                );

                CREATE TABLE IF NOT EXISTS price_statistics (
                    id SERIAL PRIMARY KEY,
                    item_id INTEGER REFERENCES known_warframes(id),
                    date DATE NOT NULL,
                    hour INTEGER CHECK (hour >= 0 AND hour < 24),
                    avg_price NUMERIC(10,2) NOT NULL,
                    median_price NUMERIC(10,2) NOT NULL,
                    min_price NUMERIC(10,2) NOT NULL,
                    max_price NUMERIC(10,2) NOT NULL,
                    volume INTEGER NOT NULL,
                    num_trades INTEGER NOT NULL,
                    side market_side NOT NULL,
                    moving_avg_7d NUMERIC(10,2),
                    moving_avg_30d NUMERIC(10,2),
                    volatility NUMERIC(10,2),
                    UNIQUE(item_id, date, hour, side)
                );
            ''')
            
            conn.commit()
            logger.info("Database tables created successfully")
            
        except (psycopg2.Error, psycopg2.OperationalError) as e:
            logger.error("Error creating tables: %s", e)
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()

    def insert_warframe(self, name: str) -> None:
        """Insert a warframe into the database"""
        conn = connect()
        cur = conn.cursor()
        
        try:
            cur.execute(
                'INSERT INTO known_warframes (name) VALUES (%s) ON CONFLICT (name) DO NOTHING',
                (name,)
            )
            conn.commit()
        except (psycopg2.Error, psycopg2.IntegrityError) as e:
            logger.error("Error inserting warframe %s: %s", name, e)
            conn.rollback()
        finally:
            cur.close()
            conn.close()

    def get_all_warframes(self) -> List[Tuple[int, str]]:
        """Get all warframes from the database"""
        conn = connect()
        cur = conn.cursor()
        
        try:
            cur.execute('SELECT id, name FROM known_warframes')
            result = cur.fetchall()
            return [(int(id), str(name)) for id, name in result]  # Explicitly cast results
        finally:
            cur.close()
            conn.close()

    def get_all_items(self) -> List[Tuple[int, str]]:
        """Get all items from the database (currently same as get_all_warframes)
        
        Returns:
            List of tuples containing item id and name
        """
        return self.get_all_warframes()

    def update_order_status(self) -> None:
        """Update status of orders that are old"""
        conn = connect()
        cur = conn.cursor()
        
        try:
            month_ago = datetime.now(timezone.utc) - timedelta(days=30)
            cur.execute('''
                UPDATE order_history 
                SET status = 'dead'::order_status
                WHERE last_seen < %s 
                AND status = 'active'::order_status
            ''', (month_ago,))
            conn.commit()
        except (psycopg2.Error, psycopg2.OperationalError) as e:
            logger.error("Error updating order statuses: %s", e)
            conn.rollback()
        finally:
            cur.close()
            conn.close()

    def purge_old_data(self, months: int = 12) -> None:
        """Purge data older than specified number of months"""
        conn = connect()
        cur = conn.cursor()
        
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=months * 30)
            
            # Delete old fulfilled orders first (due to foreign key constraints)
            cur.execute('DELETE FROM order_history WHERE fulfilled_at < %s', (cutoff_date,))
            
            # Delete old price statistics
            cur.execute('DELETE FROM price_statistics WHERE date < %s::date', (cutoff_date,))

            # Delete old item prices
            cur.execute('DELETE FROM item_prices WHERE recorded_at < %s', (cutoff_date,))
            
            conn.commit()
            logger.info("Purged data older than %s months", months)
            
        except (psycopg2.Error, psycopg2.OperationalError) as e:
            logger.error("Error purging old data: %s", e)
            conn.rollback()
        finally:
            cur.close()
            conn.close()

    def test_database(self) -> bool:
        """Test database connection and basic operations"""
        conn = connect()
        cur = conn.cursor()
        
        try:
            # Test known_warframes table
            cur.execute('INSERT INTO known_warframes (name) VALUES (%s)', ('test_warframe',))
            
            # Test order_history table
            cur.execute('''
                INSERT INTO order_history (
                    item_id, user_id, order_id, initial_price, 
                    final_price, quantity, side, first_seen, 
                    last_seen, listing_type
                ) VALUES (
                    (SELECT id FROM known_warframes WHERE name = 'test_warframe'),
                    'test_user', 'test_order', 100, 100, 1, 
                    'sell'::market_side, CURRENT_TIMESTAMP, 
                    CURRENT_TIMESTAMP, 'new'::listing_type
                )
            ''')
            
            # Clean up test data
            cur.execute('DELETE FROM order_history WHERE order_id = %s', ('test_order',))
            cur.execute('DELETE FROM known_warframes WHERE name = %s', ('test_warframe',))
            
            conn.commit()
            return True
            
        except (psycopg2.Error, psycopg2.OperationalError) as e:
            logger.error("Database test failed: %s", e)
            conn.rollback()
            return False
        finally:
            cur.close()
            conn.close()

    def get_latest_prices(self, item_id: int) -> Dict[str, Any] | None:
        """Get the latest prices for a specific warframe/item
        
        Args:
            item_id: The database ID of the warframe
            
        Returns:
            Dictionary with current, min and max prices, or None if not found
        """
        conn = connect()
        cur = conn.cursor()
        
        try:
            # Get the latest price statistics for this item
            cur.execute('''
                SELECT 
                    avg_price, 
                    min_price, 
                    max_price 
                FROM price_statistics 
                WHERE item_id = %s 
                ORDER BY date DESC, hour DESC 
                LIMIT 1
            ''', (item_id,))
            
            result = cur.fetchone()
            if result:
                return {
                    'current': result[0],
                    'min': result[1],
                    'max': result[2]
                }
            return None
                
        except (psycopg2.Error, psycopg2.OperationalError) as e:
            logger.error("Error getting latest prices for item %s: %s", item_id, e)
            return None
        finally:
            cur.close()
            conn.close()

    def insert_price(self, item_id: int, price: float, quantity: int, side: str, recorded_at: datetime) -> None:
        """Insert a price record into the database
        
        Args:
            item_id: The database ID of the item
            price: The price in platinum
            quantity: The number of items
            side: Either 'buy' or 'sell'
            recorded_at: When the price was recorded
        """
        conn = connect()
        cur = conn.cursor()
        
        try:
            cur.execute('''
                INSERT INTO item_prices (item_id, recorded_at, price, quantity, side)
                VALUES (%s, %s, %s, %s, %s::market_side)
                ON CONFLICT (item_id, recorded_at, price, side) DO NOTHING
            ''', (item_id, recorded_at, price, quantity, side))
            
            conn.commit()
        except (psycopg2.Error, psycopg2.OperationalError) as e:
            logger.error("Error inserting price for item %s: %s", item_id, e)
            conn.rollback()
        finally:
            cur.close()
            conn.close()

    def insert_order(self, item_id: int, order_id: str, price: float, 
                    quantity: int, side: str, last_seen: datetime) -> None:
        """Insert or update an order in the database
        
        Args:
            item_id: The database ID of the item
            order_id: The order ID from the Warframe Market API
            price: The price in platinum
            quantity: The number of items
            side: Either 'buy' or 'sell'
            last_seen: When the order was last seen
        """
        conn = connect()
        cur = conn.cursor()
        
        try:
            # Check if this order already exists
            cur.execute(
                'SELECT id, initial_price, last_seen FROM order_history WHERE order_id = %s',
                (order_id,)
            )
            existing = cur.fetchone()
            
            if existing:
                # Update existing order
                order_id_db, initial_price, prev_last_seen = existing
                
                # Update the order
                cur.execute('''
                    UPDATE order_history
                    SET final_price = %s,
                        quantity = %s,
                        last_seen = %s,
                        price_history = CASE 
                            WHEN final_price != %s THEN price_history || ARRAY[%s] 
                            ELSE price_history
                        END,
                        visibilty_duration = %s - first_seen    
                    WHERE id = %s
                ''', (price, quantity, last_seen, price, last_seen, order_id_db))
            else:
                # Insert new order
                cur.execute('''
                    INSERT INTO order_history (
                        item_id, order_id, initial_price, final_price,
                        quantity, side, first_seen, last_seen, price_history
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s::market_side, %s, %s, ARRAY[%s]
                    )
                ''', (
                    item_id, order_id, price, price, 
                    quantity, side, last_seen, last_seen, price
                ))
                
            conn.commit()
        except (psycopg2.Error, psycopg2.OperationalError) as e:
            logger.error("Error inserting/updating order %s: %s", order_id, e)
            conn.rollback()
        finally:
            cur.close()
            conn.close()

    def get_recent_sell_prices(self, item_id: int, hours: int = 24) -> List[float]:
        """Get recent sell prices for an item to calculate trimmed mean
        
        Args:
            item_id: The database ID of the item
            hours: How many hours back to look for prices
            
        Returns:
            List of prices for the item in the specified time period
        """
        conn = connect()
        cur = conn.cursor()
        
        try:
            # Get recent prices for an item (sell orders only)
            cur.execute('''
                SELECT price 
                FROM item_prices
                WHERE item_id = %s 
                  AND side = 'sell'::market_side
                  AND recorded_at > NOW() - INTERVAL '%s hours'
            ''', (item_id, hours))
            
            result = cur.fetchall()
            return [float(price[0]) for price in result]  # Extract prices from result tuples
        except (psycopg2.Error, psycopg2.OperationalError) as e:
            logger.error("Error getting recent prices for item %s: %s", item_id, e)
            return []
        finally:
            cur.close()
            conn.close()

    def fetch_and_store_items(self, client):
        """Fetch all items from the API and store warframe sets."""
        try:
            data = client.fetch_items()
            set_items = [
                item["url_name"]
                for item in data["payload"]["items"]
                if "url_name" in item and "set" in item["url_name"].lower()
            ]
            for item_name in set_items:
                self.insert_warframe(item_name)
        except (KeyError, Exception) as e:
            logger.error("Error fetching and storing items: %s", e)

    def process_warframe_item(self, client, item_name: str):
        """Process a single warframe item to check if it belongs to a warframe set."""
        try:
            data = client.fetch_item_details(item_name)
            if "payload" in data and "item" in data["payload"]:
                items_in_set = data["payload"]["item"]["items_in_set"]
                for item in items_in_set:
                    if "tags" in item and "warframe" in item["tags"]:
                        self.insert_warframe(item_name)
                        logger.info("Stored warframe: %s", item_name)
                        break
        except (KeyError, Exception) as e:
            logger.error("Error processing warframe item %s: %s", item_name, e)

    def identify_warframes(self, client, set_items: List[str]):
        """Identify which sets are warframes and store them."""
        tasks = [self.process_warframe_item(client, item) for item in set_items]
        for task in tasks:
            task  # Execute each task synchronously for simplicity
        logger.info("Warframe sets identified and stored.")

    def process_warframe_orders(self, client):
        """Process orders for all known warframes."""
        warframes = self.get_all_warframes()
        for wf_id, name in warframes:
            self.process_single_warframe(client, wf_id, name)

    def process_single_warframe(self, client, wf_id: int, name: str):
        """Process orders for a single warframe."""
        try:
            data = client.fetch_orders(name)
            current_time = datetime.now(timezone.utc)
            active_order_ids = set()
            for order in data['payload']['orders']:
                last_seen = client.parse_timestamp(order.get('last_seen'))
                if not last_seen or (current_time - last_seen).days > 30:
                    continue
                self.insert_order(wf_id, order['id'], order['platinum'], order['quantity'], order['order_type'], last_seen)
                active_order_ids.add(order['id'])
            self.update_order_status()
        except Exception as e:
            logger.error("Error processing orders for %s: %s", name, e)

    def process_order(self, wf_id: int, order: Dict, client):
        """Process a single order in the database."""
        try:
            conn = connect()
            cur = conn.cursor()
            try:
                cur.execute('''
                    SELECT id, initial_price, price_changes 
                    FROM order_history 
                    WHERE order_id = %s
                ''', (order['id'],))
                existing_order = cur.fetchone()
                current_price = int(order['platinum'])
                last_seen = client.parse_timestamp(order.get('last_seen'))
                if existing_order:
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
            except (psycopg2.Error, ValueError, KeyError) as e:
                conn.rollback()
                logger.error("Database error processing order: %s", e)
                raise
            finally:
                cur.close()
                conn.close()
        except (psycopg2.Error, ConnectionError) as e:
            logger.error("Error processing order: %s", e)