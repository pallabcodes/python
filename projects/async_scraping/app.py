import asyncio
import logging
import sys
import cProfile
import pstats
import io
from projects.async_scraping.crawler import BookCrawler

# Configure logging to match Elite standard
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("scraping_elite.log")
    ]
)

logger = logging.getLogger(__name__)

async def main():
    base_url = "http://books.toscrape.com"
    crawler = BookCrawler(base_url, worker_count=10)
    
    # Run with Profiling
    logger.info("Starting Elite Scraper...")
    
    pr = cProfile.Profile()
    pr.enable()
    
    await crawler.run()
    
    pr.disable()
    
    # Report Top 10 books by price (Elite sorting)
    sorted_books = sorted(crawler.results, key=lambda x: x.price, reverse=True)
    print("\n--- Top 10 Most Expensive Books ---")
    for book in sorted_books[:10]:
        print(f"£{book.price:<6} | {book.rating} Stars | {book.name}")

    # Output profiling summary to log
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats(pstats.SortKey.CUMULATIVE)
    ps.print_stats(15)
    logger.debug(f"Profiling Results:\n{s.getvalue()}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Scraper stopped by user.")
    except Exception as e:
        logger.exception("Fatal error in scraper")