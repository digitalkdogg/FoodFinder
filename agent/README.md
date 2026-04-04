# Alpha-Gal Recipe Scraper

A driver-based web scraper for collecting Alpha-Gal diet recipes from multiple recipe blogs and storing them in a MySQL database with normalized ingredients, categories, and tags.

## Features

- **Configuration-driven**: Add new sites with just 15 lines of YAML (no Python code needed)
- **Multiple drivers**: WordPress (and WordPress.com) and Blogspot platforms
- **WPRM plugin support**: Automatic structured recipe parsing when WordPress Recipe Maker is detected
- **Smart fallback**: Verb-based heuristic for extracting ingredients/instructions from standard blog posts
- **Duplicate detection**: Prevents re-scraping via source URL tracking
- **Polite scraping**: Configurable delays, 429 handling, proper User-Agent headers
- **Comprehensive logging**: Both stdout and `scraper.log` file

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## Configuration

All site configuration lives in `config/sites.yaml`. To add a new site, add an entry:

```yaml
sites:
  - id: newsite
    enabled: true
    site_name: "New Site Name"
    base_url: "https://newsite.com"
    driver: wordpress
    index_url: "https://newsite.com/recipes/"
    index_strategy: category_pages  # or: index_page
    delay_seconds: 2
    wprm: false  # Set to true if site uses WordPress Recipe Maker
```

Override any CSS selectors at the site level:

```yaml
    title_selector: "h1.recipe-title"  # Custom selector for this site only
```

## Usage

```bash
# Scrape all enabled sites
python -m scraper.main

# Scrape only one site
python -m scraper.main --site alphagalcooking

# Dry-run (print recipes without writing to DB)
python -m scraper.main --dry-run --limit 5

# Limit recipes per site
python -m scraper.main --limit 10

# Combine flags
python -m scraper.main --dry-run --site alphagaldiet_blogspot --limit 3
```

## Database Schema

The scraper populates:
- `recipes` - Recipe names, categories, instructions, images, publication dates
- `sources` - Information about scraping sites
- `recipe_sources` - Links recipes to their original URLs
- `recipe_tags` - Associative table for recipe tags (allergies, dietary info)
- `recipe_ingredients` - Detailed ingredients with quantities and units
- `categories`, `tags`, `ingredients` - Reference tables

## Current Sites

| Site | Platform | Status | Strategy |
|------|----------|--------|----------|
| Alpha-Gal Cooking | WordPress.com | ✅ | Index page |
| The Alpha Gal Allergy Cooking | WordPress.com | ⚠️ | Index page |
| Alpha Gal Diet (Blogspot) | Blogspot | ✅ | Paginated feed |
| Feathers and Fins | WordPress | ⚠️ | Category pages |
| Sage Alpha Gal | WordPress | ✅ | Category pages |
| The Alpha Gal Diet | WordPress | ❌ (disabled - slow) | Category pages |

## Data Normalization

### Categories
All raw categories are normalized to a controlled vocabulary:
- Poultry, Pasta, Soups, Beans, Salads & Sandwiches, Desserts
- Breads & Muffins, Vegetables, Eggs & Cheese, Rice & Grains
- Fish & Seafood, Appetizers, Sides, Breakfast, Dinner, Holidays, Uncategorized

### Tags
Tags are lowercased, deduplicated, and normalized (e.g., "treenut free" → "tree nut free")

### Ingredients
- Handles Unicode fractions (½, ¼, ¾, ⅓, ⅔)
- Parses quantities and units
- Normalizes units to singular abbreviations (tbsp, tsp, cup, lb, oz, etc.)
- Extracts notes (e.g., "finely chopped")

### Instructions
- Strips HTML tags
- Removes excess blank lines
- Handles both structured (WPRM) and free-form text

## Logging

All activity is logged to:
- **stdout** for real-time monitoring
- **scraper.log** for permanent record

Log entries include timestamps, site IDs, and detailed error messages with tracebacks.

## Common Issues

**"Lock wait timeout" errors**
- DB transaction was too long. The scraper now commits after each recipe.
- If still occurs: wait a minute for locks to clear, then retry.

**"404 on {url}, skipping"**
- Site structure changed or URL is invalid. Check the site manually and update config.

**No recipes found**
- Verify the site's HTML structure matches the CSS selectors in config/sites.yaml
- Run a dry-run with debug logging to see which URLs are being discovered

**Slow performance**
- Increase `delay_seconds` in config (currently 2-3s to be polite)
- Some sites may be slow; disable if scraping takes too long

## Architecture

```
scraper/
├── main.py              # Entry point, CLI, config loading
├── db.py                # Database layer (insert, check for duplicates, etc.)
├── normalizer.py        # Data cleaning, normalization, parsing
├── base_driver.py       # Abstract base with common scraping logic
└── drivers/
    ├── wordpress.py     # WordPress/WordPress.com driver
    └── blogspot.py      # Blogspot driver
```

## Adding a Custom Driver

Create a new file in `scraper/drivers/`:

```python
from scraper.base_driver import BaseDriver

class CustomDriver(BaseDriver):
    def get_recipe_urls(self) -> list:
        # Return list of recipe URLs to scrape
        pass
    
    def parse_recipe(self, url: str, soup) -> dict:
        # Return dict with: name, category, tags, raw_ingredients, 
        # instructions, image_url, publication_date
        pass
```

Register in `scraper/main.py`:

```python
driver_map = {
    "wordpress": WordPressDriver,
    "blogspot": BlogspotDriver,
    "custom": CustomDriver,
}
```

Then add sites using `driver: custom` in `sites.yaml`.

## Statistics

Current database state:
- 98 recipes inserted
- 5 recipe sources configured
- 10 normalized categories
- 399 unique ingredients
- Automatic deduplication prevents re-scraping

## Future Enhancements

- [ ] Resume capability (track last-scraped date per site)
- [ ] Recipe photo downloads
- [ ] Export to JSON/CSV
- [ ] Web UI for browsing recipes
- [ ] Support for additional recipe platforms
