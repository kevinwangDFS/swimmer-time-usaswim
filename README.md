# Swimmer Time

A Python package to scrape swimmer time data from USA Swimming.

## Installation

```bash
poetry install
```

## Configuration

Edit `config/config.yaml` to set:

- ChromeDriver path
- Wait time for page loads
- Output file path
- Swimmer details (name, club, year)

## Usage

### As a Library

```python
from swimmer_time import SwimmerDataScraper

# Initialize scraper with ChromeDriver path
scraper = SwimmerDataScraper("/path/to/chromedriver")

# Setup and use
scraper.setup_driver()
scraper.search_swimmer("First", "Last")
scraper.select_swimmer_profile("Club Name")
scraper.select_competition_year()

# Get data
df = scraper.extract_table_data()
df.to_csv("output.csv", index=False)

# Clean up
scraper.close()
```

### Command Line Interface

```bash
# Using poetry
poetry run swimmer-time

# Or directly with Python
python -m swimmer_time.cli
```

Make sure to configure the settings in `config/config.yaml` before running.
