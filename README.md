# Find-a-workinator (faw)

A Python CLI application for scraping job offers from the pracuj.pl. Allows easy searching using keywords, city, and distance.

## Features

*   Scrapes job listings from `pracuj.pl`.
*   Filters by keywords, city, and radius.
*   Handles Cloudflare protection using `cloudscraper`.
*   Provides an easy-to-use command-line interface for job searching.

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

### TODO:
- Save scrapped offers to a file for later use / prevent duplicates
- Add support for more pracuj.pl filter options
- Add support for more job boards
- Add helper functions for applying to offers
