"""
Integration tests for job extraction logic in find_a_workinator.py
"""
import pytest
import sys
import os
from bs4 import BeautifulSoup
from unittest.mock import patch, MagicMock

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from find_a_workinator import extract_job_offer, get_headers


class TestJobExtraction:
    """Test cases for job extraction from HTML."""
    
    @pytest.fixture
    def sample_job_html(self):
        """Sample HTML for a job offer element."""
        return """
        <div data-test-offerid="123456789">
            <h2 data-test="offer-title">
                <a href="/praca/python-developer-warszawa,oferta,123456789">Python Developer</a>
            </h2>
            <div data-test="section-company">
                <h3 data-test="text-company-name">TechCorp Solutions</h3>
            </div>
            <h4 data-test="text-region">Warszawa</h4>
            <span data-test="offer-salary">15000 - 20000 PLN</span>
            <p data-test="text-added">Opublikowana: 21 czerwca 2025</p>
        </div>
        """
    
    @pytest.fixture
    def minimal_job_html(self):
        """Minimal HTML for a job offer (required fields only)."""
        return """
        <div data-test-offerid="MIN123">
            <h2 data-test="offer-title">
                <a href="/praca/junior-developer">Junior Developer</a>
            </h2>
            <div data-test="section-company">
                <h3 data-test="text-company-name">StartupXYZ</h3>
            </div>
            <h4 data-test="text-region">Kraków</h4>
        </div>
        """
    
    @pytest.fixture
    def job_html_with_logo_fallback(self):
        """Job HTML where company name is in logo alt text."""
        return """
        <div data-test-offerid="LOGO123">
            <h2 data-test="offer-title">
                <a href="/praca/designer-position">UI/UX Designer</a>
            </h2>
            <img data-test="image-responsive" alt="Design Studio Pro" src="/logo.png">
            <h4 data-test="text-region">Gdańsk</h4>
        </div>
        """
    
    @pytest.fixture
    def incomplete_job_html(self):
        """Incomplete HTML missing essential fields."""
        return """
        <div data-test-offerid="INCOMPLETE">
            <h2 data-test="offer-title">Some Position</h2>
            <!-- Missing company information -->
            <h4 data-test="text-region">Wrocław</h4>
        </div>
        """
    
    def test_extract_complete_job_offer(self, sample_job_html):
        """Test extracting a complete job offer with all fields."""
        soup = BeautifulSoup(sample_job_html, 'html.parser')
        offer_element = soup.find('div', attrs={'data-test-offerid': True})
        
        result = extract_job_offer(offer_element, "https://www.pracuj.pl")
        
        assert result is not None
        assert result['offer_id'] == '123456789'
        assert result['position'] == 'Python Developer'
        assert result['company'] == 'TechCorp Solutions'
        assert result['city'] == 'Warszawa'
        assert result['salary'] == '15000 - 20000 PLN'
        assert result['offer_link'] == 'https://www.pracuj.pl/praca/python-developer-warszawa,oferta,123456789'
        assert result['date_added'] == '21.06.2025'
    
    def test_extract_minimal_job_offer(self, minimal_job_html):
        """Test extracting a job offer with minimal required fields."""
        soup = BeautifulSoup(minimal_job_html, 'html.parser')
        offer_element = soup.find('div', attrs={'data-test-offerid': True})
        
        result = extract_job_offer(offer_element, "https://www.pracuj.pl")
        
        assert result is not None
        assert result['offer_id'] == 'MIN123'
        assert result['position'] == 'Junior Developer'
        assert result['company'] == 'StartupXYZ'
        assert result['city'] == 'Kraków'
        assert result['salary'] == 'N/A'  # Missing salary should default to N/A
        assert result['date_added'] == 'N/A'  # Missing date should default to N/A
        assert result['offer_link'] == 'https://www.pracuj.pl/praca/junior-developer'
    
    def test_extract_job_with_logo_fallback(self, job_html_with_logo_fallback):
        """Test extracting job offer where company name comes from logo alt text."""
        soup = BeautifulSoup(job_html_with_logo_fallback, 'html.parser')
        offer_element = soup.find('div', attrs={'data-test-offerid': True})
        
        result = extract_job_offer(offer_element, "https://www.pracuj.pl")
        
        assert result is not None
        assert result['offer_id'] == 'LOGO123'
        assert result['position'] == 'UI/UX Designer'
        assert result['company'] == 'Design Studio Pro'  # From logo alt text
        assert result['city'] == 'Gdańsk'
    
    def test_extract_incomplete_job_offer(self, incomplete_job_html):
        """Test extracting an incomplete job offer should return None."""
        soup = BeautifulSoup(incomplete_job_html, 'html.parser')
        offer_element = soup.find('div', attrs={'data-test-offerid': True})
        
        result = extract_job_offer(offer_element, "https://www.pracuj.pl")
        
        assert result is None  # Should return None for incomplete offers
    
    def test_extract_job_with_relative_url(self, minimal_job_html):
        """Test that relative URLs are converted to absolute URLs."""
        soup = BeautifulSoup(minimal_job_html, 'html.parser')
        offer_element = soup.find('div', attrs={'data-test-offerid': True})
        
        result = extract_job_offer(offer_element, "https://www.pracuj.pl/search")
        
        assert result is not None
        assert result['offer_link'].startswith('https://www.pracuj.pl/')
    
    def test_extract_job_date_parsing(self):
        """Test various Polish date formats."""
        test_cases = [
            ("Opublikowana: 21 czerwca 2025", "21.06.2025"),
            ("Opublikowana: 1 stycznia 2025", "01.01.2025"),
            ("Opublikowana: 15 grudnia 2024", "15.12.2024"),
        ]
        
        for date_text, expected in test_cases:
            html = f"""
            <div data-test-offerid="DATE123">
                <h2 data-test="offer-title"><a href="/test">Test Position</a></h2>
                <div data-test="section-company">
                    <h3 data-test="text-company-name">Test Company</h3>
                </div>
                <h4 data-test="text-region">Test City</h4>
                <p data-test="text-added">{date_text}</p>
            </div>
            """
            
            soup = BeautifulSoup(html, 'html.parser')
            offer_element = soup.find('div', attrs={'data-test-offerid': True})
            
            result = extract_job_offer(offer_element, "https://www.pracuj.pl")
            
            assert result is not None
            assert result['date_added'] == expected
    
    def test_extract_job_with_whitespace_cleanup(self):
        """Test that extracted text is properly cleaned of whitespace."""
        html = """
        <div data-test-offerid="WHITESPACE123">
            <h2 data-test="offer-title">
                <a href="/test">  Senior  Python  Developer  </a>
            </h2>
            <div data-test="section-company">
                <h3 data-test="text-company-name">  TechCorp  Solutions  </h3>
            </div>
            <h4 data-test="text-region">  Warszawa  </h4>
            <span data-test="offer-salary">  15000  -  20000  PLN  </span>
        </div>
        """
        
        soup = BeautifulSoup(html, 'html.parser')
        offer_element = soup.find('div', attrs={'data-test-offerid': True})
        
        result = extract_job_offer(offer_element, "https://www.pracuj.pl")
        
        assert result is not None
        assert result['position'] == 'Senior Python Developer'
        assert result['company'] == 'TechCorp Solutions'
        assert result['city'] == 'Warszawa'
        assert result['salary'] == '15000 - 20000 PLN'
    
    def test_extract_job_missing_offer_id(self):
        """Test handling of missing offer ID."""
        html = """
        <div>
            <h2 data-test="offer-title"><a href="/test">Test Position</a></h2>
            <div data-test="section-company">
                <h3 data-test="text-company-name">Test Company</h3>
            </div>
            <h4 data-test="text-region">Test City</h4>
        </div>
        """
        
        soup = BeautifulSoup(html, 'html.parser')
        offer_element = soup.find('div')
        
        result = extract_job_offer(offer_element, "https://www.pracuj.pl")
        
        assert result is not None
        assert result['offer_id'] == 'N/A'  # Should handle missing offer ID gracefully


class TestHeaders:
    """Test HTTP headers generation."""
    
    def test_get_headers_structure(self):
        """Test that get_headers returns proper structure."""
        headers = get_headers()
        
        assert isinstance(headers, dict)
        assert 'User-Agent' in headers
        assert 'Accept' in headers
        assert 'Accept-Encoding' in headers
        assert 'Host' in headers
        
        # Check specific values
        assert 'Chrome' in headers['User-Agent']
        assert headers['Host'] == 'www.pracuj.pl'
        assert 'gzip' in headers['Accept-Encoding']
    
    def test_get_headers_consistency(self):
        """Test that get_headers returns consistent results."""
        headers1 = get_headers()
        headers2 = get_headers()
        
        assert headers1 == headers2