"""
Data Crawler for collecting and processing external data
"""

import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json

from config.settings import Settings
from database.database import Database

logger = logging.getLogger(__name__)

class DataCrawler:
    """Main data crawler class"""
    
    def __init__(self):
        self.settings = Settings()
        self.database = Database()
        self.session: Optional[aiohttp.ClientSession] = None
        self.running = False
        self.tasks: List[asyncio.Task] = []
    
    async def start(self):
        """Start the data crawler"""
        if not self.settings.crawler.enabled:
            logger.info("Data crawler is disabled")
            return
        
        logger.info("Starting data crawler...")
        self.running = True
        
        # Initialize HTTP session
        timeout = aiohttp.ClientTimeout(total=self.settings.crawler.timeout)
        self.session = aiohttp.ClientSession(timeout=timeout)
        
        # Initialize database connection
        await self.database.initialize()
        
        # Start crawler tasks
        await self._start_crawler_tasks()
    
    async def stop(self):
        """Stop the data crawler"""
        logger.info("Stopping data crawler...")
        self.running = False
        
        # Cancel all tasks
        for task in self.tasks:
            if not task.done():
                task.cancel()
        
        # Wait for tasks to complete
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        
        # Close HTTP session
        if self.session:
            await self.session.close()
        
        # Close database connection
        await self.database.close()
        
        logger.info("Data crawler stopped")
    
    async def _start_crawler_tasks(self):
        """Start all crawler tasks"""
        interval = self.settings.crawler.interval
        
        # Example crawler tasks - customize based on your needs
        tasks = [
            self._create_periodic_task(self._crawl_example_api, interval),
            self._create_periodic_task(self._crawl_rss_feeds, interval * 2),
            self._create_periodic_task(self._cleanup_old_data, 3600 * 24),  # Daily cleanup
        ]
        
        self.tasks.extend(tasks)
        logger.info(f"Started {len(tasks)} crawler tasks")
    
    def _create_periodic_task(self, coro_func, interval: int) -> asyncio.Task:
        """Create a periodic task that runs a coroutine at intervals"""
        async def periodic_wrapper():
            while self.running:
                try:
                    await coro_func()
                except Exception as e:
                    logger.error(f"Error in periodic task {coro_func.__name__}: {e}")
                
                # Wait for next interval
                await asyncio.sleep(interval)
        
        return asyncio.create_task(periodic_wrapper())
    
    async def _crawl_example_api(self):
        """Example API crawler - replace with your actual data sources"""
        logger.debug("Crawling example API...")
        
        try:
            url = "https://jsonplaceholder.typicode.com/posts"
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    await self._process_api_data(data)
                    logger.info(f"Processed {len(data)} items from example API")
                else:
                    logger.warning(f"API request failed with status {response.status}")
        
        except Exception as e:
            logger.error(f"Error crawling example API: {e}")
    
    async def _crawl_rss_feeds(self):
        """Example RSS feed crawler"""
        logger.debug("Crawling RSS feeds...")
        
        # Example RSS feeds - replace with your actual feeds
        feeds = [
            "https://feeds.feedburner.com/oreilly/radar/feed",
            "https://rss.cnn.com/rss/edition.rss"
        ]
        
        for feed_url in feeds:
            try:
                await self._process_rss_feed(feed_url)
            except Exception as e:
                logger.error(f"Error processing RSS feed {feed_url}: {e}")
    
    async def _process_rss_feed(self, feed_url: str):
        """Process a single RSS feed"""
        try:
            async with self.session.get(feed_url) as response:
                if response.status == 200:
                    content = await response.text()
                    # Here you would parse the RSS/XML content
                    # For now, just log that we received it
                    logger.debug(f"Received RSS content from {feed_url}: {len(content)} chars")
                    
                    # You can use libraries like feedparser to parse RSS
                    # import feedparser
                    # parsed = feedparser.parse(content)
                    # await self._store_feed_items(parsed.entries)
                else:
                    logger.warning(f"RSS feed request failed with status {response.status}")
        
        except Exception as e:
            logger.error(f"Error processing RSS feed {feed_url}: {e}")
    
    async def _process_api_data(self, data: List[Dict[str, Any]]):
        """Process data from API and store in database"""
        processed_count = 0
        
        for item in data:
            try:
                # Example processing - customize based on your data structure
                processed_item = {
                    'id': item.get('id'),
                    'title': item.get('title', ''),
                    'content': item.get('body', ''),
                    'user_id': item.get('userId'),
                    'created_at': datetime.utcnow(),
                    'source': 'example_api'
                }
                
                # Store in database (implement based on your schema)
                await self._store_data_item(processed_item)
                processed_count += 1
                
            except Exception as e:
                logger.error(f"Error processing API item {item}: {e}")
        
        logger.info(f"Successfully processed {processed_count} API items")
    
    async def _store_data_item(self, item: Dict[str, Any]):
        """Store a single data item in the database"""
        # Implement based on your database schema
        # Example:
        # async with self.database.get_session() as session:
        #     db_item = DataModel(**item)
        #     session.add(db_item)
        #     await session.commit()
        pass
    
    async def _cleanup_old_data(self):
        """Clean up old data from the database"""
        logger.debug("Running data cleanup...")
        
        try:
            # Remove data older than 30 days
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            # Implement cleanup based on your database schema
            # async with self.database.get_session() as session:
            #     result = await session.execute(
            #         delete(DataModel).where(DataModel.created_at < cutoff_date)
            #     )
            #     await session.commit()
            #     logger.info(f"Cleaned up {result.rowcount} old records")
            
            logger.info("Data cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during data cleanup: {e}")
    
    async def crawl_url(self, url: str, headers: Dict[str, str] = None) -> Optional[Dict[str, Any]]:
        """Crawl a single URL and return the data"""
        try:
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    content_type = response.headers.get('content-type', '').lower()
                    
                    if 'application/json' in content_type:
                        return await response.json()
                    else:
                        text = await response.text()
                        return {'content': text, 'url': url, 'status': response.status}
                else:
                    logger.warning(f"Failed to crawl {url}: HTTP {response.status}")
                    return None
        
        except Exception as e:
            logger.error(f"Error crawling {url}: {e}")
            return None
    
    async def batch_crawl(self, urls: List[str], max_concurrent: int = None) -> List[Dict[str, Any]]:
        """Crawl multiple URLs concurrently"""
        if max_concurrent is None:
            max_concurrent = self.settings.crawler.max_concurrent
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def crawl_with_semaphore(url):
            async with semaphore:
                return await self.crawl_url(url)
        
        tasks = [crawl_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out None results and exceptions
        valid_results = []
        for result in results:
            if isinstance(result, dict):
                valid_results.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Crawl task failed: {result}")
        
        return valid_results
    
    def get_status(self) -> Dict[str, Any]:
        """Get crawler status information"""
        return {
            'running': self.running,
            'active_tasks': len([task for task in self.tasks if not task.done()]),
            'total_tasks': len(self.tasks),
            'settings': {
                'enabled': self.settings.crawler.enabled,
                'interval': self.settings.crawler.interval,
                'max_concurrent': self.settings.crawler.max_concurrent,
                'timeout': self.settings.crawler.timeout
            }
        }