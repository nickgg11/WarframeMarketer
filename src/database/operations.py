from typing import List, Tuple, Optional
from datetime import datetime, timezone, timedelta
import logging
from .config import connect

logger = logging.getLogger(__name__)

class DatabaseOperations:
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
                    initial_price INTEGER NOT NULL,
                    final_price INTEGER NOT NULL,
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
                    price INTEGER NOT NULL,
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
                    min_price INTEGER NOT NULL,
                    max_price INTEGER NOT NULL,
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
            
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
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
        except Exception as e:
            logger.error(f"Error inserting warframe {name}: {e}")
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
            return cur.fetchall()
        finally:
            cur.close()
            conn.close()

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
        except Exception as e:
            logger.error(f"Error updating order statuses: {e}")
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
            logger.info(f"Purged data older than {months} months")
            
        except Exception as e:
            logger.error(f"Error purging old data: {e}")
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
            
        except Exception as e:
            logger.error(f"Database test failed: {e}")
            conn.rollback()
            return False
        finally:
            cur.close()
            conn.close()