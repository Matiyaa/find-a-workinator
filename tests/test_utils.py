"""
Unit tests for utility functions in find_a_workinator.py
"""
import pytest
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from find_a_workinator import clean_text, build_url


class TestCleanText:
    """Test cases for the clean_text function."""
    
    def test_clean_text_basic(self):
        """Test basic text cleaning functionality."""
        result = clean_text("  Hello World  ")
        assert result == "Hello World"
    
    def test_clean_text_non_breaking_spaces(self):
        """Test removal of non-breaking spaces."""
        result = clean_text("Hello\xa0\xa0World")
        assert result == "Hello World"
    
    def test_clean_text_multiple_whitespace(self):
        """Test collapsing multiple whitespace characters."""
        result = clean_text("Hello   \n\t  World")
        assert result == "Hello World"
    
    def test_clean_text_empty_string(self):
        """Test handling of empty string."""
        result = clean_text("")
        assert result == ""
    
    def test_clean_text_none(self):
        """Test handling of None input."""
        result = clean_text(None)
        assert result == ""
    
    def test_clean_text_only_whitespace(self):
        """Test handling of string with only whitespace."""
        result = clean_text("   \n\t  ")
        assert result == ""
    
    def test_clean_text_complex_case(self):
        """Test complex case with mixed whitespace and non-breaking spaces."""
        result = clean_text("  Python\xa0Developer\n\n  Remote\t\t  ")
        assert result == "Python Developer Remote"


class TestBuildUrl:
    """Test cases for the build_url function."""
    
    def test_build_url_basic(self):
        """Test basic URL building without parameters."""
        result = build_url()
        assert result == "https://www.pracuj.pl/praca"
    
    def test_build_url_with_keywords(self):
        """Test URL building with keywords."""
        result = build_url(keywords="python developer")
        assert result == "https://www.pracuj.pl/praca/python%20developer;kw"
    
    def test_build_url_with_city(self):
        """Test URL building with city."""
        result = build_url(city="warszawa")
        assert result == "https://www.pracuj.pl/praca/warszawa;wp"
    
    def test_build_url_with_keywords_and_city(self):
        """Test URL building with both keywords and city."""
        result = build_url(keywords="python", city="warszawa")
        assert result == "https://www.pracuj.pl/praca/python;kw/warszawa;wp"
    
    def test_build_url_with_distance(self):
        """Test URL building with distance parameter."""
        result = build_url(city="warszawa", distance=50)
        assert result == "https://www.pracuj.pl/praca/warszawa;wp?rd=50"
    
    def test_build_url_with_page(self):
        """Test URL building with page parameter."""
        result = build_url(page=2)
        assert result == "https://www.pracuj.pl/praca?pn=2"
    
    def test_build_url_all_parameters(self):
        """Test URL building with all parameters."""
        result = build_url(
            keywords="python developer",
            city="warszawa",
            distance=25,
            page=3
        )
        expected = "https://www.pracuj.pl/praca/python%20developer;kw/warszawa;wp?rd=25&pn=3"
        assert result == expected
    
    def test_build_url_special_characters(self):
        """Test URL building with special characters in keywords."""
        result = build_url(keywords="C++ developer")
        assert result == "https://www.pracuj.pl/praca/C%2B%2B%20developer;kw"
    
    def test_build_url_polish_city(self):
        """Test URL building with Polish city name."""
        result = build_url(city="kraków")
        assert result == "https://www.pracuj.pl/praca/krak%C3%B3w;wp"
    
    def test_build_url_page_one_no_param(self):
        """Test that page=1 doesn't add query parameter."""
        result = build_url(keywords="python", page=1)
        assert result == "https://www.pracuj.pl/praca/python;kw"
        assert "pn=" not in result