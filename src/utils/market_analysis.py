from typing import List, Dict, Tuple, Optional
from datetime import datetime, timezone, timedelta
import statistics
from collections import defaultdict
from scipy import stats

from ..models.data_models import TimeRange, MarketTrend, MarketAnalysis
from ..database.config import connect

def analyze_market_data(item_id: int, time_range: TimeRange) -> Optional[MarketAnalysis]:
    """Analyze market data for a specific item within the given time range"""
    conn = connect()
    cur = conn.cursor()
    
    try:
        # Calculate the start date based on time range
        current_time = datetime.now(timezone.utc)
        if time_range == TimeRange.WEEK:
            start_date = current_time - timedelta(days=7)
        elif time_range == TimeRange.MONTH:
            start_date = current_time - timedelta(days=30)
        elif time_range == TimeRange.THREE_MONTHS:
            start_date = current_time - timedelta(days=90)
        elif time_range == TimeRange.SIX_MONTHS:
            start_date = current_time - timedelta(days=180)
        else:  # ALL_TIME
            start_date = datetime.min.replace(tzinfo=timezone.utc)

        # Fetch all relevant price data
        cur.execute('''
            SELECT price, quantity, side, recorded_at
            FROM item_prices
            WHERE item_id = %s AND recorded_at >= %s
            ORDER BY recorded_at ASC
        ''', (item_id, start_date))
        
        records = cur.fetchall()
        if not records:
            return None

        # Process records into data structures
        buy_orders = defaultdict(list)
        sell_orders = defaultdict(list)
        daily_volumes = defaultdict(int)
        hourly_prices = defaultdict(list)
        weekday_prices = defaultdict(list)
        
        for price, quantity, side, timestamp in records:
            if side == 'buy':
                buy_orders[timestamp.date()].append((price, quantity))
            else:
                sell_orders[timestamp.date()].append((price, quantity))
            
            daily_volumes[timestamp.date()] += quantity
            hourly_prices[timestamp.hour].append(price)
            weekday_prices[timestamp.strftime('%A')].append(price)

        # Calculate trends
        price_trends = []
        market_spread_trend = []
        
        for date in sorted(set(buy_orders.keys()) | set(sell_orders.keys())):
            buy_prices = [p for p, _ in buy_orders[date]]
            sell_prices = [p for p, _ in sell_orders[date]]
            all_prices = buy_prices + sell_prices
            
            if all_prices:
                trend = MarketTrend(
                    avg_price=statistics.mean(all_prices) if all_prices else 0,
                    min_price=min(all_prices) if all_prices else 0,
                    max_price=max(all_prices) if all_prices else 0,
                    volatility=statistics.stdev(all_prices) if len(all_prices) > 1 else 0,
                    volume=sum(q for _, q in buy_orders[date] + sell_orders[date]),
                    market_spread=statistics.mean(sell_prices) - statistics.mean(buy_prices) if buy_prices and sell_prices else 0,
                    best_buy_price=max(buy_prices) if buy_prices else 0,
                    best_sell_price=min(sell_prices) if sell_prices else 0,
                    timestamp=datetime.combine(date, datetime.min.time()).replace(tzinfo=timezone.utc)
                )
                price_trends.append(trend)
                market_spread_trend.append(trend.market_spread)

        # Calculate best trading times
        best_buy_hour = min(hourly_prices.items(), key=lambda x: statistics.mean(x[1]))[0]
        best_sell_hour = max(hourly_prices.items(), key=lambda x: statistics.mean(x[1]))[0]

        # Calculate seasonal patterns
        seasonal_patterns = {
            day: statistics.mean(prices)
            for day, prices in weekday_prices.items()
        }

        # Calculate demand strength
        total_buy_volume = sum(q for orders in buy_orders.values() for _, q in orders)
        total_sell_volume = sum(q for orders in sell_orders.values() for _, q in orders)
        demand_strength = total_buy_volume / total_sell_volume if total_sell_volume > 0 else 0

        return MarketAnalysis(
            price_trends=price_trends,
            avg_daily_volume=statistics.mean(daily_volumes.values()),
            price_volatility=statistics.stdev([t.avg_price for t in price_trends]) if len(price_trends) > 1 else 0,
            market_spread_trend=market_spread_trend,
            best_buy_time=f"{best_buy_hour:02d}:00 UTC",
            best_sell_time=f"{best_sell_hour:02d}:00 UTC",
            demand_strength=demand_strength,
            seasonal_patterns=seasonal_patterns
        )

    except Exception as e:
        print(f"Error analyzing market data: {e}")
        return None
    finally:
        cur.close()
        conn.close()

def detect_outliers(prices: List[float], threshold: float = 2.0) -> List[bool]:
    """Detect price outliers using Z-score method"""
    if not prices:
        return []
    z_scores = stats.zscore(prices)
    return [abs(z) > threshold for z in z_scores]

def detect_rapid_price_changes(order_id: str) -> Tuple[bool, float]:
    """Detect if an order has had rapid price changes"""
    conn = connect()
    cur = conn.cursor()
    
    try:
        cur.execute('''
            SELECT initial_price, final_price, 
                   EXTRACT(EPOCH FROM (last_seen - first_seen))/3600 as hours
            FROM order_history 
            WHERE order_id = %s
        ''', (order_id,))
        
        result = cur.fetchone()
        if not result:
            return False, 0.0
            
        initial_price, final_price, hours = result
        if hours < 1:  # Less than an hour
            return False, 0.0
            
        price_change_rate = abs(final_price - initial_price) / hours
        return price_change_rate > 10, price_change_rate  # Consider >10 plat/hour rapid
        
    finally:
        cur.close()
        conn.close()

def calculate_price_heatmap(item_id: int) -> Dict[str, Dict[int, float]]:
    """Calculate price heatmap by day of week and hour"""
    conn = connect()
    cur = conn.cursor()
    
    try:
        cur.execute('''
            SELECT 
                EXTRACT(DOW FROM recorded_at) as day_of_week,
                EXTRACT(HOUR FROM recorded_at) as hour,
                AVG(price) as avg_price
            FROM item_prices
            WHERE item_id = %s
            GROUP BY day_of_week, hour
            ORDER BY day_of_week, hour
        ''', (item_id,))
        
        heatmap = defaultdict(dict)
        days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        
        for day_num, hour, avg_price in cur.fetchall():
            day_name = days[int(day_num)]
            heatmap[day_name][int(hour)] = float(avg_price)
        
        return dict(heatmap)
    finally:
        cur.close()
        conn.close()