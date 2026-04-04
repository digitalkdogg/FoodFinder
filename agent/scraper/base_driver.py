from abc import ABC, abstractmethod
import requests
import time
import logging
from bs4 import BeautifulSoup


class BaseDriver(ABC):
    """Abstract base class for recipe scrapers."""

    def __init__(self, config: dict, db_conn):
        self.config = config
        self.db_conn = db_conn
        self.delay = config.get("delay_seconds", 2)
        self.logger = logging.getLogger(config["id"])
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; AlphaGalRecipeBot/1.0)"
        })

    def fetch(self, url: str):
        """Fetch a URL and return BeautifulSoup object."""
        time.sleep(self.delay)
        try:
            r = self.session.get(url, timeout=15)
            if r.status_code == 429:
                self.logger.warning(f"429 on {url}, sleeping 60s then retrying")
                time.sleep(60)
                r = self.session.get(url, timeout=15)
            if r.status_code == 404:
                self.logger.warning(f"404 on {url}, skipping")
                return None
            r.raise_for_status()
            return BeautifulSoup(r.text, "lxml")
        except Exception as e:
            self.logger.error(f"fetch failed for {url}: {e}")
            return None

    def sel(self, key: str) -> str:
        """Get a CSS selector from the merged config."""
        return self.config.get(key, "")

    @abstractmethod
    def get_recipe_urls(self) -> list:
        """Return list of recipe URLs to scrape."""
        pass

    @abstractmethod
    def parse_recipe(self, url: str, soup):
        """Parse a recipe page and return raw recipe dict."""
        pass

    def run(self, dry_run=False, limit=None) -> dict:
        """Main execution method."""
        from scraper import db
        from scraper.normalizer import (
            normalize_recipe_name, normalize_category, normalize_tag,
            parse_ingredients, normalize_instructions, parse_date,
            split_ingredients_instructions
        )

        summary = {"found": 0, "inserted": 0, "skipped": 0, "errors": 0}

        # Get all recipe URLs first (before transaction)
        urls = self.get_recipe_urls()
        summary["found"] = len(urls)
        if limit:
            urls = urls[:limit]

        # Now get cursor and source after URL discovery
        cursor = self.db_conn.cursor()
        source_id = db.get_or_create_source(
            cursor, self.config["site_name"], self.config["base_url"]
        )
        self.db_conn.commit()

        for url in urls:
            try:
                if not dry_run and db.recipe_exists(cursor, url):
                    self.logger.info(f"SKIP (exists): {url}")
                    summary["skipped"] += 1
                    continue

                soup = self.fetch(url)
                if soup is None:
                    summary["errors"] += 1
                    continue

                raw = self.parse_recipe(url, soup)
                if not raw or not raw.get("name"):
                    self.logger.warning(f"No recipe parsed from {url}")
                    summary["errors"] += 1
                    continue

                name = normalize_recipe_name(raw["name"])
                category_str = normalize_category(raw.get("category", ""))
                tags = list(set(normalize_tag(t) for t in raw.get("tags", []) if t))
                ingredients = parse_ingredients(raw.get("raw_ingredients", []))
                instructions = normalize_instructions(raw.get("instructions", ""))
                image_url = raw.get("image_url")
                pub_date = parse_date(raw.get("publication_date") or url)

                if dry_run:
                    self._print_recipe(
                        name, category_str, tags, ingredients, instructions,
                        image_url, pub_date, url
                    )
                    summary["inserted"] += 1
                    continue

                cat_id = db.get_or_create_category(cursor, category_str)
                recipe_id = db.insert_recipe(
                    cursor, name, cat_id, instructions, image_url, pub_date
                )

                for tag_str in tags:
                    tag_id = db.get_or_create_tag(cursor, tag_str)
                    db.link_recipe_tag(cursor, recipe_id, tag_id)

                for ing in ingredients:
                    # Skip ingredients with empty names
                    if not ing.get("name", "").strip():
                        continue
                    ing_id = db.get_or_create_ingredient(cursor, ing["name"])
                    if ing_id:
                        db.insert_recipe_ingredient(
                            cursor, recipe_id, ing_id,
                            ing["quantity"], ing["unit"], ing["notes"]
                        )

                db.insert_recipe_source(cursor, recipe_id, source_id, url)
                self.db_conn.commit()
                summary["inserted"] += 1
                self.logger.info(f"INSERTED: {name}")

            except Exception as e:
                self.logger.error(f"Error on {url}: {e}", exc_info=True)
                try:
                    self.db_conn.rollback()
                except:
                    pass
                summary["errors"] += 1

        cursor.close()
        return summary

    def _print_recipe(self, name, category, tags, ingredients, instructions, image_url, pub_date, url):
        """Print recipe for dry-run."""
        print(f"\n--- Recipe ---")
        print(f"Name:     {name}")
        print(f"Category: {category}")
        print(f"Tags:     {', '.join(tags)}")
        print(f"Image:    {image_url}")
        print(f"Date:     {pub_date}")
        print(f"URL:      {url}")
        print(f"Ingredients:")
        for i in ingredients:
            notes = f" [notes: {i['notes']}]" if i["notes"] else ""
            ing_str = f"  {i['quantity']} {i['unit']} {i['name']}{notes}".strip()
            print(ing_str)
        print(f"Instructions (first 200 chars):")
        print(f"  {instructions[:200]}...")
        print(f"--------------")
