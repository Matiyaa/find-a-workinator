import argparse
import cloudscraper
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote
import re
import json
import logging

# Import custom logger setup
from logger import setup_logger

# Set up logging using the custom function
logger = setup_logger(name='find_a_workinator', log_level=logging.INFO)


def get_headers():
    """Generate HTTP headers that mimic a modern web browser.

    Returns:
        dict: A dictionary of HTTP headers including:
            - User-Agent: Chrome browser identifier
            - Accept: Accepted content types
            - Accept-Encoding: Supported compression methods
            - Various security and fetch-related headers
            - Connection settings
            - Host configuration for pracuj.pl

    Note:
        Headers are logged at debug level for troubleshooting purposes.
        Cookie handling is managed separately by the session object.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Connection': 'keep-alive',
        'Cache-Control': 'no-cache',
        'Host': 'www.pracuj.pl',
    }
    logger.debug(f"Request headers being used (excluding cookies handled by session): {json.dumps(headers, indent=2)}")
    return headers


def build_url(keywords=None, city=None, distance=None, page=1):
    """Constructs a URL for searching jobs on pracuj.pl.

    Args:
        keywords (str, optional): Search keywords for job listings.
        city (str, optional): City name to filter job locations.
        distance (int, optional): Search radius in kilometers from the specified city.
        page (int, optional): Page number for pagination. Defaults to 1.

    Returns:
        str: Complete URL for the pracuj.pl job search with the specified parameters.
    """
    base_url = "https://www.pracuj.pl/praca"
    url_parts = []
    
    if keywords:
        url_parts.append(f"/{quote(keywords)};kw")
    if city:
        url_parts.append(f"/{quote(city)};wp")
    
    url = base_url + "".join(url_parts)
    
    query_params = []
    if distance:
        query_params.append(f"rd={distance}")
    if page > 1:
        query_params.append(f"pn={page}")
    
    if query_params:
        url += "?" + "&".join(query_params)
    
    return url


def make_request(scraper, url):
    """Makes an HTTP request using a scraper object with proper error handling and logging.

    Args:
        scraper: A requests.Session-like object that handles cookies and session management.
        url (str): The target URL to make the request to.

    Returns:
        requests.Response: The response object from the successful request.

    Raises:
        Exception: Any network, HTTP, or request-related exceptions that occur during the request.
            Failed requests will be logged with detailed error information including status codes
            and response snippets when available.

    Notes:
        - Uses custom headers to mimic browser behavior
        - Implements a 20-second timeout
        - Handles Cloudflare challenges and other potential blocks
        - Logs detailed request/response information at various log levels
    """
    try:
        logger.info(f"Making request to: {url}")
        headers = get_headers() # Get headers (without hardcoded Cookie)

        # Use the scraper object's get method
        response = scraper.get(
            url,
            headers=headers,
            allow_redirects=True,
            timeout=20 # Timeout to prevent hanging indefinitely
        )

        logger.info(f"Response status: {response.status_code}")
        # Log received cookies (optional, for debugging)
        logger.debug(f"Cookies received and managed by session: {scraper.cookies.get_dict()}")
        # Log response headers (as before)
        logger.info(f"Response headers: {json.dumps(dict(response.headers), indent=2)}")

        # Check for explicit blocks
        if response.status_code == 403:
            logger.error(f"Cloudflare challenge likely failed or persisted. Status: 403.")
            # Consider raising an exception or handling this case
        elif "Przepraszamy, strona której szukasz jest niedostępna" in response.text or "detected unusual activity" in response.text:
            logger.warning(f"Potential block detected despite status {response.status_code} on URL: {url}")

        response.raise_for_status()

        return response

    except Exception as e:
        logger.error(f"Request failed for {url}: {str(e)}")
        # Log response details if available, even on error
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Status code: {e.response.status_code}")
            logger.error(f"Response text snippet: {e.response.text[:500]}...")
        raise


def clean_text(text):
    """Normalizes and sanitizes text by removing redundant whitespace.

    Args:
        text (str): The input text to be cleaned. Can be None or empty.

    Returns:
        str: Cleaned text with:
            - Non-breaking spaces (\xa0) converted to regular spaces
            - Leading/trailing whitespace removed
            - Multiple consecutive whitespace characters collapsed to a single space
            - Empty string if input is None or empty

    Example:
        >>> clean_text("  Hello\xa0\xa0World\n  ")
        "Hello World"
    """
    if not text:
        return ""
    # Replace non-breaking spaces and trim
    text = text.replace('\xa0', ' ').strip()
    # Collapse multiple whitespace characters into a single space
    return re.sub(r'\s+', ' ', text.strip())


def extract_job_offer(offer_element, base_url):
    """
    Extracts job offer details from a single offer HTML element using data-test attributes.

    Args:
        offer_element (bs4.element.Tag): The BeautifulSoup Tag object representing the job offer container.
        base_url (str): The base URL of the page, used to resolve relative links if necessary.

    Returns:
        dict: A dictionary containing the extracted job offer details (company, city, position, salary, offer_link),
              or None if essential information couldn't be extracted.
    """
    
    data = {
        "company": "N/A",
        "city": "N/A",
        "position": "N/A",
        "salary": "N/A", # Salary often varies in how it's displayed, needs careful checking
        "offer_link": "N/A"
    }
    
    try:
        # --- Extract Position ---
        position_tag = offer_element.find('h2', attrs={'data-test': 'offer-title'})
        if position_tag:
            # Sometimes the title is inside an 'a' tag within the h2
            link_in_title = position_tag.find('a')
            if link_in_title and link_in_title.text:
                 data['position'] = clean_text(link_in_title.text)
            else:
                 data['position'] = clean_text(position_tag.text)
        else:
            logger.warning("Could not find position tag with data-test='offer-title'")
            return None

        # --- Extract Company Name ---
        company_section = offer_element.find('div', attrs={'data-test': 'section-company'})
        if company_section:
            company_tag = company_section.find('h3', attrs={'data-test': 'text-company-name'})
            if company_tag:
                data['company'] = clean_text(company_tag.text)
            else:
                logger.warning("Could not find company name tag (h3[data-test='text-company-name']) within company section")
        else:
            # Fallback: Sometimes company name might be in the alt text of the logo image
            logo_img = offer_element.find('img', attrs={'data-test': 'image-responsive'})
            if logo_img and logo_img.get('alt'):
                data['company'] = clean_text(logo_img['alt'])
                logger.debug("Found company name in logo alt text as fallback.")
            else:
                logger.warning("Could not find company section or logo alt text for company name.")
                return None

        # --- Extract Location (City) ---
        location_tag = offer_element.find('h4', attrs={'data-test': 'text-region'})
        if location_tag:
            data['city'] = clean_text(location_tag.text)
        else:
            # Sometimes location might be in a list item if multiple locations exist
            location_list_item = offer_element.find('li', attrs={'data-test': lambda x: x and x.startswith('offer-location-')})
            if location_list_item:
                data['city'] = clean_text(location_list_item.text)
            else:
                logger.warning("Could not find location tag (h4[data-test='text-region'] or li[data-test^='offer-location-'])")
        
        # --- Extract Salary ---
        salary_tag = offer_element.find('span', attrs={'data-test': 'offer-salary'})
        if salary_tag:
            data['salary'] = clean_text(salary_tag.text)
        else:
            # Log that salary wasn't found using the current selector
            logger.debug("Salary tag with data-test='offer-salary' not found for this offer.")
            data['salary'] = "N/A" # Explicitly set to N/A if not found

        # --- Extract Offer Link ---
        link_tag = None
        if position_tag: # Prefer link within the title h2
            link_tag = position_tag.find('a')
        if not link_tag: # Fallback to the direct link if not in title
            link_tag = offer_element.find('a', attrs={'data-test': 'link-offer'}, recursive=False)

        if link_tag and link_tag.get('href'):
            data['offer_link'] = urljoin(base_url, link_tag['href']) # Ensure absolute URL
        else:
            logger.warning("Could not find offer link tag (inside title or a[data-test='link-offer'])")
            return None

        # --- Final Validation ---
        if data['position'] == "N/A" or data['company'] == "N/A" or data['offer_link'] == "N/A":
            logger.warning(f"Missing essential data for an offer. Extracted: {data}. Skipping this offer.")
            return None # Skip incomplete offers

        logger.debug(f"Successfully extracted: {data['position']} at {data['company']}")
        return data

    except Exception as e:
        logger.error(f"Error extracting job offer details: {e}", exc_info=True)
        return None


def scrape_jobs(url_template, max_offers=25):
    """Scrapes job listings from pracuj.pl with robust error handling and pagination.

    Creates a CloudScraper instance to handle Cloudflare protection and iteratively
    fetches job listings across multiple pages until either max_offers is reached
    or no more pages are available.

    Args:
        url_template (str): Base URL template for job searches on pracuj.pl.
            Will be populated with search parameters using build_url().
        max_offers (int, optional): Maximum number of job offers to collect.
            Defaults to 25. The function may return fewer offers if not enough
            are available.

    Returns:
        list[dict]: List of job offer dictionaries, each containing:
            - position (str): Job title
            - company (str): Company name
            - city (str): Job location
            - salary (str): Salary information if available
            - offer_link (str): URL to the full job posting

    Note:
        - Implements automatic pagination detection
        - Handles Cloudflare protection
        - Includes extensive error handling and logging
        - Creates debug HTML files if parsing fails
        - Respects rate limits through CloudScraper
    """
    offers = []
    current_page = 1
    max_page_number = None

    # Create cloudscraper instance
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'mobile': False
        }
    )
    
    try:        
        # Loop while we haven't reached max_offers AND
        # (we don't know the max page OR we haven't reached the max page)
        while len(offers) < max_offers and (max_page_number is None or current_page <= max_page_number):
            current_url = build_url(
                keywords=args.keywords,
                city=args.city,
                distance=args.distance,
                page=current_page
            )
            
            logger.info(f"Fetching page {current_page}" +
                        (f"/{max_page_number}" if max_page_number else "") +
                        f" (target: {max_offers} offers)... URL: {current_url}")
            
            response = make_request(scraper, current_url)
            
            if response is None or not response.ok:
                logger.error(f"Failed to retrieve or received error for page {current_page}. Stopping scrape.")
                if response:
                     logger.error(f"Status code: {response.status_code}. Response sample: {response.text[:500]}...")
                break # Stop if the request failed

            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # --- Determine Max Page Number (only once, on the first page) ---
            if current_page == 1 and max_page_number is None:
                try:
                    max_page_span = soup.find('span', attrs={'data-test': 'top-pagination-max-page-number'})
                    if max_page_span and max_page_span.text:
                        max_page_number = int(clean_text(max_page_span.text))
                        logger.info(f"Detected maximum page number: {max_page_number}")
                    else:
                        logger.warning("Could not find max page number span. Relying on offer count or lack of offers.")
                except Exception as e:
                    logger.error(f"Error finding/parsing max page number: {e}")
            
            # Find all job offer containers
            main_offers_area = soup.find('div', id='offers-list')
            
            if not main_offers_area:
                # If even the main container isn't found, something is wrong with the page structure
                logger.error(f"Could not find the main offers area ('div#offers-list') on page {current_page}.")
                if "nie znaleźliśmy ofert pasujących" in response.text.lower():
                    logger.info("No offers found matching the criteria (message found).")
                else:
                    debug_filename = f"page_{current_page}_debug_main_area_not_found.html"
                    with open(debug_filename, "w", encoding="utf-8") as f: f.write(response.text)
                    logger.warning(f"Could not find main offers area. Saved page HTML to {debug_filename}")
                break # Stop if the main area isn't found

            job_offer_elements = main_offers_area.find_all('div', attrs={'data-test-offerid': True})
                
            if not job_offer_elements:
                logger.info(f"No job offer elements (div[data-test-offerid]) found within the container on page {current_page}.")
                # Check again if it's just the end of results
                if "nie znaleźliśmy ofert pasujących" in response.text.lower():
                     logger.info("No more offers found (confirmed by message).")
                else:
                     # Log the container's content for debugging
                     logger.warning(f"Container found, but no offer elements inside. Container snippet: {str(main_offers_area)[:500]}...")
                     # Save HTML again if needed
                     debug_filename = f"page_{current_page}_debug_no_offers_in_container.html"
                     with open(debug_filename, "w", encoding="utf-8") as f:
                          f.write(response.text)
                     logger.warning(f"Saved page HTML to {debug_filename} for inspection.")

                break # Stop if no offers found on the page

            offers_extracted_on_page = 0
            for offer_element in job_offer_elements:
                if len(offers) >= max_offers:
                    break
                
                # Pass the response.url as base_url for resolving relative links if needed
                job_data = extract_job_offer(offer_element, response.url)

                if job_data:
                    offers.append(job_data)
                    offers_extracted_on_page += 1 

            logger.info(f"Found {len(job_offer_elements)} potential offer elements on page {current_page}.")
         
            # If elements were found but nothing was extracted, it points to issues in extract_job_offer selectors
            if offers_extracted_on_page == 0 and job_offer_elements:
                logger.warning(f"Found {len(job_offer_elements)} offer elements on page {current_page}, but failed to extract data from any. Check selectors in extract_job_offer.")
                # Save HTML for debugging extraction issues
                debug_filename = f"page_{current_page}_debug_extraction_failed.html"
                with open(debug_filename, "w", encoding="utf-8") as f:
                    f.write(response.text)
                logger.warning(f"Saved page HTML to {debug_filename} for inspection.")
                break # Stop if extraction fails consistently
            
            logger.info(f"Successfully extracted {offers_extracted_on_page} offers from page {current_page}. Total extracted: {len(offers)}.")
            
            if len(offers) >= max_offers:
                logger.info(f"Reached max offers limit ({max_offers}).")
                break
            
            current_page += 1
            
    finally:
        # Any cleanup if needed
        logger.info("Scraping process finished or stopped.")    
        
        # Print the results
        print("\nFound job offers:")
        print("-" * 100)
        if offers:
            for offer in offers:
                print(f"Company: {offer['company']}")
                print(f"Position: {offer['position']}")
                print(f"Location: {offer['city']}")
                print(f"Salary: {offer['salary']}")
                print("-" * 100)
        else:
            print("No job offers were successfully scraped.")
    
    return offers


def main():
    parser = argparse.ArgumentParser(description='Find-a-workinator (faw) - Job offer scraper for pracuj.pl')
    parser.add_argument('--keywords', '-k', type=str, help='Keywords for job search')
    parser.add_argument('--city', '-c', type=str, help='City for job search')
    parser.add_argument('--distance', '-d', type=int, help='Maximum distance from city in km')
    parser.add_argument('--max-offers', '-m', type=int, default=25, help='Maximum number of offers to return (default: 25)')
    
    global args
    args = parser.parse_args()
    
    url = build_url(
        keywords=args.keywords,
        city=args.city,
        distance=args.distance
    )
    
    scrape_jobs(url, args.max_offers)


if __name__ == "__main__":
    main()
