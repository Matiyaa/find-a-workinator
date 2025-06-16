# Find-a-workinator (faw)

A Python CLI application for scraping job offers from the pracuj.pl. Allows easy searching using keywords, city, and distance.

## Features

*   Scrapes job listings from `pracuj.pl`.
*   Filters by keywords, city, and radius.
*   Handles Cloudflare protection using `cloudscraper`.
*   Provides an easy-to-use command-line interface for job searching.

## Database Features

Find-a-workinator now includes SQLite database integration for saving and managing scraped job offers:

* **Persistent Storage**: Save job offers to a SQLite database for later reference
* **Duplicate Prevention**: Automatically detects and skips duplicate job offers
* **Filtering**: Query saved offers by company, position, city, or date range
* **CSV Export**: Export filtered offers to CSV files for further analysis
* **Search Context**: Tracks which city and distance parameters were used to find each offer

## Prerequisites

*   **Python 3.7+** with `pip` installed and available in your system's PATH.
*   **Git** (for cloning the repository).
*   **(Windows)** PowerShell 5.1 or higher.
*   **(Linux/macOS)** Bash or Zsh shell.

## Installation

1.  **Clone this repository:**
    ```bash
    git clone https://github.com/Matiyaa/find-a-workinator
    cd find-a-workinator
    ```

2.  **Install dependencies:**
    Install the required Python packages using pip:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the script:**
    You can run the script directly using Python:
    ```bash
    python find_a_workinator.py [options]
    ```

## Usage

You can run the application using Python directly:

```bash
python find_a_workinator.py [options]
```

### Options:
- --keywords, -k: Keywords for the job search (e.g., "python developer", java).
- --city, -c: City for the job search (e.g., warszawa, wroclaw).
- --distance, -d: Maximum distance from the city in kilometers (e.g., 50).
- --max-offers, -m: Maximum number of offers to retrieve (default: 25).

#### Database Options:
- --save-to-db: Save scraped offers to database (default: True).
- --no-save-to-db: Do not save scraped offers to database.
- --db-path: Path to SQLite database file (default: job_offers.db in script directory).
- --list-saved: List saved job offers from the database.
- --filter-company: Filter saved offers by company name.
- --filter-position: Filter saved offers by position/title.
- --filter-city: Filter saved offers by city.
- --filter-date-from: Filter saved offers by date added (from) in format YYYY-MM-DD.
- --filter-date-to: Filter saved offers by date added (to) in format YYYY-MM-DD.
- --export-csv: Export saved offers to CSV file (provide filename).

- --help, -h: Show the help message and exit.

### Usage examples:

Search for Python jobs in Warsaw:
```bash
python find_a_workinator.py --keywords python --city warszawa
```

Search for Java jobs in Kraków within 50km:
```bash
python find_a_workinator.py --keywords java --city krakow --distance 50
```

Search for all jobs in Gdańsk, limit to 10 offers:
```bash
python find_a_workinator.py --city gdansk --max-offers 10
```

### Database Usage Examples:

Search for Python jobs in Warsaw and save to database:
```bash
python find_a_workinator.py --keywords python --city warszawa
```

Search without saving to database:
```bash
python find_a_workinator.py --keywords java --city krakow --no-save-to-db
```

List all saved job offers:
```bash
python find_a_workinator.py --list-saved
```

Filter saved offers by company name:
```bash
python find_a_workinator.py --list-saved --filter-company "Google"
```

Filter saved offers by position and city:
```bash
python find_a_workinator.py --list-saved --filter-position "developer" --filter-city "warszawa"
```

Filter offers added after a specific date:
```bash
python find_a_workinator.py --list-saved --filter-date-from "2025-01-01"
```

Export filtered offers to CSV:
```bash
python find_a_workinator.py --filter-position "python" --export-csv "python_jobs.csv"
```

Use a custom database location:
```bash
python find_a_workinator.py --db-path "C:\path\to\my_job_database.db" --keywords python
```

### TODO:
- ✅ Save scrapped offers to a file for later use / prevent duplicates
- Add support for more pracuj.pl filter options
- Add support for more job boards
- Add helper functions for applying to offers
