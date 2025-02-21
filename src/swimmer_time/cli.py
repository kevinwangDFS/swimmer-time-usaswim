#!/usr/bin/env python3

import yaml
import logging
from pathlib import Path
from .scraper import SwimmerDataScraper

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def load_config(config_path: str = "config/config.yaml") -> dict:
    """Load configuration from YAML file."""
    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logger.error(f"Error loading config file: {e}")
        raise


def main():
    """Main execution function."""
    config = load_config()

    scraper = SwimmerDataScraper(config["chromedriver"]["path"], wait_time=config["chromedriver"]["wait_time"])

    try:
        scraper.setup_driver()
        scraper.search_swimmer(config["swimmer"]["first_name"], config["swimmer"]["last_name"])
        scraper.select_swimmer_profile(club_name=config["swimmer"]["club_name"])
        scraper.select_competition_year(year=config["swimmer"]["year"])

        df, validation_results = scraper.extract_table_data()

        if not validation_results["is_valid"]:
            logger.error("Data validation failed:")
            for error in validation_results["errors"]:
                logger.error(f"  - {error}")
            for warning in validation_results["warnings"]:
                logger.warning(f"  - {warning}")

        if validation_results["is_valid"] or config.get("output", {}).get("save_invalid_data", False):
            df.to_csv(config["output"]["file"], index=False)
            logger.info(f"Data saved to {config['output']['file']}")
            if not validation_results["is_valid"]:
                logger.warning("Invalid data was saved due to save_invalid_data=True setting")
        else:
            logger.error("Data was not saved due to validation failures")

    except Exception as e:
        logger.error(f"An error occurred during execution: {e}")
        raise
    finally:
        scraper.close()


if __name__ == "__main__":
    main()
