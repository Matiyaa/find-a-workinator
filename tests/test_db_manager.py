"""
Unit tests for database operations in db_manager.py
"""
import pytest
import sqlite3
import tempfile
import os
import sys
from datetime import datetime

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db_manager import (
    initialize_database, connect_to_database, close_database,
    check_duplicate, save_job_offer, save_job_offers,
    get_job_offer, get_job_offers, delete_job_offer, export_to_csv
)


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)  # Close the file descriptor
    
    # Initialize the database
    initialize_database(db_path)
    
    yield db_path
    
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def db_connection(temp_db):
    """Create a database connection for testing."""
    conn = connect_to_database(temp_db)
    yield conn
    close_database(conn)


@pytest.fixture
def sample_job_offer():
    """Sample job offer data for testing."""
    return {
        'offer_id': 'TEST001',
        'company': 'Test Company',
        'position': 'Python Developer',
        'city': 'Warszawa',
        'salary': '10000-15000 PLN',
        'offer_link': 'https://www.pracuj.pl/praca/test-offer',
        'date_added': '21.06.2025'
    }


@pytest.fixture
def sample_search_params():
    """Sample search parameters for testing."""
    return {
        'city': 'warszawa',
        'distance': 50
    }


class TestDatabaseInitialization:
    """Test database initialization and connection."""
    
    def test_initialize_database(self, temp_db):
        """Test database initialization creates proper schema."""
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='job_offers'")
        table_exists = cursor.fetchone() is not None
        assert table_exists
        
        # Check table structure
        cursor.execute("PRAGMA table_info(job_offers)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        expected_columns = [
            'offer_id', 'company', 'position', 'city', 'salary',
            'offer_link', 'date_added', 'date_scraped', 'search_city', 'search_distance'
        ]
        
        for col in expected_columns:
            assert col in column_names
        
        conn.close()
    
    def test_connect_to_database(self, temp_db):
        """Test database connection."""
        conn = connect_to_database(temp_db)
        assert isinstance(conn, sqlite3.Connection)
        assert conn.row_factory == sqlite3.Row
        close_database(conn)


class TestJobOfferOperations:
    """Test job offer CRUD operations."""
    
    def test_save_job_offer_new(self, db_connection, sample_job_offer, sample_search_params):
        """Test saving a new job offer."""
        result = save_job_offer(db_connection, sample_job_offer, sample_search_params)
        assert result is True
        
        # Verify the offer was saved
        saved_offer = get_job_offer(db_connection, sample_job_offer['offer_id'])
        assert saved_offer is not None
        assert saved_offer['company'] == sample_job_offer['company']
        assert saved_offer['position'] == sample_job_offer['position']
        assert saved_offer['search_city'] == sample_search_params['city']
        assert saved_offer['search_distance'] == sample_search_params['distance']
    
    def test_save_job_offer_duplicate(self, db_connection, sample_job_offer):
        """Test saving a duplicate job offer."""
        # Save the offer first time
        save_job_offer(db_connection, sample_job_offer)
        
        # Try to save the same offer again
        result = save_job_offer(db_connection, sample_job_offer)
        assert result is False  # Should return False for duplicate
    
    def test_check_duplicate(self, db_connection, sample_job_offer):
        """Test duplicate checking functionality."""
        # Initially should not exist
        assert check_duplicate(db_connection, sample_job_offer['offer_id']) is False
        
        # Save the offer
        save_job_offer(db_connection, sample_job_offer)
        
        # Now should exist
        assert check_duplicate(db_connection, sample_job_offer['offer_id']) is True
    
    def test_save_multiple_job_offers(self, db_connection, sample_search_params):
        """Test saving multiple job offers."""
        offers = [
            {
                'offer_id': 'TEST001',
                'company': 'Company A',
                'position': 'Developer A',
                'city': 'Warszawa',
                'salary': '10000 PLN',
                'offer_link': 'https://example.com/1',
                'date_added': '21.06.2025'
            },
            {
                'offer_id': 'TEST002',
                'company': 'Company B',
                'position': 'Developer B',
                'city': 'Kraków',
                'salary': '12000 PLN',
                'offer_link': 'https://example.com/2',
                'date_added': '20.06.2025'
            }
        ]
        
        saved_count, duplicate_count = save_job_offers(db_connection, offers, sample_search_params)
        
        assert saved_count == 2
        assert duplicate_count == 0
        
        # Try to save the same offers again
        saved_count2, duplicate_count2 = save_job_offers(db_connection, offers, sample_search_params)
        
        assert saved_count2 == 0
        assert duplicate_count2 == 2
    
    def test_get_job_offer(self, db_connection, sample_job_offer):
        """Test retrieving a specific job offer."""
        # Save an offer first
        save_job_offer(db_connection, sample_job_offer)
        
        # Retrieve it
        retrieved = get_job_offer(db_connection, sample_job_offer['offer_id'])
        
        assert retrieved is not None
        assert retrieved['offer_id'] == sample_job_offer['offer_id']
        assert retrieved['company'] == sample_job_offer['company']
        assert retrieved['position'] == sample_job_offer['position']
        assert 'date_scraped' in retrieved  # Should have timestamp
    
    def test_get_job_offer_not_found(self, db_connection):
        """Test retrieving a non-existent job offer."""
        result = get_job_offer(db_connection, 'NONEXISTENT')
        assert result is None
    
    def test_delete_job_offer(self, db_connection, sample_job_offer):
        """Test deleting a job offer."""
        # Save an offer first
        save_job_offer(db_connection, sample_job_offer)
        
        # Delete it
        result = delete_job_offer(db_connection, sample_job_offer['offer_id'])
        assert result is True
        
        # Verify it's gone
        retrieved = get_job_offer(db_connection, sample_job_offer['offer_id'])
        assert retrieved is None
    
    def test_delete_job_offer_not_found(self, db_connection):
        """Test deleting a non-existent job offer."""
        result = delete_job_offer(db_connection, 'NONEXISTENT')
        assert result is False


class TestJobOfferFiltering:
    """Test job offer filtering and querying."""
    
    @pytest.fixture
    def populated_db(self, db_connection):
        """Populate database with test data."""
        offers = [
            {
                'offer_id': 'PYTHON001',
                'company': 'TechCorp',
                'position': 'Python Developer',
                'city': 'Warszawa',
                'salary': '15000 PLN',
                'offer_link': 'https://example.com/python1',
                'date_added': '21.06.2025'
            },
            {
                'offer_id': 'JAVA001',
                'company': 'JavaSoft',
                'position': 'Java Developer',
                'city': 'Kraków',
                'salary': '12000 PLN',
                'offer_link': 'https://example.com/java1',
                'date_added': '20.06.2025'
            },
            {
                'offer_id': 'PYTHON002',
                'company': 'StartupXYZ',
                'position': 'Senior Python Developer',
                'city': 'Warszawa',
                'salary': '20000 PLN',
                'offer_link': 'https://example.com/python2',
                'date_added': '19.06.2025'
            }
        ]
        
        for offer in offers:
            save_job_offer(db_connection, offer)
        
        return db_connection
    
    def test_get_all_offers(self, populated_db):
        """Test retrieving all job offers."""
        offers = get_job_offers(populated_db)
        assert len(offers) == 3
    
    def test_filter_by_company(self, populated_db):
        """Test filtering by company name."""
        offers = get_job_offers(populated_db, filters={'company': 'TechCorp'})
        assert len(offers) == 1
        assert offers[0]['company'] == 'TechCorp'
    
    def test_filter_by_position(self, populated_db):
        """Test filtering by position."""
        offers = get_job_offers(populated_db, filters={'position': 'Python'})
        assert len(offers) == 2
        for offer in offers:
            assert 'Python' in offer['position']
    
    def test_filter_by_city(self, populated_db):
        """Test filtering by city."""
        offers = get_job_offers(populated_db, filters={'city': 'Warszawa'})
        assert len(offers) == 2
        for offer in offers:
            assert offer['city'] == 'Warszawa'
    
    def test_filter_by_date_range(self, populated_db):
        """Test filtering by date range."""
        offers = get_job_offers(populated_db, filters={
            'date_from': '20.06.2025',
            'date_to': '21.06.2025'
        })
        assert len(offers) == 2
    
    def test_multiple_filters(self, populated_db):
        """Test applying multiple filters."""
        offers = get_job_offers(populated_db, filters={
            'position': 'Python',
            'city': 'Warszawa'
        })
        assert len(offers) == 2
        for offer in offers:
            assert 'Python' in offer['position']
            assert offer['city'] == 'Warszawa'
    
    def test_limit_and_offset(self, populated_db):
        """Test limit and offset parameters."""
        offers = get_job_offers(populated_db, limit=2, offset=0)
        assert len(offers) == 2
        
        offers_page2 = get_job_offers(populated_db, limit=2, offset=2)
        assert len(offers_page2) == 1


class TestCSVExport:
    """Test CSV export functionality."""
    
    def test_export_to_csv(self, db_connection, sample_job_offer):
        """Test exporting job offers to CSV."""
        # Save a job offer first
        save_job_offer(db_connection, sample_job_offer)
        
        # Create temporary CSV file
        fd, csv_path = tempfile.mkstemp(suffix='.csv')
        os.close(fd)
        
        try:
            # Export to CSV
            result = export_to_csv(db_connection, csv_path)
            assert result is True
            
            # Verify file was created and has content
            assert os.path.exists(csv_path)
            with open(csv_path, 'r', encoding='utf-8') as f:
                content = f.read()
                assert 'offer_id' in content  # Header
                assert sample_job_offer['offer_id'] in content
                assert sample_job_offer['company'] in content
        
        finally:
            # Cleanup
            if os.path.exists(csv_path):
                os.unlink(csv_path)
    
    def test_export_empty_database(self, db_connection):
        """Test exporting from empty database."""
        fd, csv_path = tempfile.mkstemp(suffix='.csv')
        os.close(fd)
        
        try:
            result = export_to_csv(db_connection, csv_path)
            assert result is False  # Should fail with empty database
        
        finally:
            if os.path.exists(csv_path):
                os.unlink(csv_path)