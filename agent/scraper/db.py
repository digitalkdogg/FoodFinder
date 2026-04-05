import os
import logging
import pymysql
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
load_dotenv(dotenv_path=env_path)

logger = logging.getLogger(__name__)


def get_connection():
    """Create and return a database connection."""
    conn = pymysql.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        autocommit=False,
    )
    return conn


def get_or_create_category(cursor, name: str) -> int:
    """Insert or get category ID."""
    cursor.execute("INSERT IGNORE INTO categories (name) VALUES (%s)", (name,))
    cursor.execute("SELECT id FROM categories WHERE name = %s", (name,))
    result = cursor.fetchone()
    return result[0] if result else None


def get_or_create_tag(cursor, name: str) -> int:
    """Insert or get tag ID."""
    cursor.execute("INSERT IGNORE INTO tags (name) VALUES (%s)", (name,))
    cursor.execute("SELECT id FROM tags WHERE name = %s", (name,))
    result = cursor.fetchone()
    return result[0] if result else None


def get_or_create_ingredient(cursor, name: str) -> int:
    """Insert or get ingredient ID."""
    cursor.execute("INSERT IGNORE INTO ingredients (name) VALUES (%s)", (name,))
    cursor.execute("SELECT id FROM ingredients WHERE name = %s", (name,))
    result = cursor.fetchone()
    return result[0] if result else None


def get_or_create_source(cursor, site_name: str, base_url: str) -> int:
    """Insert or get source ID."""
    cursor.execute("INSERT IGNORE INTO sources (site_name, base_url) VALUES (%s, %s)", (site_name, base_url))
    cursor.execute("SELECT id FROM sources WHERE base_url = %s", (base_url,))
    result = cursor.fetchone()
    return result[0] if result else None


def recipe_exists(cursor, source_url: str) -> bool:
    """Check if recipe with given source URL already exists."""
    cursor.execute("SELECT 1 FROM recipe_sources WHERE source_url = %s", (source_url,))
    return cursor.fetchone() is not None


def insert_recipe(cursor, name: str, category_id: int, instructions: str,
                  image_url: str, publication_date: str, raw_ingredients: str = None) -> int:
    """Insert recipe and return recipe ID."""
    cursor.execute(
        """INSERT INTO recipes (name, category_id, instructions, image_url, publication_date, raw_ingredients)
           VALUES (%s, %s, %s, %s, %s, %s)""",
        (name, category_id, instructions, image_url, publication_date, raw_ingredients)
    )
    return cursor.lastrowid


def link_recipe_tag(cursor, recipe_id: int, tag_id: int):
    """Link a recipe to a tag."""
    cursor.execute(
        "INSERT IGNORE INTO recipe_tags (recipe_id, tag_id) VALUES (%s, %s)",
        (recipe_id, tag_id)
    )


def insert_recipe_ingredient(cursor, recipe_id: int, ingredient_id: int,
                             quantity: str, unit: str, notes: str):
    """Insert recipe ingredient."""
    cursor.execute(
        """INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity, unit, notes)
           VALUES (%s, %s, %s, %s, %s)""",
        (recipe_id, ingredient_id, quantity, unit, notes)
    )


def insert_recipe_instruction(cursor, recipe_id: int, step_number: int, instruction_text: str):
    """Insert recipe instruction step."""
    cursor.execute(
        """INSERT INTO recipe_instructions (recipe_id, step_number, instruction_text)
           VALUES (%s, %s, %s)""",
        (recipe_id, step_number, instruction_text)
    )


def insert_recipe_source(cursor, recipe_id: int, source_id: int, source_url: str):
    """Link recipe to source."""
    cursor.execute(
        "INSERT IGNORE INTO recipe_sources (recipe_id, source_id, source_url) VALUES (%s, %s, %s)",
        (recipe_id, source_id, source_url)
    )
