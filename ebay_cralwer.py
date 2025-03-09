import requests
from bs4 import BeautifulSoup
import os
import json
import aiofiles
import asyncio
from urllib.parse import urljoin
import re
import argparse
import logging
from datetime import datetime


class EbayCrawler:
    """A web crawler for extracting product listings from an eBay store."""
    
    def __init__(self, store_name="garlandcomputer", data_dir="data", log_level=logging.INFO):
        """Initialize crawler with store name and setup logging."""
        self.store_name = store_name
        self.base_url = f"https://www.ebay.com/sch/{store_name}/m.html"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        self.data_dir = os.path.join(data_dir, store_name)
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
        self._setup_logging(log_level)

    def _setup_logging(self, log_level):
        """Configure logging for the crawler."""
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        log_file = os.path.join(log_dir, f"{self.store_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        
        self.logger = logging.getLogger(f"EbayCrawler_{self.store_name}")
        self.logger.setLevel(log_level)
        
        if self.logger.handlers:
            self.logger.handlers.clear()
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        self.logger.info(f"Initialized crawler for store: {self.store_name}")
        self.logger.info(f"Data will be saved to: {self.data_dir}")

    async def write_json_file(self, item_id, data):
        """Save item data to a JSON file."""
        filename = os.path.join(self.data_dir, f"{item_id}.json")
        async with aiofiles.open(filename, 'w') as f:
            await f.write(json.dumps(data, indent=4))
        self.logger.debug(f"Saved item {item_id} to {filename}")

    def extract_item_id(self, url):
        """Extract the item ID from the product URL."""
        match = re.search(r'/itm/(\d+)', url)
        return match.group(1) if match else None

    def parse_item(self, item, condition_filter=None):
        """Parse an item listing and return its details if it matches the filter."""
        title_elem = item.find('div', class_='s-item__title')
        title = title_elem.text.strip() if title_elem else "No title"

        price_elem = item.find('span', class_='s-item__price')
        price = price_elem.text.strip() if price_elem else "0.00"

        price = re.sub(r'[^\d.]', '', price.split(' to ')[0])

        link_elem = item.find('a', class_='s-item__link')
        product_url = link_elem['href'] if link_elem else None
        if not product_url:
            return None

        condition_elem = item.find('span', class_='SECONDARY_INFO')
        condition = condition_elem.text.strip() if condition_elem else "Unknown"

        # apply condition filter if specified
        if condition_filter and condition.lower() != condition_filter.lower():
            self.logger.debug(f"Skipping item with condition '{condition}' (filter: '{condition_filter}')")
            return None

        item_id = self.extract_item_id(product_url)
        if not item_id:
            self.logger.warning(f"Could not extract item ID from URL: {product_url}")
            return None

        self.logger.debug(f"Parsed item: {title} ({condition}) - ${price}")
        return {
            "title": title,
            "condition": condition,
            "price": price,
            "product_url": product_url
        }

    async def process_page(self, url, condition_filter=None):
        """Process a page, extract items, and save them."""
        self.logger.info(f"Processing page: {url}")
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch page: {url} - {str(e)}")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        items = soup.find_all('li', class_='s-item')
        self.logger.info(f"Found {len(items)} items on page")

        tasks = []
        for item in items:
            item_data = self.parse_item(item, condition_filter)
            if item_data:
                item_id = self.extract_item_id(item_data['product_url'])
                if item_id:
                    tasks.append(self.write_json_file(item_id, item_data))

        if tasks:
            self.logger.info(f"Saving {len(tasks)} items")
            await asyncio.gather(*tasks)

        # Pagination
        next_page = soup.find('a', class_='pagination__next')
        next_url = urljoin(self.base_url, next_page['href']) if next_page else None
        
        if next_url:
            self.logger.info(f"Found next page: {next_url}")
        else:
            self.logger.info("No more pages to process")
            
        return next_url

    async def crawl(self, condition_filter=None):
        """Crawl the eBay store and save product data."""
        self.logger.info(f"Starting crawl of store '{self.store_name}' with condition filter: {condition_filter}")
        url = self.base_url
        page_count = 0
        item_count = 0

        while url:
            self.logger.info(f"Processing page {page_count + 1}")
            next_url = await self.process_page(url, condition_filter)
            
            current_items = len([f for f in os.listdir(self.data_dir) if f.endswith('.json')])
            new_items = current_items - item_count
            item_count = current_items
            
            self.logger.info(f"Extracted {new_items} new items from page {page_count + 1}")
            
            url = next_url
            page_count += 1

        self.logger.info(f"Crawl completed for store '{self.store_name}'. Processed {page_count} pages with {item_count} total items.")
        return page_count, item_count


def main():
    """Parse arguments and run the crawler."""
    parser = argparse.ArgumentParser(description="eBay Store Crawler")
    parser.add_argument('--store', type=str, default="garlandcomputer",
                        help='eBay store name to crawl (default: garlandcomputer)')
    parser.add_argument('--condition', type=str, choices=['New', 'Pre-Owned', 'Used'], 
                        help='Filter items by condition')
    parser.add_argument('--data-dir', type=str, default="data",
                        help='Base directory to save crawled data (default: "data")')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug logging')
    args = parser.parse_args()

    log_level = logging.DEBUG if args.debug else logging.INFO

    crawler = EbayCrawler(store_name=args.store, data_dir=args.data_dir, log_level=log_level)
    asyncio.run(crawler.crawl(condition_filter=args.condition))


if __name__ == "__main__":
    main()