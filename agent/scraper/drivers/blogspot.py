import logging
from urllib.parse import urljoin, urlparse
from scraper.base_driver import BaseDriver


class BlogspotDriver(BaseDriver):
    """Handles all Blogspot sites."""

    def get_recipe_urls(self) -> list:
        """Get recipe URLs from paginated Blogspot feed."""
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
                    # Keep only URLs from the base domain that look like posts (contain /YYYY/)
                    if self._is_valid_post_url(full_url):
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

    def _is_valid_post_url(self, url: str) -> bool:
        """Check if URL is a valid post URL (contains year pattern)."""
        base_domain = urlparse(self.config["base_url"]).netloc
        url_domain = urlparse(url).netloc
        if url_domain != base_domain:
            return False
        if "/20" not in url:  # Basic check for year in URL
            return False
        return True

    def parse_recipe(self, url: str, soup) -> dict:
        """Parse a Blogspot recipe page."""
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

        # Extract category and tags from labels
        label_elems = soup.select(self.sel("category_selector"))
        if label_elems:
            # First label = category, rest = tags
            result["category"] = label_elems[0].get_text(strip=True)
            result["tags"] = [elem.get_text(strip=True) for elem in label_elems[1:]]

        # Extract image URL
        image_skip_pattern = self.config.get("image_src_skip_pattern", "")
        img_elems = soup.select(self.sel("image_selector"))
        for img in img_elems:
            src = img.get("src", "")
            if src and (not image_skip_pattern or image_skip_pattern not in src):
                result["image_url"] = src
                break

        # Extract publication date
        date_elem = soup.select_one(self.sel("date_selector"))
        if date_elem:
            if date_elem.name == "abbr":
                result["publication_date"] = date_elem.get("title")
            else:
                result["publication_date"] = date_elem.get_text(strip=True)

        # Extract ingredients and instructions (no recipe plugins on Blogspot)
        self._parse_standard_recipe(soup, result)

        return result

    def _parse_standard_recipe(self, soup, result: dict):
        """Parse using body text heuristic."""
        from scraper.normalizer import split_ingredients_instructions

        body_elem = soup.select_one(self.sel("body_selector"))
        if not body_elem:
            return

        body_text = body_elem.get_text(separator="\n")
        trigger_verbs = self.config.get("instruction_trigger_verbs", [])
        ing_lines, inst_text = split_ingredients_instructions(body_text, trigger_verbs)
        result["raw_ingredients"] = ing_lines
        result["instructions"] = inst_text
