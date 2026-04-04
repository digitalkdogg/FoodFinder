import logging
from urllib.parse import urljoin, urlparse
from scraper.base_driver import BaseDriver


class WordPressDriver(BaseDriver):
    """Handles WordPress and WordPress.com sites."""

    def get_recipe_urls(self) -> list:
        """Get list of recipe URLs based on index strategy."""
        strategy = self.config.get("index_strategy", "index_page")

        if strategy == "index_page":
            return self._get_from_index_page()
        elif strategy == "category_pages":
            return self._get_from_category_pages()
        else:
            self.logger.error(f"Unknown index strategy: {strategy}")
            return []

    def _get_from_index_page(self) -> list:
        """Get recipe URLs from a single index page."""
        urls = set()
        soup = self.fetch(self.config["index_url"])
        if not soup:
            return []

        links = soup.select(self.sel("index_link_selector"))
        filter_str = self.config.get("index_link_filter", "")

        for link in links:
            href = link.get("href", "")
            if not href:
                continue
            if filter_str and filter_str not in href:
                continue
            full_url = urljoin(self.config["base_url"], href)
            urls.add(full_url)

        return list(urls)

    def _get_from_category_pages(self) -> list:
        """Get recipe URLs from paginated category pages."""
        urls = set()
        current_url = self.config["index_url"]

        while current_url:
            soup = self.fetch(current_url)
            if not soup:
                break

            # Find post links
            links = soup.select(self.sel("archive_post_link_selector"))
            for link in links:
                href = link.get("href", "")
                if href:
                    full_url = urljoin(self.config["base_url"], href)
                    urls.add(full_url)

            # Find next page link
            next_link = soup.select_one(self.sel("next_page_selector"))
            if next_link:
                next_href = next_link.get("href", "")
                if next_href:
                    current_url = urljoin(self.config["base_url"], next_href)
                else:
                    break
            else:
                break

        return list(urls)

    def parse_recipe(self, url: str, soup) -> dict:
        """Parse a WordPress recipe page."""
        result = {
            "name": "",
            "category": "",
            "tags": [],
            "raw_ingredients": [],
            "instructions": "",
            "image_url": None,
            "publication_date": None,
            "source_url": url,
        }

        # Extract title
        title_elem = soup.select_one(self.sel("title_selector"))
        if title_elem:
            result["name"] = title_elem.get_text(strip=True)

        # Extract category (first element only)
        category_elems = soup.select(self.sel("category_selector"))
        if category_elems:
            result["category"] = category_elems[0].get_text(strip=True)

        # Extract tags (all elements)
        tag_elems = soup.select(self.sel("tag_selector"))
        result["tags"] = [elem.get_text(strip=True) for elem in tag_elems]

        # Extract image URL
        og_image = soup.select_one("meta[property='og:image']")
        if og_image:
            result["image_url"] = og_image.get("content")
        else:
            # Fallback: first img in body
            body = soup.select_one(self.sel("body_selector"))
            if body:
                img = body.find("img")
                if img:
                    result["image_url"] = img.get("src")

        # Extract publication date
        date_elem = soup.select_one(self.sel("date_selector"))
        if date_elem:
            if date_elem.name == "time":
                result["publication_date"] = date_elem.get("datetime")
            else:
                result["publication_date"] = date_elem.get_text(strip=True)

        # Extract ingredients and instructions
        wprm = self.config.get("wprm", False)
        if wprm:
            self._parse_wprm_recipe(soup, result)
        else:
            self._parse_standard_recipe(soup, result)

        return result

    def _parse_wprm_recipe(self, soup, result: dict):
        """Parse using WordPress Recipe Maker plugin."""
        from scraper.normalizer import split_ingredients_instructions

        # Check if WPRM container exists
        if not soup.select_one("div.wprm-recipe-container"):
            self.logger.warning(f"WPRM container not found, falling back to heuristic")
            self._parse_standard_recipe(soup, result)
            return

        # Extract ingredients
        ing_elements = soup.select(self.sel("wprm_ingredient_selector"))
        ingredients = []
        for ing_elem in ing_elements:
            ing_text = ing_elem.get_text(strip=True)
            if ing_text:
                ingredients.append(ing_text)
        result["raw_ingredients"] = ingredients

        # Extract instructions
        inst_elements = soup.select(self.sel("wprm_instruction_selector"))
        instructions = []
        for inst_elem in inst_elements:
            inst_text = inst_elem.get_text(strip=True)
            if inst_text:
                instructions.append(inst_text)
        result["instructions"] = "\n".join(instructions)

    def _parse_standard_recipe(self, soup, result: dict):
        """Parse using body text heuristic (no recipe plugin)."""
        from scraper.normalizer import split_ingredients_instructions

        body_elem = soup.select_one(self.sel("body_selector"))
        if not body_elem:
            return

        body_text = body_elem.get_text(separator="\n")
        trigger_verbs = self.config.get("instruction_trigger_verbs", [])
        ing_lines, inst_text = split_ingredients_instructions(body_text, trigger_verbs)
        result["raw_ingredients"] = ing_lines
        result["instructions"] = inst_text
