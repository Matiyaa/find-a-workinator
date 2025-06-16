"""
Database manager for Find-a-workinator.

This module provides functions for managing the SQLite database that stores
scraped job offers. It handles database connection, schema creation, and
CRUD operations for job offers.
"""

import sqlite3
import os
from datetime import datetime
from typing import Dict, List, Optional, Union, Any, Tuple

# Import custom logger setup
from logger import setup_logger

# Set up logger
logger = setup_logger(name='db_manager')

# Default database path
DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'job_offers.db')

def initialize_database(db_path: str = DEFAULT_DB_PATH) -> None:
    """
    Initialize the SQLite database with the required schema.

    Args:
        db_path (str): Path to the SQLite database file
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create job_offers table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS job_offers (
            offer_id TEXT PRIMARY KEY,
            company TEXT NOT NULL,
            position TEXT NOT NULL,
            city TEXT NOT NULL,
            salary TEXT,
            offer_link TEXT NOT NULL,
            date_added TEXT NOT NULL,
            date_scraped TEXT NOT NULL,
            search_city TEXT,
            search_distance INTEGER
        )
        ''')

        # Create indexes for faster queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_company ON job_offers(company)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_position ON job_offers(position)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_city ON job_offers(city)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_date_added ON job_offers(date_added)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_date_scraped ON job_offers(date_scraped)')

        conn.commit()
        logger.info(f"Database initialized successfully at {db_path}")
    except sqlite3.Error as e:
        logger.error(f"Error initializing database: {e}", exc_info=True)
        raise
    finally:
        if conn:
            conn.close()

def connect_to_database(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """
    Connect to the SQLite database.

    Args:
        db_path (str): Path to the SQLite database file

    Returns:
        sqlite3.Connection: Database connection object
    """
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        logger.debug(f"Connected to database at {db_path}")
        return conn
    except sqlite3.Error as e:
        logger.error(f"Error connecting to database: {e}", exc_info=True)
        raise

def close_database(conn: sqlite3.Connection) -> None:
    """
    Close the database connection.

    Args:
        conn (sqlite3.Connection): Database connection to close
    """
    if conn:
        conn.close()
        logger.debug("Database connection closed")

def check_duplicate(conn: sqlite3.Connection, offer_id: str) -> bool:
    """
    Check if a job offer with the given ID already exists in the database.

    Args:
        conn (sqlite3.Connection): Database connection
        offer_id (str): Job offer ID to check

    Returns:
        bool: True if the offer exists, False otherwise
    """
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM job_offers WHERE offer_id = ?", (offer_id,))
        return cursor.fetchone() is not None
    except sqlite3.Error as e:
        logger.error(f"Error checking for duplicate offer: {e}", exc_info=True)
        return False

def save_job_offer(conn: sqlite3.Connection, job_offer: Dict[str, Any], 
                  search_params: Dict[str, Any] = None) -> bool:
    """
    Save a job offer to the database.

    Args:
        conn (sqlite3.Connection): Database connection
        job_offer (Dict[str, Any]): Job offer data
        search_params (Dict[str, Any], optional): Search parameters used to find this offer

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Check if offer already exists
        if check_duplicate(conn, job_offer['offer_id']):
            logger.info(f"Offer {job_offer['offer_id']} already exists in database, skipping")
            return False

        cursor = conn.cursor()

        # Add current timestamp for when the offer was scraped
        date_scraped = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # Extract search parameters if provided
        search_city = search_params.get('city') if search_params else None
        search_distance = search_params.get('distance') if search_params else None

        cursor.execute('''
        INSERT INTO job_offers (
            offer_id, company, position, city, salary, offer_link, date_added, 
            date_scraped, search_city, search_distance
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            job_offer['offer_id'],
            job_offer['company'],
            job_offer['position'],
            job_offer['city'],
            job_offer['salary'],
            job_offer['offer_link'],
            job_offer['date_added'],
            date_scraped,
            search_city,
            search_distance
        ))

        conn.commit()
        logger.info(f"Saved job offer {job_offer['offer_id']} to database")
        return True
    except sqlite3.Error as e:
        logger.error(f"Error saving job offer: {e}", exc_info=True)
        conn.rollback()
        return False

def save_job_offers(conn: sqlite3.Connection, job_offers: List[Dict[str, Any]], 
                   search_params: Dict[str, Any] = None) -> Tuple[int, int]:
    """
    Save multiple job offers to the database.

    Args:
        conn (sqlite3.Connection): Database connection
        job_offers (List[Dict[str, Any]]): List of job offer data
        search_params (Dict[str, Any], optional): Search parameters used to find these offers

    Returns:
        Tuple[int, int]: (number of offers saved, number of duplicates skipped)
    """
    saved_count = 0
    duplicate_count = 0

    for offer in job_offers:
        if save_job_offer(conn, offer, search_params):
            saved_count += 1
        else:
            duplicate_count += 1

    logger.info(f"Saved {saved_count} new job offers, skipped {duplicate_count} duplicates")
    return saved_count, duplicate_count

def get_job_offer(conn: sqlite3.Connection, offer_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve a specific job offer by ID.

    Args:
        conn (sqlite3.Connection): Database connection
        offer_id (str): Job offer ID

    Returns:
        Optional[Dict[str, Any]]: Job offer data or None if not found
    """
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM job_offers WHERE offer_id = ?", (offer_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    except sqlite3.Error as e:
        logger.error(f"Error retrieving job offer: {e}", exc_info=True)
        return None

def get_job_offers(conn: sqlite3.Connection, filters: Dict[str, Any] = None, 
                  limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """
    Retrieve job offers based on filters.

    Args:
        conn (sqlite3.Connection): Database connection
        filters (Dict[str, Any], optional): Filters to apply (company, position, city, date_from, date_to)
        limit (int, optional): Maximum number of offers to retrieve
        offset (int, optional): Number of offers to skip

    Returns:
        List[Dict[str, Any]]: List of job offers
    """
    try:
        cursor = conn.cursor()

        query = "SELECT * FROM job_offers"
        params = []

        # Apply filters if provided
        if filters:
            conditions = []

            if 'company' in filters and filters['company']:
                conditions.append("company LIKE ?")
                params.append(f"%{filters['company']}%")

            if 'position' in filters and filters['position']:
                conditions.append("position LIKE ?")
                params.append(f"%{filters['position']}%")

            if 'city' in filters and filters['city']:
                conditions.append("city LIKE ?")
                params.append(f"%{filters['city']}%")

            if 'date_from' in filters and filters['date_from']:
                conditions.append("date_added >= ?")
                params.append(filters['date_from'])

            if 'date_to' in filters and filters['date_to']:
                conditions.append("date_added <= ?")
                params.append(filters['date_to'])

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

        # Add ordering and limits
        query += " ORDER BY date_scraped DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except sqlite3.Error as e:
        logger.error(f"Error retrieving job offers: {e}", exc_info=True)
        return []

def delete_job_offer(conn: sqlite3.Connection, offer_id: str) -> bool:
    """
    Delete a specific job offer.

    Args:
        conn (sqlite3.Connection): Database connection
        offer_id (str): Job offer ID

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM job_offers WHERE offer_id = ?", (offer_id,))
        conn.commit()

        if cursor.rowcount > 0:
            logger.info(f"Deleted job offer {offer_id} from database")
            return True
        else:
            logger.warning(f"No job offer with ID {offer_id} found to delete")
            return False
    except sqlite3.Error as e:
        logger.error(f"Error deleting job offer: {e}", exc_info=True)
        conn.rollback()
        return False

def export_to_csv(conn: sqlite3.Connection, filepath: str, 
                 filters: Dict[str, Any] = None) -> bool:
    """
    Export job offers to a CSV file.

    Args:
        conn (sqlite3.Connection): Database connection
        filepath (str): Path to save the CSV file
        filters (Dict[str, Any], optional): Filters to apply

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        import csv

        # Get job offers with filters
        job_offers = get_job_offers(conn, filters, limit=10000)  # Higher limit for export

        if not job_offers:
            logger.warning("No job offers to export")
            return False

        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            # Get field names from the first offer
            fieldnames = job_offers[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for offer in job_offers:
                writer.writerow(offer)

        logger.info(f"Exported {len(job_offers)} job offers to {filepath}")
        return True
    except Exception as e:
        logger.error(f"Error exporting to CSV: {e}", exc_info=True)
        return False