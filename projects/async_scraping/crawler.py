import asyncio
import aiohttp
import logging
import time
from typing import List
from bs4 import BeautifulSoup
from projects.async_scraping.pages.all_books_page import AllBooksPage
from projects.async_scraping.models import Book

logger = logging.getLogger(__name__)

class BookCrawler:
    def __init__(self, base_url: str, worker_count: int = 5):
        self.base_url = base_url
        self.worker_count = worker_count
        self.queue = asyncio.Queue()
        self.results: List[Book] = []
        self.session = None

    async def fetch(self, url: str) -> str:
        async with self.session.get(url) as response:
            if response.status != 200:
                logger.error(f"Failed to fetch {url}: {response.status}")
                return ""
            return await response.text()

    async def worker(self):
        while True:
            url = await self.queue.get()
            try:
                logger.info(f"Crawling {url}")
                html = await self.fetch(url)
                if html:
                    page = AllBooksPage(html)
                    for book_parser in page.books:
                        # Extract raw data from the parser
                        raw_data = {
                            "name": book_parser.name,
                            "price": book_parser.price, # The parser already does some regex, but our model handles it too
                            "rating": book_parser.rating,
                            "link": book_parser.link
                        }
                        try:
                            book = Book(**raw_data)
                            self.results.append(book)
                        except Exception as e:
                            logger.error(f"Validation error for {raw_data['name']}: {e}")
            except Exception as e:
                logger.exception(f"Worker encountered error on {url}")
            finally:
                self.queue.task_done()

    async def run(self):
        async with aiohttp.ClientSession() as session:
            self.session = session
            
            # 1. Discover total pages (Bootstrap)
            logger.info("Discovering total pages...")
            initial_html = await self.fetch(self.base_url)
            if not initial_html:
                return
            
            initial_page = AllBooksPage(initial_html)
            page_count = initial_page.page_count
            logger.info(f"Found {page_count} pages to crawl.")

            # 2. Fill the queue
            for i in range(1, page_count + 1):
                url = f"{self.base_url}/catalogue/page-{i}.html"
                await self.queue.put(url)

            # 3. Start workers
            workers = [asyncio.create_task(self.worker()) for _ in range(self.worker_count)]

            # 4. Wait for queue to empty
            start_time = time.perf_counter()
            await self.queue.join()
            end_time = time.perf_counter()

            # 5. Cleanup workers
            for w in workers:
                w.cancel()
            
            logger.info(f"Crawl completed in {end_time - start_time:.2f}s. Total books: {len(self.results)}")
