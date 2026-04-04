import re
from bs4 import BeautifulSoup

CATEGORY_MAP = {
    "poultry": "Poultry",
    "chicken": "Poultry",
    "turkey": "Poultry",
    "pasta": "Pasta",
    "bean recipes": "Beans",
    "beans": "Beans",
    "soups": "Soups",
    "soup": "Soups",
    "salads & sandwiches": "Salads & Sandwiches",
    "salads": "Salads & Sandwiches",
    "desserts": "Desserts",
    "dessert": "Desserts",
    "breads & muffins": "Breads & Muffins",
    "breads": "Breads & Muffins",
    "vegetables": "Vegetables",
    "vegetable": "Vegetables",
    "eggs & cheese": "Eggs & Cheese",
    "rice recipes": "Rice & Grains",
    "rice & grains": "Rice & Grains",
    "fish": "Fish & Seafood",
    "seafood": "Fish & Seafood",
    "appetizers": "Appetizers",
    "appetizer": "Appetizers",
    "side dishes": "Sides",
    "sides": "Sides",
    "breakfast": "Breakfast",
    "dinner": "Dinner",
    "holidays": "Holidays",
}

TAG_ALIASES = {
    "treenut free": "tree nut free",
    "treenut-free": "tree nut free",
    "soy free": "soybean free",
    "nut free": "tree nut free",
    "dairy free": "dairy free",
    "gluten free": "gluten free",
}

UNITS = [
    "cup", "cups", "tbsp", "tablespoon", "tablespoons",
    "tsp", "teaspoon", "teaspoons", "pound", "pounds",
    "lb", "lbs", "oz", "ounce", "ounces", "clove", "cloves",
    "medium", "large", "small", "can", "cans", "package",
    "pkg", "slice", "slices", "bunch", "pinch", "dash",
    "quart", "pint", "gallon", "liter", "ml", "gram", "g",
]

UNIT_NORMALIZE = {
    "cups": "cup", "tablespoons": "tablespoon", "tablespoon": "tbsp",
    "teaspoons": "teaspoon", "teaspoon": "tsp",
    "pounds": "lb", "pound": "lb", "lbs": "lb",
    "ounces": "oz", "ounce": "oz",
    "cloves": "clove", "cans": "can", "slices": "slice",
}

FRACTION_MAP = {"½": "1/2", "¼": "1/4", "¾": "3/4", "⅓": "1/3", "⅔": "2/3"}

SITE_NAME_KEYWORDS = [
    "Alpha-Gal Cooking", "Alpha Gal Diet", "Feathers and Fins",
    "Sage Alpha Gal", "The Alpha Gal Allergy Cooking", "The Alpha Gal Diet"
]


def normalize_recipe_name(raw: str) -> str:
    """Normalize recipe name: strip site suffixes and title-case."""
    name = raw.strip()

    # Remove site name suffixes: anything after | or - if what follows is a known site name
    for sep in ["|", "-"]:
        if sep in name:
            parts = name.split(sep)
            suffix = parts[-1].strip()
            # Check if suffix looks like a site name
            if any(keyword.lower() in suffix.lower() for keyword in SITE_NAME_KEYWORDS):
                name = parts[0].strip()

    # Title case
    return name.title()


def normalize_category(raw: str) -> str:
    """Normalize category using controlled vocabulary."""
    if not raw:
        return "Uncategorized"

    key = raw.lower().strip()
    return CATEGORY_MAP.get(key, "Uncategorized")


def normalize_tag(raw: str) -> str:
    """Normalize tag: lowercase, replace hyphens, apply aliases."""
    if not raw:
        return ""

    cleaned = raw.lower().strip().replace("-", " ")
    return TAG_ALIASES.get(cleaned, cleaned)


def parse_ingredients(raw_lines: list[str]) -> list[dict]:
    """Parse ingredient lines into structured dicts."""
    ingredients = []

    for line in raw_lines:
        if not line.strip():
            continue

        # Replace Unicode fractions
        for unicode_frac, text_frac in FRACTION_MAP.items():
            line = line.replace(unicode_frac, text_frac)

        # Strip HTML tags
        soup = BeautifulSoup(line, "html.parser")
        line = soup.get_text(strip=True)

        if not line:
            continue

        ing_dict = {
            "quantity": "",
            "unit": "",
            "name": line,
            "notes": ""
        }

        # Try to extract quantity
        qty_match = re.match(r"^(\d+\s+\d+/\d+|\d+/\d+|\d+\.?\d*)\s+", line)
        if qty_match:
            ing_dict["quantity"] = qty_match.group(1)
            remainder = line[qty_match.end():]

            # Try to match a unit
            words = remainder.split()
            if words:
                first_word = words[0].lower()
                if first_word in UNITS:
                    ing_dict["unit"] = UNIT_NORMALIZE.get(first_word, first_word)
                    remainder = " ".join(words[1:])

            # Split on first comma for notes
            if "," in remainder:
                name_part, notes_part = remainder.split(",", 1)
                ing_dict["name"] = name_part.strip().lower()
                ing_dict["notes"] = notes_part.strip()
            else:
                ing_dict["name"] = remainder.strip().lower()

        # Only add if name is not empty
        if ing_dict["name"].strip():
            ingredients.append(ing_dict)

    return ingredients


def normalize_instructions(raw: str) -> str:
    """Normalize instructions: strip HTML, collapse extra newlines."""
    if not raw:
        return ""

    soup = BeautifulSoup(raw, "html.parser")
    text = soup.get_text(separator="\n")

    # Collapse 3+ consecutive newlines to 2
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def parse_date(raw: str) -> str:
    """Parse date from various formats, or extract from URL."""
    if not raw:
        return None

    import datetime

    # Try common date formats
    formats = [
        "%B %d, %Y",           # "March 07, 2014"
        "%Y-%m-%dT%H:%M:%S",   # ISO format
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%d %B %Y"
    ]

    for fmt in formats:
        try:
            dt = datetime.datetime.strptime(raw, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue

    # Try to extract from URL: (\d{4}/\d{2}/\d{2})
    url_date_match = re.search(r"(\d{4})/(\d{2})/(\d{2})", raw)
    if url_date_match:
        return f"{url_date_match.group(1)}-{url_date_match.group(2)}-{url_date_match.group(3)}"

    return None


def split_ingredients_instructions(body_text: str, trigger_verbs: list[str]) -> tuple:
    """Split body text into ingredients and instructions based on verb triggers."""
    lines = [line.strip() for line in body_text.split("\n")]
    lines = [line for line in lines if line]  # Remove empty lines

    # Find the trigger verb line (start of instructions)
    trigger_line_idx = None
    for i, line in enumerate(lines):
        # Strip punctuation and check if starts with any trigger verb
        line_clean = re.sub(r"[^\w\s]", "", line)
        words = line_clean.split()
        if words and words[0].lower() in [v.lower() for v in trigger_verbs]:
            trigger_line_idx = i
            break

    if trigger_line_idx is None:
        # No trigger found; use a different heuristic
        # Filter to keep only lines that look like ingredients
        ingredient_lines = []
        for line in lines:
            # Include lines that start with quantity/unit or are short (likely ingredients)
            if (re.match(r"^[\d½¼¾⅓⅔]", line) or
                any(line.lower().startswith(unit) for unit in UNITS) or
                (len(line) <= 100 and re.search(r"\d", line) and len(line.split()) <= 10)):
                ingredient_lines.append(line)
        instructions_text = ""
    else:
        ingredient_candidates = lines[:trigger_line_idx]
        instructions_lines = lines[trigger_line_idx:]

        # Filter ingredient candidates more strictly
        ingredient_lines = []
        for line in ingredient_candidates:
            # Include if starts with digit/fraction/unit
            if (re.match(r"^[\d½¼¾⅓⅔]", line) or
                any(line.lower().startswith(unit) for unit in UNITS)):
                ingredient_lines.append(line)
            # Or short lines with digit and few words (likely ingredient)
            elif (len(line) <= 100 and re.search(r"\d", line) and
                  len(line.split()) <= 10 and len(line) > 5):
                ingredient_lines.append(line)

        instructions_text = "\n".join(instructions_lines)

    return ingredient_lines, instructions_text
