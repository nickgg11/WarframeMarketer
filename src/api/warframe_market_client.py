"""
Client for interacting with the Warframe Market API.
Provides rate-limited access to the API endpoints with retry mechanisms.
"""

# Standard library imports first
import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, List, Any

# Third-party imports next
import aiohttp
import dateutil.parser

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiter to control API request frequency.
    
    Ensures API requests are spaced properly to avoid rate limiting.
    """
    def __init__(self, calls_per_second: float = 2.0):
        self.calls_per_second = calls_per_second
        self.min_interval = 1.0 / calls_per_second
        self.last_call = 0.0
        self.semaphore = asyncio.Semaphore(1)

    async def acquire(self):
        """Acquire permission to make an API call with proper rate limiting."""
        async with self.semaphore:
            now = asyncio.get_event_loop().time()
            time_since_last = now - self.last_call
            if time_since_last < self.min_interval:
                await asyncio.sleep(self.min_interval - time_since_last)
            self.last_call = asyncio.get_event_loop().time()

class WarframeMarketClient:
    """Client for accessing the Warframe Market API.
    
    Provides methods to fetch items, item details, and market orders
    with built-in rate limiting and error handling.
    """
    def __init__(self):
        self.base_url = "https://api.warframe.market/v1"
        self.headers = {
            "Platform": "pc",
            "Accept": "application/json"
        }
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limiter = RateLimiter(2.0)  # 2 requests per second
        self.max_retries = 3
        self.retry_delay = 1.0

    async def create_session(self):
        """Create an HTTP session"""
        if not self.session:
            connector = aiohttp.TCPConnector(limit=10)  # Limit concurrent connections
            self.session = aiohttp.ClientSession(connector=connector)

    async def close_session(self):
        """Close the HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None

    async def make_request(self, url: str, retries: int = 0) -> Dict:
        """Make a rate-limited request with retries.
        
        Args:
            url: The URL to make the request to
            retries: Current retry count (used internally)
            
        Returns:
            JSON response as a dictionary
            
        Raises:
            aiohttp.ClientError: If the request fails after all retries
        """
        if not self.session:
            await self.create_session()
            
        # Ensure session is initialized
        if not self.session:
            raise RuntimeError("Failed to create HTTP session")

        await self.rate_limiter.acquire()
        
        try:
            async with self.session.get(url, headers=self.headers) as response:
                if response.status == 429:  # Too Many Requests
                    if retries < self.max_retries:
                        await asyncio.sleep(self.retry_delay * (retries + 1))
                        return await self.make_request(url, retries + 1)
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=response.status,
                        message=f"Max retries reached for {url}"
                    )
                
                response.raise_for_status()
                return await response.json()
                
        except aiohttp.ClientError:
            if retries < self.max_retries:
                await asyncio.sleep(self.retry_delay * (retries + 1))
                return await self.make_request(url, retries + 1)
            raise

    async def fetch_items(self, progress_callback=None) -> Dict:
        """Fetch all items from the API.
        
        Args:
            progress_callback: Optional callback function to report progress
            
        Returns:
            Dictionary containing all items data
        """
        result = await self.make_request(f"{self.base_url}/items")
        if progress_callback:
            progress_callback(100)
        return result

    async def fetch_item_details(self, item_name: str, progress_callback=None) -> Dict:
        """Fetch details for a specific item.
        
        Args:
            item_name: URL name of the item to fetch
            progress_callback: Optional callback function to report progress
            
        Returns:
            Dictionary containing item details
        """
        result = await self.make_request(f"{self.base_url}/items/{item_name}")
        if progress_callback:
            progress_callback(100)
        return result

    async def fetch_orders(self, item_name: str, progress_callback=None) -> Dict:
        """Fetch orders for a specific item.
        
        Args:
            item_name: URL name of the item to fetch orders for
            progress_callback: Optional callback function to report progress
            
        Returns:
            Dictionary containing order data
        """
        result = await self.make_request(f"{self.base_url}/items/{item_name}/orders")
        if progress_callback:
            progress_callback(100)
        return result
        
    async def fetch_items_batch(self, items: List[str], progress_callback=None) -> Dict[str, Any]:
        """Fetch details for multiple items with progress reporting.
        
        Args:
            items: List of item names to fetch details for
            progress_callback: Optional callback function to report progress
            
        Returns:
            Dictionary mapping item names to their details
        """
        results = {}
        total = len(items)
        
        for i, item in enumerate(items):
            results[item] = await self.fetch_item_details(item)
            
            if progress_callback and total > 0:
                # Report progress as a percentage
                progress = int((i + 1) / total * 100)
                progress_callback(progress)
                
        return results
        
    async def fetch_orders_batch(self, items: List[str], progress_callback=None) -> Dict[str, Any]:
        """Fetch orders for multiple items with progress reporting.
        
        Args:
            items: List of item names to fetch orders for
            progress_callback: Optional callback function to report progress
            
        Returns:
            Dictionary mapping item names to their orders data
        """
        results = {}
        total = len(items)
        
        for i, item in enumerate(items):
            results[item] = await self.fetch_orders(item)
            
            if progress_callback and total > 0:
                # Report progress as a percentage
                progress = int((i + 1) / total * 100)
                progress_callback(progress)
                
        return results

    async def fetch_prices_batch(self, items: List[str], progress_callback=None) -> Dict[str, Any]:
        """Fetch price data for multiple items with progress reporting.
        
        This method fetches orders for each item and extracts price information.
        
        Args:
            items: List of item names to fetch prices for
            progress_callback: Optional callback function to report progress
            
        Returns:
            Dictionary mapping item names to their price data
        """
        results = {}
        total = len(items)
        
        for i, item in enumerate(items):
            # Fetch orders which contain price information
            orders_data = await self.fetch_orders(item)
            
            # Extract price information from orders
            if orders_data and 'payload' in orders_data:
                # Process the orders to extract price data
                # In this implementation we're just storing the raw orders data
                # You might want to process this further depending on your needs
                results[item] = orders_data['payload']
            
            if progress_callback and total > 0:
                # Report progress as a percentage
                progress = int((i + 1) / total * 100)
                progress_callback(progress)
                
        return results

    @staticmethod
    def parse_timestamp(timestamp_str: str) -> Optional[datetime]:
        """Parse timestamp string to datetime object.
        
        Args:
            timestamp_str: ISO format timestamp string
            
        Returns:
            Datetime object or None if parsing fails
        """
        if not timestamp_str:
            return None
        try:
            return dateutil.parser.parse(timestamp_str)
        except (ValueError, TypeError):
            return None
