#!/usr/bin/env python3

import sys
import logging
import argparse
import yaml
from pathlib import Path

from scraper import db


# Configure logging
def setup_logging():
    """Configure logging to stdout and file."""
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    handlers = [
        logging.FileHandler("scraper.log"),
        logging.StreamHandler(sys.stdout),
    ]

    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=handlers,
    )


def build_site_config(site: dict, defaults: dict) -> dict:
    """Merge driver defaults with site-specific config."""
    platform = site.get("driver", "wordpress")
    platform_defaults = defaults.get(platform, {})
    merged = {**platform_defaults, **site}
    return merged


def load_config(config_path: str) -> tuple:
    """Load and parse sites.yaml."""
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    driver_defaults = config.get("driver_defaults", {})
    sites = config.get("sites", [])

    # Merge defaults into each site
    for site in sites:
        site.update(build_site_config(site, driver_defaults))

    return driver_defaults, sites


def get_driver_class(driver_name: str):
    """Dynamically import driver class."""
    if driver_name == "wordpress":
        from scraper.drivers.wordpress import WordPressDriver
        return WordPressDriver
    elif driver_name == "blogspot":
        from scraper.drivers.blogspot import BlogspotDriver
        return BlogspotDriver
    else:
        raise ValueError(f"Unknown driver: {driver_name}")


def main():
    parser = argparse.ArgumentParser(description="Alpha-Gal Recipe Scraper")
    parser.add_argument("--site", help="Run only this site ID")
    parser.add_argument("--dry-run", action="store_true", help="Parse but don't write to DB")
    parser.add_argument("--limit", type=int, help="Stop after N recipes per site")

    args = parser.parse_args()

    setup_logging()
    logger = logging.getLogger("main")

    # Find config file
    config_path = Path(__file__).parent.parent / "config" / "sites.yaml"
    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        sys.exit(1)

    logger.info(f"Loading config from {config_path}")
    driver_defaults, sites = load_config(config_path)

    # Connect to database
    try:
        db_conn = db.get_connection()
        logger.info("Connected to database")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        sys.exit(1)

    # Run scraper on each site
    total_summary = {"found": 0, "inserted": 0, "skipped": 0, "errors": 0}

    for site in sites:
        site_id = site.get("id")
        site_name = site.get("site_name")
        enabled = site.get("enabled", True)

        # Filter by --site if provided
        if args.site and site_id != args.site:
            continue

        if not enabled:
            logger.info(f"SKIP (disabled): {site_name}")
            continue

        logger.info(f"=== {site_name} ===")
        logger.info(f"Index strategy: {site.get('index_strategy')}")

        try:
            driver_class = get_driver_class(site.get("driver", "wordpress"))
            driver = driver_class(site, db_conn)
            summary = driver.run(dry_run=args.dry_run, limit=args.limit)

            logger.info(f"[{site_id}] Summary — found: {summary['found']}, "
                       f"inserted: {summary['inserted']}, "
                       f"skipped: {summary['skipped']}, "
                       f"errors: {summary['errors']}")

            # Accumulate totals
            for key in total_summary:
                total_summary[key] += summary[key]

        except Exception as e:
            logger.error(f"Error scraping {site_name}: {e}", exc_info=True)
            total_summary["errors"] += 1

    db_conn.close()

    # Final summary
    logger.info("\n=== GRAND TOTAL ===")
    logger.info(f"Found: {total_summary['found']}, "
               f"Inserted: {total_summary['inserted']}, "
               f"Skipped: {total_summary['skipped']}, "
               f"Errors: {total_summary['errors']}")

    if args.dry_run:
        logger.info("Dry-run complete. No database changes made.")


if __name__ == "__main__":
    main()
