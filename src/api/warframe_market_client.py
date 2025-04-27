import aiohttp
import asyncio
from datetime import datetime
from typing import Optional, Dict
import dateutil.parser
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self, calls_per_second: float = 2.0):
        self.calls_per_second = calls_per_second
        self.min_interval = 1.0 / calls_per_second
        self.last_call = 0.0
        self.semaphore = asyncio.Semaphore(1)

    async def acquire(self):
        async with self.semaphore:
            now = asyncio.get_event_loop().time()
            time_since_last = now - self.last_call
            if time_since_last < self.min_interval:
                await asyncio.sleep(self.min_interval - time_since_last)
            self.last_call = asyncio.get_event_loop().time()

class WarframeMarketClient:
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
        """Make a rate-limited request with retries"""
        if not self.session:
            await self.create_session()

        await self.rate_limiter.acquire()
        
        try:
            async with self.session.get(url, headers=self.headers) as response:
                if response.status == 429:  # Too Many Requests
                    if retries < self.max_retries:
                        await asyncio.sleep(self.retry_delay * (retries + 1))
                        return await self.make_request(url, retries + 1)
                    raise Exception(f"Max retries reached for {url}")
                
                response.raise_for_status()
                return await response.json()
                
        except aiohttp.ClientError as e:
            if retries < self.max_retries:
                await asyncio.sleep(self.retry_delay * (retries + 1))
                return await self.make_request(url, retries + 1)
            raise

    async def fetch_items(self) -> Dict:
        """Fetch all items from the API"""
        return await self.make_request(f"{self.base_url}/items")

    async def fetch_item_details(self, item_name: str) -> Dict:
        """Fetch details for a specific item"""
        return await self.make_request(f"{self.base_url}/items/{item_name}")

    async def fetch_orders(self, item_name: str) -> Dict:
        """Fetch orders for a specific item"""
        return await self.make_request(f"{self.base_url}/items/{item_name}/orders")

    @staticmethod
    def parse_timestamp(timestamp_str: str) -> Optional[datetime]:
        """Parse timestamp string to datetime object"""
        if not timestamp_str:
            return None
        try:
            return dateutil.parser.parse(timestamp_str)
        except (ValueError, TypeError):
            return None