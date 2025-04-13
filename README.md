# Find-a-workinator (faw)

A Python CLI application for scraping job offers from the pracuj.pl. Allows easy searching using keywords, city, and distance.

## Features

*   Scrapes job listings from `pracuj.pl`.
*   Filters by keywords, city, and radius.
*   Handles Cloudflare protection using `cloudscraper`.
*   Provides an easy-to-use command-line interface (`faw`).
*   Includes installation scripts for Windows (PowerShell) and Linux/macOS (Bash/Zsh) to set up the `faw` command and install dependencies.

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

2.  **Run the appropriate installation script:**
    This script will install the necessary Python packages from `requirements.txt` and set up the `faw` command for easy use in your terminal/shell.

    *   **On Windows (using PowerShell):**
        *   You might need to adjust your PowerShell execution policy first. Open PowerShell **as Administrator** and run (choose one):
          ```powershell
          # Option 1: Allow scripts signed by a trusted publisher (recommended for security)
          Set-ExecutionPolicy RemoteSigned -Scope LocalMachine -Force

          # Option 2: Allow all local scripts and signed remote scripts (for current user)
          # Set-ExecutionPolicy RemoteSigned -Scope CurrentUser -Force

          # Option 3: Allow any script (less secure, use with caution)
          # Set-ExecutionPolicy Unrestricted -Scope CurrentUser -Force
          ```
        *   Close the Administrator PowerShell. Open a **regular PowerShell** window, navigate to the project directory (`cd find-a-workinator`), and run the installer:
          ```powershell
          .\install.ps1
          ```

    *   **On Linux or macOS (using Bash or Zsh):**
        *   Navigate to the project directory in your terminal:
          ```bash
          cd find-a-workinator
          ```
        *   Make the installation script executable (only needed once):
          ```bash
          chmod +x install.sh
          ```
        *   Run the installer:
          ```bash
          ./install.sh
          ```

3.  **Restart your Terminal/Shell:**
    After the installation script finishes, **close and reopen** your PowerShell or Terminal window. Alternatively, you can reload your shell profile manually by running the command suggested by the script (e.g., `. $PROFILE` in PowerShell, or `source ~/.bashrc` / `source ~/.zshrc` in Bash/Zsh).

## Usage

Once installed, you can run the application from **anywhere** in your terminal using the `faw` command followed by the desired options:

```bash
faw [options]
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
faw --keywords python --city warszawa
```

Search for Java jobs in Kraków within 50km:
```bash
faw --keywords java --city krakow --distance 50
```

Search for all jobs in Gdańsk, limit to 10 offers:
```bash
faw --city gdansk --max-offers 10
```

### TODO:
- Save scrapped offers to a file for later use / prevent duplicates
- Add support for more pracuj.pl filter options
- Add support for more job boards
- Add helper functions for applying to offers