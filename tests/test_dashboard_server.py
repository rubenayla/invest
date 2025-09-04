"""Tests for dashboard server endpoints and functionality."""

import json
import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.dashboard_server import DashboardHandler


class TestDashboardServer(unittest.TestCase):
    """Test dashboard server HTTP endpoints."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.handler = Mock(spec=DashboardHandler)
        self.handler.dashboard_dir = Path('dashboard')
        self.handler.send_response = Mock()
        self.handler.send_header = Mock()
        self.handler.end_headers = Mock()
        self.handler.wfile = Mock()
        
    def test_serve_dashboard_data(self):
        """Test serving dashboard JSON data."""
        mock_data = {'stocks': {'AAPL': {'ticker': 'AAPL', 'market_cap': 3000000000000}}}
        
        with patch('builtins.open', unittest.mock.mock_open(read_data=json.dumps(mock_data))):
            with patch('scripts.dashboard_server.DashboardHandler.__init__', return_value=None):
                handler = DashboardHandler(None, None, None)
                handler.dashboard_dir = Path('dashboard')
                handler.send_response = Mock()
                handler.send_header = Mock()
                handler.end_headers = Mock()
                handler.wfile = Mock()
                
                handler.serve_dashboard_data()
                
                handler.send_response.assert_called_with(200)
                handler.send_header.assert_any_call('Content-type', 'application/json')
                handler.wfile.write.assert_called()
    
    def test_get_existing_stock_count(self):
        """Test counting existing stocks."""
        mock_data = {
            'stocks': {
                'AAPL': {'ticker': 'AAPL'},
                'GOOGL': {'ticker': 'GOOGL'},
                'MSFT': {'ticker': 'MSFT'}
            }
        }
        
        with patch('builtins.open', unittest.mock.mock_open(read_data=json.dumps(mock_data))):
            with patch('scripts.dashboard_server.DashboardHandler.__init__', return_value=None):
                handler = DashboardHandler(None, None, None)
                handler.dashboard_dir = Path('dashboard')
                count = handler.get_existing_stock_count()
                assert count == 3
    
    def test_handle_update_request(self):
        """Test update endpoint."""
        with patch('scripts.dashboard_server.DashboardHandler.__init__', return_value=None):
            handler = DashboardHandler(None, None, None)
            handler.dashboard_dir = Path('dashboard')
            handler.rfile = Mock()
            handler.rfile.read.return_value = json.dumps({'universe': 'sp500'}).encode()
            handler.headers = {'Content-Length': '100'}
            handler.send_response = Mock()
            handler.send_header = Mock()
            handler.end_headers = Mock()
            handler.wfile = Mock()
            # Add required HTTP server attributes
            handler.path = '/update'
            handler.client_address = ('127.0.0.1', 8000)
            handler.log_error = Mock()
            handler.send_error = Mock()
            # Add the two_step_update method
            handler.two_step_update = Mock(return_value={'status': 'started', 'estimated_stocks': 100})
            
            handler.handle_update()
            
            handler.send_response.assert_called_with(200)
            handler.wfile.write.assert_called()


if __name__ == '__main__':
    unittest.main()