#!/usr/bin/env python3
"""Update recipe_instructions table by parsing raw_instructions for all recipes."""

import re
import logging
from scraper import db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_instructions_into_steps(instructions_text: str) -> list[str]:
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


def main():
    db_conn = db.get_connection()
    cursor = db_conn.cursor()

    try:
        # Get all recipes with instructions (use instructions column which has the data)
        cursor.execute("SELECT id, instructions FROM recipes WHERE instructions IS NOT NULL AND instructions != ''")
        recipes = cursor.fetchall()
        logger.info(f"Found {len(recipes)} recipes with instructions")

        updated = 0
        for recipe_id, instructions_text in recipes:
            steps = parse_instructions_into_steps(instructions_text)

            if steps:
                for step_number, step_text in enumerate(steps, 1):
                    if step_text.strip():
                        db.insert_recipe_instruction(cursor, recipe_id, step_number, step_text)
                db_conn.commit()
                updated += 1

                if updated % 20 == 0:
                    logger.info(f"Updated {updated} recipes...")

        logger.info(f"✓ Successfully updated {updated} recipes with parsed instructions")
        cursor.close()

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        db_conn.rollback()
    finally:
        db_conn.close()


if __name__ == "__main__":
    main()
