from abc import ABC, abstractmethod
import re
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

    def _parse_instructions_into_steps(self, instructions_text: str) -> list[str]:
        """Parse instructions into individual steps, removing blog content and noise."""
        if not instructions_text:
            return []

        text = instructions_text

        # Remove common blog/content sections that come AFTER the recipe
        # These patterns detect where the recipe instructions END
        end_markers = [
            r'(?:Notes?|Note:|Tip:|Tips?:|Variations?|Variation:|Storage:|Storing|Freezer|Can you|No Artificial Intelligence|Every recipe|If it\'s on|Serve.*with|What to|Nutrition|Calories|Protein|Fat|Thank you|Tried this|Please Note|Nutrition information).*',
            r'Print.*Recipe.*',
            r'Pin.*Recipe.*',
            r'Prep Time.*Cook Time.*',
            r'Servings.*Calories.*',
            r'Equipment.*',
            r'Share this:.*',
            r'Email.*Print.*',
            r'Tweet.*Like.*',
        ]

        for pattern in end_markers:
            # Find the match
            match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
            if match:
                # Truncate at the start of the match
                text = text[:match.start()]

        text = text.strip()

        # Also strip trailing noise patterns that might remain
        text = re.sub(r'\s+(No ratings yet|Loading\.\.\.).*', '', text, flags=re.IGNORECASE | re.DOTALL)
        text = re.sub(r'\s+Related\s*$', '', text, flags=re.IGNORECASE)

        # First, try to parse already-numbered steps (1. 2. 3. format)
        numbered_pattern = r'^\d+[\.\)]\s*'
        if re.search(numbered_pattern, text, re.MULTILINE):
            # Already has numbered steps - preserve the structure
            steps = re.split(r'^\d+[\.\)]\s*', text, flags=re.MULTILINE)
            steps = [s.strip() for s in steps if s.strip() and len(s.strip()) > 5]
            return steps

        # Otherwise, split by semicolons (strong delimiter for run-on instructions)
        if ';' in text:
            steps = text.split(';')
            steps = [s.strip() for s in steps if s.strip()]

            final_steps = []
            for step in steps:
                # Skip very short fragments (likely noise)
                if len(step) < 5:
                    continue

                # If step is too long, try to break it up by sentence
                if len(step) > 200 and '.' in step:
                    sentences = re.split(r'(?<=[.!?])\s+', step)
                    current = ""
                    for sent in sentences:
                        sent = sent.strip()
                        if not sent:
                            continue
                        # Group sentences into reasonable step size (100-200 chars)
                        if len(current) + len(sent) < 180:
                            current += (" " + sent) if current else sent
                        else:
                            if current and len(current) > 10:
                                final_steps.append(current)
                            current = sent
                    if current and len(current) > 10:
                        final_steps.append(current)
                else:
                    final_steps.append(step)

            return final_steps if final_steps else [text]

        # Fall back to splitting by periods/sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        steps = []
        current = ""

        for sent in sentences:
            sent = sent.strip()
            if not sent or len(sent) < 5:
                continue

            # Group 1-2 sentences per step
            if len(current) + len(sent) < 180:
                current += (" " + sent) if current else sent
            else:
                if current:
                    steps.append(current)
                current = sent

        if current:
            steps.append(current)

        # Filter out very short steps
        steps = [s for s in steps if len(s.strip()) > 10]
        return steps if steps else []

    def _is_valid_recipe(self, name: str, ingredients: list, instructions: str) -> tuple[bool, str]:
        """Check if parsed content is a real recipe or just generic content.

        Returns (is_valid, reason) tuple.
        """
        # Check if title contains generic/non-recipe keywords
        generic_keywords = [
            "guide", "tips", "how to", "how-to", "roundup", "round-up",
            "tutorial", "beginner", "faq", "substitut", "comparison",
            "storage", "storing", "nutrition", "calorie", "recipes"
        ]
        name_lower = name.lower()
        for keyword in generic_keywords:
            if keyword in name_lower:
                return False, f"Generic content ({keyword})"

        # Check minimum ingredients (real recipes have at least 3)
        ingredient_count = len([ing for ing in ingredients if ing.get("name", "").strip()])
        if ingredient_count < 3:
            return False, f"Too few ingredients ({ingredient_count})"

        # Check minimum instruction length (real recipes have substantial instructions)
        if not instructions or len(instructions.strip()) < 50:
            return False, "Instructions too short or missing"

        return True, "Valid recipe"

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
                raw_ingredients_list = raw.get("raw_ingredients", [])
                raw_ingredients_text = "\n".join(raw_ingredients_list) if raw_ingredients_list else None
                ingredients = parse_ingredients(raw_ingredients_list)
                instructions = normalize_instructions(raw.get("instructions", ""))
                image_url = raw.get("image_url")
                pub_date = parse_date(raw.get("publication_date") or url)

                # Validate that this is a real recipe, not generic content
                is_valid, reason = self._is_valid_recipe(name, ingredients, instructions)
                if not is_valid:
                    self.logger.info(f"SKIP ({reason}): {name}")
                    summary["skipped"] += 1
                    continue

                if dry_run:
                    self._print_recipe(
                        name, category_str, tags, ingredients, instructions,
                        image_url, pub_date, url
                    )
                    summary["inserted"] += 1
                    continue

                cat_id = db.get_or_create_category(cursor, category_str)
                recipe_id = db.insert_recipe(
                    cursor, name, cat_id, instructions, image_url, pub_date, raw_ingredients_text
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

                # Insert instruction steps
                instruction_steps = self._parse_instructions_into_steps(instructions)
                for step_number, step_text in enumerate(instruction_steps, 1):
                    if step_text.strip():
                        db.insert_recipe_instruction(cursor, recipe_id, step_number, step_text)

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
