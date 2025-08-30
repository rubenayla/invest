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
from typing import List
import json
import subprocess
import logging
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
        """Handle update and sorting requests."""
        if self.path == '/update':
            self.handle_update()
        elif self.path == '/sort':
            self.handle_sort()
        else:
            self.send_error(404)
    
    def handle_update(self):
        """Handle dashboard update request with universe selection."""
        try:
            # Parse request body to get universe selection
            content_length = int(self.headers.get('Content-Length', 0))
            request_body = self.rfile.read(content_length).decode('utf-8')
            
            # Default to S&P 500 if no universe specified
            universe = 'sp500'
            if request_body:
                try:
                    request_data = json.loads(request_body)
                    universe = request_data.get('universe', 'sp500')
                except json.JSONDecodeError:
                    pass
            
            # Run dashboard update in background thread
            def update_dashboard():
                try:
                    tickers = get_universe_tickers(universe)
                    logger.info(f"Updating dashboard with {len(tickers)} stocks from {universe}")
                    
                    # Create a temporary config and run systematic analysis
                    config_path = create_temp_config(tickers, universe)
                    run_systematic_analysis_for_dashboard(config_path)
                    logger.info("Dashboard updated successfully via systematic analysis")
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
            self.wfile.write(json.dumps({
                'status': 'update_started',
                'universe': universe,
                'estimated_stocks': len(get_universe_tickers(universe))
            }).encode())
            
        except Exception as e:
            self.send_error(500, f"Update failed: {e}")
    
    def handle_sort(self):
        """Handle dashboard sorting request."""
        try:
            # Parse request body to get sort parameters
            content_length = int(self.headers.get('Content-Length', 0))
            request_body = self.rfile.read(content_length).decode('utf-8')
            
            sort_params = {'column': 'composite_score', 'direction': 'desc'}
            if request_body:
                try:
                    request_data = json.loads(request_body)
                    sort_params.update(request_data)
                except json.JSONDecodeError:
                    pass
            
            # Get sorted data
            sorted_data = get_sorted_dashboard_data(sort_params['column'], sort_params['direction'])
            
            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(sorted_data).encode())
            
        except Exception as e:
            self.send_error(500, f"Sorting failed: {e}")


def get_universe_tickers(universe: str) -> List[str]:
    """Get tickers dynamically from configs and existing data."""
    from src.invest.config.loader import load_analysis_config, list_available_configs
    import glob
    
    # Load from existing dashboard data  
    existing_tickers = []
    dashboard_data_path = get_dashboard_dir() / 'dashboard_data.json'
    
    if dashboard_data_path.exists():
        try:
            with open(dashboard_data_path, 'r') as f:
                data = json.load(f)
                existing_tickers = list(data.get('stocks', {}).keys())
                logger.info(f"Found {len(existing_tickers)} existing tickers in dashboard data")
        except Exception as e:
            logger.warning(f"Could not load existing dashboard data: {e}")
    
    # Clean universe to config mapping
    universe_configs = {
        'sp500': ['sp500_top100.yaml', 'sp500_subset.yaml'],
        'international': ['international_value.yaml', 'mixed_international.yaml'], 
        'japan': ['japan_buffett_favorites.yaml', 'japan_topix30.yaml'],
        'growth': ['aggressive_growth.yaml'],
        'mixed': ['simple_mixed.yaml', 'mixed_international.yaml'],
        'tech': ['test_tech_giants.yaml'],
        'watchlist': ['watchlist_analysis.yaml'],
    }
    
    # Handle existing data
    if universe == 'existing' and existing_tickers:
        return existing_tickers[:50]
    
    # Load tickers from configs
    tickers = load_tickers_from_configs(universe_configs.get(universe, ['simple_mixed.yaml']))
    
    # Fallback to existing + defaults
    if not tickers:
        fallback = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', '7203.T', 'ASML.AS']
        tickers = (existing_tickers + fallback)[:30]
        logger.info("Using fallback tickers")
    
    return list(dict.fromkeys(tickers))[:50]  # Unique + limited


def load_tickers_from_configs(config_files):
    """Load tickers from config files - cleaner than inline logic"""
    from pathlib import Path
    configs_dir = Path(__file__).parent.parent / 'configs'
    
    for config_file in config_files:
        config_path = configs_dir / config_file
        if not config_path.exists():
            continue
            
        try:
            config = load_analysis_config(config_path)
            if hasattr(config.universe, 'custom_tickers') and config.universe.custom_tickers:
                logger.info(f"Loaded {len(config.universe.custom_tickers)} tickers from {config_file}")
                return config.universe.custom_tickers
        except Exception as e:
            logger.warning(f"Could not load config {config_file}: {e}")
    
    return []


def create_temp_config(tickers: List[str], universe_name: str) -> str:
    """Create a temporary config file for dashboard analysis."""
    import tempfile
    import yaml
    
    # Clean config template  
    config = {
        'name': f'dashboard_{universe_name}',
        'description': f'Dashboard analysis for {universe_name} universe',
        'universe': {'region': 'ALL', 'custom_tickers': tickers},
        'value': {'max_pe': 50, 'max_pb': 10, 'max_ev_ebitda': 30},
        'quality': {'min_roe': 0.05, 'min_current_ratio': 0.8, 'max_debt_equity': 3.0},
        'growth': {'min_revenue_growth': -0.20, 'min_earnings_growth': -0.20},
        'generate_reports': True,
        'save_data': True,
        'max_results': len(tickers),
        'sort_by': 'composite_score'
    }
    
    # Write to temp file
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
    yaml.dump(config, temp_file, default_flow_style=False)
    temp_file.close()
    
    logger.info(f"Created temp config: {temp_file.name}")
    return temp_file.name


def run_systematic_analysis_for_dashboard(config_path: str):
    """Run systematic analysis and update dashboard data."""
    try:
        # Import and run the systematic analysis
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from scripts.systematic_analysis import run_analysis
        
        # Create a mock args object
        class MockArgs:
            def __init__(self):
                self.output = None
                self.save_json = False
                self.save_csv = False
                self.quiet = True
                self.verbose = False
        
        mock_args = MockArgs()
        
        # Run analysis
        results = run_analysis(config_path, mock_args)
        
        # Convert results to dashboard format and save
        dashboard_data = convert_analysis_to_dashboard_format(results)
        save_dashboard_data(dashboard_data)
        
        # Clean up temp file
        os.unlink(config_path)
        
    except Exception as e:
        logger.error(f"Systematic analysis failed: {e}")
        raise


def convert_analysis_to_dashboard_format(results: dict) -> dict:
    """Convert systematic analysis results to dashboard data format."""
    return {
        'last_updated': datetime.now().isoformat(),
        'stocks': {
            stock.get('ticker', ''): create_dashboard_stock(stock)
            for stock in results.get('stocks', [])
        }
    }


def create_dashboard_stock(stock):
    """Create dashboard format for a single stock - cleaner than inline dict"""
    ticker = stock.get('ticker', '')
    return {
        'ticker': ticker,
        'status': 'completed',
        'status_message': 'Analysis completed successfully',
        'current_price': stock.get('current_price', 0),
        'company_name': stock.get('longName', ticker),
        'sector': stock.get('sector', 'Unknown'),
        'market_cap': stock.get('market_cap', 0),
        'composite_score': stock.get('composite_score', 0),
        'value_score': stock.get('value_score', 0),
        'quality_score': stock.get('quality_score', 0),
        'growth_score': stock.get('growth_score', 0),
        'financial_metrics': {
            'trailing_pe': stock.get('trailing_pe', 0),
            'price_to_book': stock.get('price_to_book', 0),
            'return_on_equity': stock.get('return_on_equity', 0),
            'debt_to_equity': stock.get('debt_to_equity', 0),
            'current_ratio': stock.get('current_ratio', 0)
        },
        'valuations': {
            'dcf': {
                'fair_value': stock.get('dcf_value', 0),
                'current_price': stock.get('current_price', 0),
                'margin_of_safety': stock.get('margin_of_safety', 0),
                'confidence': 'medium'
            }
        }
    }


def save_dashboard_data(dashboard_data: dict):
    """Save dashboard data to the standard location."""
    dashboard_dir = get_dashboard_dir()
    data_file = dashboard_dir / 'dashboard_data.json'
    
    with open(data_file, 'w') as f:
        json.dump(dashboard_data, f, indent=2)
    
    logger.info(f"Dashboard data saved to {data_file}")


def get_dashboard_dir():
    """Get dashboard directory path - cleaner than inline path joins"""
    from pathlib import Path
    dashboard_dir = Path(__file__).parent.parent / 'dashboard'
    dashboard_dir.mkdir(exist_ok=True)
    return dashboard_dir


def get_sorted_dashboard_data(sort_column: str, direction: str = 'desc') -> dict:
    """Get dashboard data sorted by specified column."""
    data_file = get_dashboard_dir() / 'dashboard_data.json'
    
    if not data_file.exists():
        return {'error': 'No dashboard data available'}
    
    try:
        with open(data_file, 'r') as f:
            dashboard_data = json.load(f)
        
        stocks = dashboard_data.get('stocks', {})
        if not stocks:
            return {'error': 'No stock data available'}
        
        # Convert to list for sorting
        stock_list = []
        for ticker, data in stocks.items():
            stock_list.append(data)
        
        # Clean column mapping - much better than elif hell
        def get_sort_key(stock):
            column_paths = {
                'ticker': ('ticker', ''),
                'company_name': ('company_name', stock.get('ticker', '')),
                'current_price': ('current_price', 0),
                'market_cap': ('market_cap', 0),
                'composite_score': ('composite_score', 0),
                'value_score': ('value_score', 0),
                'quality_score': ('quality_score', 0),
                'growth_score': ('growth_score', 0),
                'sector': ('sector', ''),
                'dcf_fair_value': ('valuations.dcf.fair_value', 0),
                'dcf_margin_safety': ('valuations.dcf.margin_of_safety', 0),
                'pe_ratio': ('financial_metrics.trailing_pe', 0),
                'pb_ratio': ('financial_metrics.price_to_book', 0),
                'roe': ('financial_metrics.return_on_equity', 0),
                'debt_equity': ('financial_metrics.debt_to_equity', 0),
            }
            
            path, default = column_paths.get(sort_column, ('composite_score', 0))
            return get_nested_value(stock, path, default)
        
        def get_nested_value(obj, path, default):
            """Clean nested dict access"""
            for key in path.split('.'):
                obj = obj.get(key, {}) if isinstance(obj, dict) else default
            return obj if obj != {} else default
        
        # Sort the stock list
        reverse_sort = (direction.lower() == 'desc')
        stock_list.sort(key=get_sort_key, reverse=reverse_sort)
        
        # Return sorted data
        result = {
            'stocks': stock_list,
            'sort_column': sort_column,
            'sort_direction': direction,
            'total_stocks': len(stock_list),
            'last_updated': dashboard_data.get('last_updated', datetime.now().isoformat())
        }
        
        logger.info(f"Sorted {len(stock_list)} stocks by {sort_column} ({direction})")
        return result
        
    except Exception as e:
        logger.error(f"Error sorting dashboard data: {e}")
        return {'error': f'Sorting failed: {str(e)}'}


def main():
    """Start the dashboard server."""
    # Check for dashboard HTML
    dashboard_html = get_dashboard_dir() / 'valuation_dashboard.html'
    if not dashboard_html.exists():
        print("❌ Dashboard HTML not found. Please run systematic analysis first to generate dashboard data.")
        print("   Example: poetry run python scripts/systematic_analysis.py configs/simple_mixed.yaml")
        return
    
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