"""
Global pytest configuration and fixtures for find-a-workinator tests.
"""
import pytest
import tempfile
import os
import sys
from unittest.mock import patch

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session")
def test_data_dir():
    """Create a temporary directory for test data that persists for the session."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def sample_html_responses():
    """Provide sample HTML responses for different scenarios."""
    return {
        'job_listing_page': """
        <html>
        <body>
            <div id="offers-list">
                <span data-test="top-pagination-max-page-number">3</span>
                <div data-test-offerid="TEST001">
                    <h2 data-test="offer-title">
                        <a href="/praca/python-developer">Python Developer</a>
                    </h2>
                    <div data-test="section-company">
                        <h3 data-test="text-company-name">TechCorp</h3>
                    </div>
                    <h4 data-test="text-region">Warszawa</h4>
                    <span data-test="offer-salary">15000 - 20000 PLN</span>
                    <p data-test="text-added">Opublikowana: 21 czerwca 2025</p>
                </div>
            </div>
        </body>
        </html>
        """,
        
        'empty_results': """
        <html>
        <body>
            <div id="offers-list">
                <p>nie znaleźliśmy ofert pasujących do Twoich kryteriów</p>
            </div>
        </body>
        </html>
        """,
        
        'malformed_page': """
        <html>
        <body>
            <div>Some other content without proper structure</div>
        </body>
        </html>
        """
    }


@pytest.fixture
def sample_job_offers():
    """Provide sample job offer data for testing."""
    return [
        {
            'offer_id': 'SAMPLE001',
            'company': 'TechCorp Solutions',
            'position': 'Senior Python Developer',
            'city': 'Warszawa',
            'salary': '15000 - 20000 PLN',
            'offer_link': 'https://www.pracuj.pl/praca/senior-python-developer',
            'date_added': '21.06.2025'
        },
        {
            'offer_id': 'SAMPLE002',
            'company': 'StartupXYZ',
            'position': 'Junior Java Developer',
            'city': 'Kraków',
            'salary': '8000 - 12000 PLN',
            'offer_link': 'https://www.pracuj.pl/praca/junior-java-developer',
            'date_added': '20.06.2025'
        },
        {
            'offer_id': 'SAMPLE003',
            'company': 'Enterprise Corp',
            'position': 'Full Stack Developer',
            'city': 'Gdańsk',
            'salary': 'N/A',
            'offer_link': 'https://www.pracuj.pl/praca/full-stack-developer',
            'date_added': '19.06.2025'
        }
    ]


@pytest.fixture
def mock_cloudscraper():
    """Mock cloudscraper for tests that need to avoid actual HTTP requests."""
    with patch('find_a_workinator.cloudscraper.create_scraper') as mock_create:
        mock_scraper = patch('cloudscraper.CloudScraper').start()
        mock_create.return_value = mock_scraper
        yield mock_scraper
        patch.stopall()


@pytest.fixture
def mock_logger():
    """Mock logger to capture log messages during tests."""
    with patch('find_a_workinator.logger') as mock_log:
        yield mock_log


@pytest.fixture(autouse=True)
def cleanup_debug_files():
    """Automatically clean up debug HTML files created during tests."""
    yield
    
    # Clean up any debug files that might have been created
    debug_files = [
        f for f in os.listdir('.')
        if f.startswith('page_') and f.endswith('_debug') and f.endswith('.html')
    ]
    
    for debug_file in debug_files:
        try:
            os.remove(debug_file)
        except OSError:
            pass  # File might not exist or be locked


# Pytest configuration for different test types
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Mark tests based on their file names
        if "test_utils" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "test_db_manager" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "test_job_extraction" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "test_scraping" in str(item.fspath):
            item.add_marker(pytest.mark.integration)