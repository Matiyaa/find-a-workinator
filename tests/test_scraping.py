"""
Mock tests for web scraping functionality to avoid actual HTTP requests.
"""
import pytest
import sys
import os
from unittest.mock import patch, MagicMock, Mock
from requests import Response
import cloudscraper

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from find_a_workinator import make_request, scrape_jobs


class TestMakeRequest:
    """Test the make_request function with mocked responses."""
    
    def test_make_request_success(self):
        """Test successful HTTP request."""
        # Create mock scraper and response
        mock_scraper = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_response.headers = {'content-type': 'text/html'}
        mock_response.text = '<html><body>Test content</body></html>'
        mock_scraper.get.return_value = mock_response
        mock_scraper.cookies.get_dict.return_value = {}
        
        url = "https://www.pracuj.pl/praca"
        
        result = make_request(mock_scraper, url)
        
        assert result == mock_response
        mock_scraper.get.assert_called_once()
        mock_response.raise_for_status.assert_called_once()
    
    def test_make_request_403_error(self):
        """Test handling of 403 Forbidden response."""
        mock_scraper = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.headers = {}
        mock_response.text = 'Access denied'
        mock_scraper.get.return_value = mock_response
        mock_scraper.cookies.get_dict.return_value = {}
        
        url = "https://www.pracuj.pl/praca"
        
        result = make_request(mock_scraper, url)
        
        assert result == mock_response
        assert mock_response.status_code == 403
    
    def test_make_request_cloudflare_block_detection(self):
        """Test detection of Cloudflare blocks in response text."""
        mock_scraper = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {}
        mock_response.text = 'detected unusual activity from your computer'
        mock_scraper.get.return_value = mock_response
        mock_scraper.cookies.get_dict.return_value = {}
        
        url = "https://www.pracuj.pl/praca"
        
        # Should not raise exception but log warning
        result = make_request(mock_scraper, url)
        assert result == mock_response
    
    def test_make_request_network_error(self):
        """Test handling of network errors."""
        mock_scraper = MagicMock()
        mock_scraper.get.side_effect = Exception("Network timeout")
        
        url = "https://www.pracuj.pl/praca"
        
        with pytest.raises(Exception) as exc_info:
            make_request(mock_scraper, url)
        
        assert "Network timeout" in str(exc_info.value)
    
    def test_make_request_http_error(self):
        """Test handling of HTTP errors."""
        mock_scraper = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.headers = {}
        mock_response.text = 'Internal server error'
        mock_response.raise_for_status.side_effect = Exception("500 Server Error")
        mock_scraper.get.return_value = mock_response
        mock_scraper.cookies.get_dict.return_value = {}
        
        url = "https://www.pracuj.pl/praca"
        
        with pytest.raises(Exception) as exc_info:
            make_request(mock_scraper, url)
        
        assert "500 Server Error" in str(exc_info.value)


class TestScrapingIntegration:
    """Test the scrape_jobs function with mocked components."""
    
    @pytest.fixture
    def mock_job_listing_html(self):
        """Mock HTML response for job listings page."""
        return """
        <html>
        <body>
            <div id="offers-list">
                <span data-test="top-pagination-max-page-number">5</span>
                <div data-test-offerid="JOB001">
                    <h2 data-test="offer-title">
                        <a href="/praca/python-dev">Python Developer</a>
                    </h2>
                    <div data-test="section-company">
                        <h3 data-test="text-company-name">TechCorp</h3>
                    </div>
                    <h4 data-test="text-region">Warszawa</h4>
                    <span data-test="offer-salary">15000 PLN</span>
                    <p data-test="text-added">Opublikowana: 21 czerwca 2025</p>
                </div>
                <div data-test-offerid="JOB002">
                    <h2 data-test="offer-title">
                        <a href="/praca/java-dev">Java Developer</a>
                    </h2>
                    <div data-test="section-company">
                        <h3 data-test="text-company-name">JavaSoft</h3>
                    </div>
                    <h4 data-test="text-region">Kraków</h4>
                    <span data-test="offer-salary">12000 PLN</span>
                    <p data-test="text-added">Opublikowana: 20 czerwca 2025</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    @pytest.fixture
    def mock_empty_listing_html(self):
        """Mock HTML response for empty job listings."""
        return """
        <html>
        <body>
            <div id="offers-list">
                <p>nie znaleźliśmy ofert pasujących do Twoich kryteriów</p>
            </div>
        </body>
        </html>
        """
    
    @pytest.fixture
    def mock_no_offers_container_html(self):
        """Mock HTML response without offers container."""
        return """
        <html>
        <body>
            <div>Some other content</div>
        </body>
        </html>
        """
    
    @patch('find_a_workinator.cloudscraper.create_scraper')
    @patch('find_a_workinator.make_request')
    @patch('find_a_workinator.args', create=True)
    def test_scrape_jobs_success(self, mock_args, mock_make_request, mock_create_scraper, mock_job_listing_html):
        """Test successful job scraping."""
        # Setup mocks
        mock_args.keywords = "python"
        mock_args.city = "warszawa"
        mock_args.distance = None
        
        mock_scraper = MagicMock()
        mock_create_scraper.return_value = mock_scraper
        
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.text = mock_job_listing_html
        mock_response.url = "https://www.pracuj.pl/praca"
        mock_make_request.return_value = mock_response
        
        # Execute
        url = "https://www.pracuj.pl/praca/python;kw/warszawa;wp"
        result = scrape_jobs(url, max_offers=5)
        
        # Verify - should return 5 offers (max_offers limit reached)
        # The function finds 2 offers per page and continues until max_offers (5) is reached
        assert len(result) == 5
        assert result[0]['offer_id'] == 'JOB001'
        assert result[0]['position'] == 'Python Developer'
        assert result[0]['company'] == 'TechCorp'
        assert result[1]['offer_id'] == 'JOB002'
        assert result[1]['position'] == 'Java Developer'
        
        mock_make_request.assert_called()
    
    @patch('find_a_workinator.args', create=True)
    @patch('find_a_workinator.cloudscraper.create_scraper')
    @patch('find_a_workinator.make_request')
    def test_scrape_jobs_empty_results(self, mock_make_request, mock_create_scraper, mock_args, mock_empty_listing_html):
        """Test scraping when no jobs are found."""
        # Setup mocks
        mock_args.keywords = "nonexistent"
        mock_args.city = "nowhere"
        mock_args.distance = None
        
        mock_scraper = MagicMock()
        mock_create_scraper.return_value = mock_scraper
        
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.text = mock_empty_listing_html
        mock_response.url = "https://www.pracuj.pl/praca"
        mock_make_request.return_value = mock_response
        
        # Execute
        url = "https://www.pracuj.pl/praca"
        result = scrape_jobs(url, max_offers=5)
        
        # Verify
        assert len(result) == 0
    
    @patch('find_a_workinator.args', create=True)
    @patch('find_a_workinator.cloudscraper.create_scraper')
    @patch('find_a_workinator.make_request')
    def test_scrape_jobs_no_container(self, mock_make_request, mock_create_scraper, mock_args, mock_no_offers_container_html):
        """Test scraping when offers container is missing."""
        # Setup mocks
        mock_args.keywords = "test"
        mock_args.city = "test"
        mock_args.distance = None
        
        mock_scraper = MagicMock()
        mock_create_scraper.return_value = mock_scraper
        
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.text = mock_no_offers_container_html
        mock_response.url = "https://www.pracuj.pl/praca"
        mock_make_request.return_value = mock_response
        
        # Execute
        url = "https://www.pracuj.pl/praca"
        result = scrape_jobs(url, max_offers=5)
        
        # Verify
        assert len(result) == 0
    
    @patch('find_a_workinator.args', create=True)
    @patch('find_a_workinator.cloudscraper.create_scraper')
    @patch('find_a_workinator.make_request')
    def test_scrape_jobs_request_failure(self, mock_make_request, mock_create_scraper, mock_args):
        """Test scraping when HTTP request fails."""
        # Setup mocks
        mock_args.keywords = "test"
        mock_args.city = "test"
        mock_args.distance = None
        
        mock_scraper = MagicMock()
        mock_create_scraper.return_value = mock_scraper
        
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 500
        mock_make_request.return_value = mock_response
        
        # Execute
        url = "https://www.pracuj.pl/praca"
        result = scrape_jobs(url, max_offers=5)
        
        # Verify
        assert len(result) == 0
    
    @patch('find_a_workinator.args', create=True)
    @patch('find_a_workinator.cloudscraper.create_scraper')
    @patch('find_a_workinator.make_request')
    def test_scrape_jobs_max_offers_limit(self, mock_make_request, mock_create_scraper, mock_args, mock_job_listing_html):
        """Test that scraping respects max_offers limit."""
        # Setup mocks
        mock_args.keywords = "python"
        mock_args.city = "warszawa"
        mock_args.distance = None
        
        mock_scraper = MagicMock()
        mock_create_scraper.return_value = mock_scraper
        
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.text = mock_job_listing_html
        mock_response.url = "https://www.pracuj.pl/praca"
        mock_make_request.return_value = mock_response
        
        # Execute with max_offers=1
        url = "https://www.pracuj.pl/praca"
        result = scrape_jobs(url, max_offers=1)
        
        # Verify - should stop after 1 offer even though more are available
        assert len(result) == 1
        assert result[0]['offer_id'] == 'JOB001'
    
    @patch('find_a_workinator.args', create=True)
    @patch('find_a_workinator.cloudscraper.create_scraper')
    @patch('find_a_workinator.make_request')
    def test_scrape_jobs_pagination_detection(self, mock_make_request, mock_create_scraper, mock_args, mock_job_listing_html):
        """Test that pagination is properly detected."""
        # Setup mocks
        mock_args.keywords = "python"
        mock_args.city = "warszawa"
        mock_args.distance = None
        
        mock_scraper = MagicMock()
        mock_create_scraper.return_value = mock_scraper
        
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.text = mock_job_listing_html  # Contains max page number 5
        mock_response.url = "https://www.pracuj.pl/praca"
        mock_make_request.return_value = mock_response
        
        # Execute
        url = "https://www.pracuj.pl/praca"
        result = scrape_jobs(url, max_offers=5)
        
        # Should find 5 offers (max_offers limit) and detect max page = 5
        assert len(result) == 5
        
        # Verify that make_request was called (pagination would call it multiple times if needed)
        mock_make_request.assert_called()


class TestCloudscraperIntegration:
    """Test cloudscraper integration without actual network calls."""
    
    @patch('find_a_workinator.args', create=True)
    @patch('find_a_workinator.cloudscraper.create_scraper')
    def test_cloudscraper_creation(self, mock_create_scraper, mock_args):
        """Test that cloudscraper is created with proper configuration."""
        from find_a_workinator import scrape_jobs
        
        mock_scraper = MagicMock()
        mock_create_scraper.return_value = mock_scraper
        
        # Setup args mock
        mock_args.keywords = None
        mock_args.city = None
        mock_args.distance = None
        
        # Mock make_request to avoid actual network calls
        with patch('find_a_workinator.make_request') as mock_make_request:
            mock_response = MagicMock()
            mock_response.ok = False  # Force early exit
            mock_make_request.return_value = mock_response
            
            scrape_jobs("https://test.com", max_offers=1)
        
        # Verify cloudscraper was created with correct browser config
        mock_create_scraper.assert_called_once_with(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            }
        )