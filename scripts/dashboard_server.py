#!/usr/bin/env python
"""
Investment Dashboard Server - The main way to use the dashboard.

Usage:
    poetry run python scripts/dashboard_server.py
    
Then open: http://localhost:8080

Features:
- Live dashboard at http://localhost:8080
- Click "Update Data" button to refresh valuations
- Tooltips explain all metrics
- Auto-refreshes during updates
"""

import sys
import os
import threading
import time
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse
import json
import subprocess
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.invest.dashboard import ValuationDashboard

logger = logging.getLogger(__name__)

class DashboardHandler(SimpleHTTPRequestHandler):
    """HTTP handler that can serve dashboard and handle updates."""
    
    def __init__(self, *args, **kwargs):
        self.dashboard_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'dashboard')
        super().__init__(*args, directory=self.dashboard_dir, **kwargs)
    
    def do_GET(self):
        """Serve dashboard HTML file."""
        if self.path == '/' or self.path == '':
            self.path = '/valuation_dashboard.html'
        elif self.path == '/favicon.ico':
            # Return empty 204 response for favicon to avoid errors
            self.send_response(204)
            self.end_headers()
            return
        super().do_GET()
    
    def do_POST(self):
        """Handle update requests."""
        if self.path == '/update':
            self.handle_update()
        else:
            self.send_error(404)
    
    def handle_update(self):
        """Handle dashboard update request."""
        try:
            # Run dashboard update in background thread
            def update_dashboard():
                try:
                    # Get full S&P 500 tickers for comprehensive analysis
                    from src.invest.data.yahoo import get_sp500_tickers
                    tickers = get_sp500_tickers()
                    
                    # Use full S&P 500 - complete investment universe
                    # This ensures we don't miss hidden gems in mid/small cap stocks
                    
                    logger.info(f"Updating dashboard with {len(tickers)} stocks from S&P 500")
                    dashboard = ValuationDashboard()
                    dashboard.update_dashboard(tickers, timeout_per_stock=45)
                    logger.info("Dashboard updated successfully")
                except Exception as e:
                    logger.error(f"Dashboard update failed: {e}")
            
            # Start update in background
            update_thread = threading.Thread(target=update_dashboard)
            update_thread.daemon = True
            update_thread.start()
            
            # Send immediate response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'update_started'}).encode())
            
        except Exception as e:
            self.send_error(500, f"Update failed: {e}")
    
    def log_message(self, format, *args):
        """Override to reduce log noise."""
        # Check if first arg is a string and contains noise patterns
        try:
            if args and isinstance(args[0], str):
                if not any(x in args[0] for x in ['.css', '.js', '.ico', 'favicon']):
                    super().log_message(format, *args)
        except:
            # If anything goes wrong, just use default logging
            super().log_message(format, *args)


def main():
    """Start the dashboard server."""
    # Ensure dashboard exists
    dashboard = ValuationDashboard()
    if not dashboard.html_file.exists():
        print("🔧 Creating initial dashboard...")
        dashboard._generate_html()
    
    # Start server
    port = 8080
    server = HTTPServer(('localhost', port), DashboardHandler)
    
    print(f"🚀 Dashboard server starting on http://localhost:{port}")
    print("📊 Opening dashboard in your browser...")
    print("🔄 Click 'Update Data' button to refresh valuations")
    print("⏹️  Press Ctrl+C to stop server")
    
    # Open browser after a short delay
    def open_browser():
        time.sleep(1.5)
        webbrowser.open(f'http://localhost:{port}')
    
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n⏹️  Server stopped")
        server.shutdown()


if __name__ == '__main__':
    main()