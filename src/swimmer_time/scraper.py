#!/usr/bin/env python3

import time
import logging
from typing import List, Optional, Tuple
from functools import wraps
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def retry_on_exception(max_retries: int = 3, initial_delay: int = 1):
    """
    Decorator that retries a function on specified exceptions with exponential backoff.

    Args:
        max_retries (int): Maximum number of retry attempts
        initial_delay (int): Initial delay between retries in seconds
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (TimeoutException, WebDriverException) as e:
                    last_exception = e
                    if attempt == max_retries - 1:
                        logger.error(f"Final attempt failed: {str(e)}")
                        raise
                    logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                    time.sleep(delay)
                    delay *= 2  # Exponential backoff

            if last_exception:
                raise last_exception
            return None

        return wrapper

    return decorator


class SwimmerDataValidator:
    """Validates and cleans swimmer time data."""

    EXPECTED_COLUMNS = ["Date", "Meet", "Event", "Time", "Standard"]

    @staticmethod
    def validate_dataframe(df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
        """
        Validates the structure and content of the scraped data.

        Args:
            df (pd.DataFrame): Raw scraped data

        Returns:
            Tuple[pd.DataFrame, dict]: Cleaned dataframe and validation results
        """
        validation_results = {"is_valid": True, "errors": [], "warnings": []}

        # Validate structure
        if df.empty:
            validation_results["is_valid"] = False
            validation_results["errors"].append("Empty dataset")
            return df, validation_results

        # Validate columns
        missing_cols = set(SwimmerDataValidator.EXPECTED_COLUMNS) - set(df.columns)
        if missing_cols:
            validation_results["errors"].append(f"Missing columns: {missing_cols}")
            validation_results["is_valid"] = False

        # Clean and validate data
        df = SwimmerDataValidator.clean_data(df)

        return df, validation_results

    @staticmethod
    def clean_data(df: pd.DataFrame) -> pd.DataFrame:
        """
        Cleans and standardizes the data.

        Args:
            df (pd.DataFrame): Raw dataframe

        Returns:
            pd.DataFrame: Cleaned dataframe
        """
        # Remove any completely empty rows
        df = df.dropna(how="all")

        # Convert date strings to datetime
        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

        # Clean time strings
        if "Time" in df.columns:
            df["Time"] = df["Time"].str.strip()

        return df


class SwimmerDataScraper:
    def __init__(self, chromedriver_path: str, wait_time: int = 10):
        """
        Initialize the scraper with WebDriver configuration.

        Args:
            chromedriver_path (str): Path to chromedriver executable
            wait_time (int): Default wait time for explicit waits
        """
        self.driver = None
        self.wait_time = wait_time
        self.chromedriver_path = chromedriver_path
        self.base_url = "https://data.usaswimming.org/datahub/usas/individualsearch"

    def setup_driver(self) -> None:
        """Initialize and configure the Chrome WebDriver."""
        try:
            service = Service(self.chromedriver_path)
            self.driver = webdriver.Chrome(service=service)
            self.wait = WebDriverWait(self.driver, self.wait_time)
            logger.info("WebDriver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            raise

    @retry_on_exception(max_retries=3)
    def search_swimmer(self, first_name: str, last_name: str) -> None:
        """
        Search for a swimmer using their name.

        Args:
            first_name (str): Swimmer's first name
            last_name (str): Swimmer's last name
        """
        try:
            self.driver.get(self.base_url)
            time.sleep(5)  # Wait for page load

            first_name_input = self.driver.find_element(By.NAME, "firstOrPreferredName")
            last_name_input = self.driver.find_element(By.NAME, "lastName")

            first_name_input.send_keys(first_name)
            last_name_input.send_keys(last_name)
            last_name_input.send_keys(Keys.RETURN)

            logger.info(f"Searched for swimmer: {first_name} {last_name}")
            time.sleep(5)  # Wait for search results
        except Exception as e:
            logger.error(f"Error searching for swimmer: {e}")
            raise

    @retry_on_exception(max_retries=3)
    def select_swimmer_profile(self, club_name: str = "Rockwood Swim Club") -> None:
        """
        Select swimmer's profile from search results.

        Args:
            club_name (str): Name of the swimmer's club
        """
        try:
            row = self.driver.find_element(By.XPATH, f"//tr[contains(., '{club_name}')]")
            button = row.find_element(By.CLASS_NAME, "_ActionButton_8nq2x_59")
            button.click()
            time.sleep(5)
            logger.info("Selected swimmer profile")
        except NoSuchElementException:
            logger.error(f"Could not find swimmer associated with {club_name}")
            raise

    @retry_on_exception(max_retries=3)
    def select_competition_year(self, year: str = "-1") -> None:
        """Select the first competition year from the dropdown."""
        try:
            dropdown = self.wait.until(EC.presence_of_element_located((By.NAME, "competitionYearId")))
            select = Select(dropdown)
            select.select_by_value(year)  # all year
            logger.info(f"Selected competition year: {'all year' if year=='-1' else year}")
        except TimeoutException:
            logger.error("Timeout waiting for competition year dropdown")
            raise

    def extract_table_data(self) -> Tuple[pd.DataFrame, dict]:
        """
        Extract data from the table and return as DataFrame.

        Returns:
            pd.DataFrame: Extracted table data
        """
        try:
            table = self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))

            headers = [header.text for header in table.find_elements(By.TAG_NAME, "th")]

            rows = []
            for row in table.find_elements(By.TAG_NAME, "tr")[1:]:
                row_data = [cell.text for cell in row.find_elements(By.TAG_NAME, "td")]
                rows.append(row_data)

            df = pd.DataFrame(rows, columns=headers)
            df = df.rename(columns=lambda x: x.split("\n")[0] if "\n" in x else x)

            logger.info("Successfully extracted raw table data")
            return SwimmerDataValidator.validate_dataframe(df)
        except Exception as e:
            logger.error(f"Error extracting table data: {e}")
            raise

    def close(self) -> None:
        """Clean up resources by closing the WebDriver."""
        if self.driver:
            self.driver.quit()
            logger.info("WebDriver closed")
