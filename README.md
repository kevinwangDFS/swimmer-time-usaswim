# Swimmer Time

A Python package to scrape swimmer time data from USA Swimming.

## Installation

### From PyPI

```bash
pip install swimmer-time
```

### From Source

```bash
git clone https://github.com/kevinwang/swimmer-time.git
cd swimmer-time
poetry install
```

## Configuration

Edit `config/config.yaml` to set:

- ChromeDriver path
- Wait time for page loads
- Output file path and validation settings
  - `file`: Path to save the CSV output
  - `save_invalid_data`: Set to true to save data even if validation fails
- Swimmer details (name, club, year)

## Features

- Automatic retry mechanism for web operations with exponential backoff
- Data validation and cleaning
  - Validates expected columns are present
  - Converts dates to proper datetime format
  - Cleans time strings
  - Removes empty rows
- Configurable invalid data handling

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

### Error Handling

The scraper includes several error handling features:

1. Automatic Retries
   - Web operations automatically retry on failure
   - Uses exponential backoff between attempts
   - Configurable max retries and initial delay

2. Data Validation
   - Validates data structure and content
   - Reports validation errors and warnings
   - Optional saving of invalid data (controlled by config)

3. Logging
   - Detailed logging of operations
   - Error and warning messages
   - Validation status reporting
