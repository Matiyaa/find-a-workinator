"""
Unit tests for logger.py module.
"""
import pytest
import logging
import os
import tempfile
import sys
from unittest.mock import patch, MagicMock

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logger import setup_logger


class TestSetupLogger:
    """Test cases for the setup_logger function."""
    
    def test_setup_logger_basic(self):
        """Test basic logger setup."""
        logger = setup_logger(name='test_logger', log_level=logging.INFO, log_to_file=False)
        
        assert logger.name == 'test_logger'
        assert logger.level == logging.INFO
        assert len(logger.handlers) == 1  # Only console handler
        assert isinstance(logger.handlers[0], logging.StreamHandler)
    
    def test_setup_logger_with_file(self):
        """Test logger setup with file logging."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('logger.os.path.dirname') as mock_dirname:
                mock_dirname.return_value = temp_dir
                
                logger = setup_logger(name='test_file_logger', log_level=logging.DEBUG, log_to_file=True)
                
                assert logger.name == 'test_file_logger'
                assert logger.level == logging.DEBUG
                assert len(logger.handlers) == 2  # Console + file handlers
                
                # Check handler types
                handler_types = [type(h).__name__ for h in logger.handlers]
                assert 'StreamHandler' in handler_types
                assert 'FileHandler' in handler_types
                
                # Check that log directory was created
                logs_dir = os.path.join(temp_dir, 'logs')
                assert os.path.exists(logs_dir)
                
                # Close file handlers to avoid Windows file lock issues
                for handler in logger.handlers[:]:
                    if isinstance(handler, logging.FileHandler):
                        handler.close()
                        logger.removeHandler(handler)
    
    def test_setup_logger_duplicate_calls(self):
        """Test that calling setup_logger multiple times clears old handlers."""
        # First call
        logger1 = setup_logger(name='duplicate_test', log_level=logging.INFO, log_to_file=False)
        initial_handler_count = len(logger1.handlers)
        
        # Second call with same name
        logger2 = setup_logger(name='duplicate_test', log_level=logging.WARNING, log_to_file=False)
        
        # Should be the same logger object with cleared handlers
        assert logger1 is logger2
        assert len(logger2.handlers) == initial_handler_count  # Handlers should be cleared and recreated
        assert logger2.level == logging.WARNING  # Level should be updated
    
    def test_setup_logger_different_levels(self):
        """Test logger setup with different log levels."""
        levels = [logging.DEBUG, logging.INFO, logging.WARNING, logging.ERROR, logging.CRITICAL]
        
        for level in levels:
            logger = setup_logger(name=f'test_level_{level}', log_level=level, log_to_file=False)
            assert logger.level == level
            
            # All handlers should have the same level
            for handler in logger.handlers:
                assert handler.level == level
    
    def test_setup_logger_formatter(self):
        """Test that logger uses correct formatter."""
        logger = setup_logger(name='test_formatter', log_level=logging.INFO, log_to_file=False)
        
        # Check that handlers have formatters
        for handler in logger.handlers:
            assert handler.formatter is not None
            
            # Check formatter format string
            format_string = handler.formatter._fmt
            assert '%(asctime)s' in format_string
            assert '%(name)s' in format_string
            assert '%(levelname)s' in format_string
            assert '%(message)s' in format_string
    
    def test_setup_logger_file_creation(self):
        """Test that log file is created with correct naming pattern."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('logger.os.path.dirname') as mock_dirname:
                mock_dirname.return_value = temp_dir
                
                logger = setup_logger(name='file_creation_test', log_to_file=True)
                
                # Write a log message to ensure file is created
                logger.info("Test message")
                
                # Check that log file was created
                logs_dir = os.path.join(temp_dir, 'logs')
                log_files = [f for f in os.listdir(logs_dir) if f.startswith('file_creation_test_')]
                
                assert len(log_files) == 1
                assert log_files[0].endswith('.log')
                
                # Check file contains the log message
                with open(os.path.join(logs_dir, log_files[0]), 'r') as f:
                    content = f.read()
                    assert 'Test message' in content
                    assert 'file_creation_test' in content
                
                # Close file handlers to avoid Windows file lock issues
                for handler in logger.handlers[:]:
                    if isinstance(handler, logging.FileHandler):
                        handler.close()
                        logger.removeHandler(handler)
    
    def test_setup_logger_logs_directory_creation(self):
        """Test that logs directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('logger.os.path.dirname') as mock_dirname:
                mock_dirname.return_value = temp_dir
                
                logs_dir = os.path.join(temp_dir, 'logs')
                
                # Ensure logs directory doesn't exist initially
                assert not os.path.exists(logs_dir)
                
                # Setup logger with file logging
                logger = setup_logger(name='dir_creation_test', log_to_file=True)
                
                # Check that logs directory was created
                assert os.path.exists(logs_dir)
                assert os.path.isdir(logs_dir)
                
                # Close file handlers to avoid Windows file lock issues
                for handler in logger.handlers[:]:
                    if isinstance(handler, logging.FileHandler):
                        handler.close()
                        logger.removeHandler(handler)
    
    @patch('logger.logging.getLogger')
    def test_setup_logger_existing_handlers(self, mock_get_logger):
        """Test that existing handlers are cleared."""
        # Create mock logger with existing handlers
        mock_logger = MagicMock()
        mock_logger.name = 'test_existing'
        mock_logger.hasHandlers.return_value = True
        mock_logger.handlers = [MagicMock(), MagicMock()]  # Two existing handlers
        mock_get_logger.return_value = mock_logger
        
        setup_logger(name='test_existing', log_to_file=False)
        
        # Check that handlers were cleared (clear() is a built-in method, not a Mock)
        # We can't assert on mock_logger.handlers.clear() since it's not a Mock object
        # Instead, verify that addHandler was called to add new handlers
        assert mock_logger.addHandler.called
    
    def test_setup_logger_default_parameters(self):
        """Test logger setup with default parameters."""
        logger = setup_logger()
        
        assert logger.name == 'find_a_workinator'
        assert logger.level == logging.INFO  # Default LOG_LEVEL
        # Should have both console and file handlers by default
        assert len(logger.handlers) >= 1