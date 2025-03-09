# eBay Store Crawler

A flexible Python crawler designed to extract product listings from any eBay store. Originally designed for "garlandcomputer" but now supports any eBay store with organized data storage and comprehensive logging.

## Features

- **Store-Specific Organization**: Crawls any eBay store with data organized in store-specific folders
- **Comprehensive Data Extraction**: Extracts title, price, condition, and product URL for each item
- **Structured Data Storage**: Saves data as JSON files named by item ID in store-specific directories
- **Advanced Logging**: Detailed logging with both console and file output for better tracking
- **Asynchronous Processing**: Uses asyncio for concurrent file writing and improved performance
- **Condition Filtering**: Filter items by condition (e.g., "New", "Pre-Owned", "Used")

## Requirements

- Python 3.7 or higher
- Required Python packages:
  - `requests`: For HTTP requests
  - `beautifulsoup4`: For HTML parsing
  - `aiofiles`: For asynchronous file operations

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/MlataIbrahim/ebay_scraper
   cd ebay_scraper
   ```

2. Install the required dependencies:
   ```bash
   pip install requests beautifulsoup4 aiofiles
   ```

## Usage

### Command Line Interface

The crawler can be configured via command line arguments:

```bash
python ebay_crawler.py [--store STORE_NAME] [--condition CONDITION] [--data-dir DATA_DIR] [--debug]
```

Arguments:
- `--store`: eBay store name to crawl (default: "garlandcomputer")
- `--condition`: Filter items by condition (choices: "New", "Pre-Owned", "Used")
- `--data-dir`: Base directory for saved data (default: "data")
- `--debug`: Enable more detailed debug logging

### Examples

Crawl the default store (garlandcomputer):
```bash
python ebay_crawler.py
```

Crawl a different store:
```bash
python ebay_crawler.py --store thecomputershed
```

Filter items by condition:
```bash
python ebay_crawler.py --store garlandcomputer --condition New
```

Enable debug logging:
```bash
python ebay_crawler.py --debug
```

### Using as a Module

The crawler can also be imported and used in other Python scripts:

```python
import asyncio
from ebay_crawler import EbayCrawler

async def main():
    crawler = EbayCrawler(store_name="garlandcomputer")
    
    pages, items = await crawler.crawl(condition_filter="New")
    
    print(f"Crawled {pages} pages and extracted {items} items")

if __name__ == "__main__":
    asyncio.run(main())
```

## Data Organization

The crawler creates the following directory structure:
```
data/
  ├── store1/
  │     ├── item1.json
  │     ├── item2.json
  │     └── ...
  ├── store2/
  │     ├── item1.json
  │     └── ...
  └── ...
logs/
  ├── store1_YYYYMMDD_HHMMSS.log
  ├── store2_YYYYMMDD_HHMMSS.log
  └── ...
```

### Example Output

For an item with ID `234908325972` from the "garlandcomputer" store, the generated file (`data/garlandcomputer/234908325972.json`) will look like this:

```json
{
    "title": "Dell PowerEdge R710 Server 2x X5660 2.80GHz 12-Core / 64gb / 2xtrays / Perc6i",
    "condition": "Pre-Owned",
    "price": "199.99",
    "product_url": "https://www.ebay.com/itm/294294157222?hash=item448d374e16:g:fbA0dSWCibJ"
}
```

## Logging

Comprehensive logging is available with different verbosity levels:
- **INFO** (default): Records basic progress information
- **DEBUG** (with `--debug` flag): Records detailed information including item parsing

Log files are stored in the `logs/` directory with timestamp and store name for easy identification.
