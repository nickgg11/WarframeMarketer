"""
Market analysis utilities for Warframe Market data.
Provides functions to analyze price trends, detect outliers, and identify market patterns.
"""

from typing import List, Dict, Tuple, Optional
from datetime import datetime, timezone, timedelta, date as datetime_date
import statistics
from collections import defaultdict
from scipy import stats

# Fix import paths to be relative for proper module resolution
from src.models.data_models import TimeRange, MarketTrend, MarketAnalysis
from src.database.config import connect

def analyze_market_data(item_id: int, time_range: TimeRange) -> Optional[MarketAnalysis]:
    """Analyze market data for a specific item within the given time range.
    
    Args:
        item_id: Database ID of the item to analyze
        time_range: Time period for the analysis
        
    Returns:
        MarketAnalysis object containing trend data or None if no data available
    """
    # pylint: disable=too-many-locals,too-many-branches
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
        daily_volumes: Dict[datetime_date, int] = defaultdict(int)
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
        
        for day_date in sorted(set(buy_orders.keys()) | set(sell_orders.keys())):
            buy_prices = [p for p, _ in buy_orders[day_date]]
            sell_prices = [p for p, _ in sell_orders[day_date]]
            all_prices = buy_prices + sell_prices
            
            if all_prices:
                trend = MarketTrend(
                    avg_price=statistics.mean(all_prices) if all_prices else 0,
                    min_price=min(all_prices) if all_prices else 0,
                    max_price=max(all_prices) if all_prices else 0,
                    volatility=statistics.stdev(all_prices) if len(all_prices) > 1 else 0,
                    volume=sum(q for _, q in buy_orders[day_date] + sell_orders[day_date]),
                    market_spread=(
                        statistics.mean(sell_prices) - statistics.mean(buy_prices) 
                        if buy_prices and sell_prices else 0
                    ),
                    best_buy_price=max(buy_prices) if buy_prices else 0,
                    best_sell_price=min(sell_prices) if sell_prices else 0,
                    timestamp=datetime.combine(day_date, datetime.min.time()).replace(tzinfo=timezone.utc)
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
            price_volatility=(
                statistics.stdev([t.avg_price for t in price_trends]) if len(price_trends) > 1 else 0
            ),
            market_spread_trend=market_spread_trend,
            best_buy_time=f"{best_buy_hour:02d}:00 UTC",
            best_sell_time=f"{best_sell_hour:02d}:00 UTC",
            demand_strength=demand_strength,
            seasonal_patterns=seasonal_patterns
        )
    # Use a more specific exception instead of a broad catch
    except (ValueError, TypeError, statistics.StatisticsError) as e:
        # Should use proper logging instead of print
        print(f"Error analyzing market data: {e}")
        return None
    finally:
        cur.close()
        conn.close()

def detect_outliers(prices: List[float], threshold: float = 2.0) -> List[bool]:
    """Detect price outliers using Z-score method.
    
    Args:
        prices: List of price values to analyze
        threshold: Z-score threshold to consider as outlier (default: 2.0)
        
    Returns:
        List of boolean values indicating which prices are outliers
    """
    if not prices:
        return []
    z_scores = stats.zscore(prices)
    return [abs(z) > threshold for z in z_scores]

def detect_rapid_price_changes(order_id: str) -> Tuple[bool, float]:
    """Detect if an order has had rapid price changes.
    
    Args:
        order_id: ID of the order to analyze
        
    Returns:
        Tuple of (is_rapid_change, change_rate_per_hour)
    """
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
    """Calculate price heatmap by day of week and hour.
    
    Args:
        item_id: Database ID of the item to analyze
        
    Returns:
        Nested dict mapping day names to hours to average prices
    """
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
        
        heatmap: Dict[str, Dict[int, float]] = defaultdict(dict)
        days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        
        for day_num, hour, avg_price in cur.fetchall():
            day_name = days[int(day_num)]
            heatmap[day_name][int(hour)] = float(avg_price)
        
        return dict(heatmap)
    finally:
        cur.close()
        conn.close()

def calculate_trimmed_mean(values: list, trim_percent: float = 10.0) -> float:
    """Calculate the trimmed mean from a list of values
    
    Removes the specified percentage from both the high and low ends
    before calculating the mean.
    
    Args:
        values: List of numerical values
        trim_percent: Percentage to trim from both ends (default: 10%)
        
    Returns:
        Trimmed mean value, or 0 if insufficient data
    """
    if not values:
        return 0.0
        
    # Need at least 3 values for a meaningful trimmed mean
    if len(values) < 3:
        return sum(values) / len(values)
        
    # Sort the values
    sorted_values = sorted(values)
    
    # Calculate how many values to trim from each end
    trim_count = int(len(sorted_values) * trim_percent / 100)
    
    # Trim the values and calculate mean
    if trim_count > 0:
        trimmed_values = sorted_values[trim_count:-trim_count]
    else:
        trimmed_values = sorted_values
        
    # Calculate and return mean of trimmed values
    if trimmed_values:
        return sum(trimmed_values) / len(trimmed_values)
    return 0.0