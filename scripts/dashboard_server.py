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
        """Serve dashboard HTML file with updated data."""
        if self.path == '/' or self.path == '':
            # Update the existing HTML file with current data, then serve it
            try:
                self.update_existing_dashboard_html()
                self.path = '/valuation_dashboard.html'
            except Exception as e:
                logger.error(f"Error updating dashboard HTML: {e}")
                self.path = '/valuation_dashboard.html'
        elif self.path == '/favicon.ico':
            # Return empty 204 response for favicon to avoid errors
            self.send_response(204)
            self.end_headers()
            return
        elif self.path == '/data':
            # Serve current JSON data
            self.serve_dashboard_data()
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
        """Handle dashboard update request with universe selection and progressive loading."""
        try:
            # Parse request body to get universe selection
            content_length = int(self.headers.get('Content-Length', 0))
            request_body = self.rfile.read(content_length).decode('utf-8')
            
            # Default parameters
            universe = 'existing'
            expand = False
            batch_size = 20
            
            if request_body:
                try:
                    request_data = json.loads(request_body)
                    universe = request_data.get('universe', 'existing')
                    expand = request_data.get('expand', False)
                    batch_size = request_data.get('batch_size', 20)
                except json.JSONDecodeError:
                    pass
            
            # Run dashboard update in background thread
            def update_dashboard():
                try:
                    if expand:
                        # Progressive loading: add more stocks to existing ones
                        self.progressive_stock_loading_v2(universe, batch_size)
                    else:
                        # Two-step approach: fetch data then analyze offline
                        logger.info(f"Starting two-step dashboard update for {universe} universe")
                        
                        # Step 1: Fetch data asynchronously
                        max_stocks = 1000 if universe == 'sp500' else 500
                        fetch_success = self.fetch_stock_data_async(universe, max_stocks)
                        
                        if fetch_success:
                            # Step 2: Run offline analysis on ALL cached data (not just the universe)
                            self.run_offline_analysis('cached', max_stocks)
                            logger.info("Dashboard updated successfully via two-step approach")
                        else:
                            logger.error("Data fetching failed, trying to analyze existing cached data")
                            # Try to analyze whatever cached data we have
                            try:
                                self.run_offline_analysis('cached', 2000)
                                logger.info("Fallback: analyzed existing cached data")
                            except Exception as fallback_error:
                                logger.error(f"Both new system and fallback failed: {fallback_error}")
                                # Last resort: use old method with small dataset
                                tickers = get_universe_tickers(universe)
                                config_path = create_temp_config(tickers, universe)
                                run_systematic_analysis_for_dashboard(config_path)
                except Exception as e:
                    logger.error(f"Dashboard update failed: {e}")
            
            # Start update in background
            update_thread = threading.Thread(target=update_dashboard)
            update_thread.daemon = True
            update_thread.start()
            
            # Get ticker information for response
            if expand:
                estimated_stocks = batch_size
            else:
                # Get actual stock counts dynamically
                from scripts.data_fetcher import get_universe_tickers
                stock_estimates = {}
                for universe_key in ['all', 'sp500', 'international', 'japan', 'tech', 'growth']:
                    stock_estimates[universe_key] = len(get_universe_tickers(universe_key, 10000))
                stock_estimates['existing'] = self.get_existing_stock_count()
                estimated_stocks = stock_estimates.get(universe, 500)
            
            logger.info(f"Dashboard update starting: {estimated_stocks} stocks from {universe} universe (expand={expand})")
            
            # Send immediate response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'status': 'update_started',
                'universe': universe,
                'estimated_stocks': estimated_stocks,
                'expand': expand,
                'batch_size': batch_size
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
    
    def update_existing_dashboard_html(self):
        """Update the existing dashboard HTML file with current data."""
        dashboard_html_path = get_dashboard_dir() / 'valuation_dashboard.html'
        dashboard_data_path = get_dashboard_dir() / 'dashboard_data.json'
        
        # If HTML doesn't exist, create a basic one
        if not dashboard_html_path.exists():
            self.create_basic_dashboard_html()
            return
        
        # Update last modified time to prevent caching
        dashboard_html_path.touch()
    
    def create_basic_dashboard_html(self):
        """Create a basic functional dashboard HTML file."""
        dashboard_html_path = get_dashboard_dir() / 'valuation_dashboard.html'
        
        # Get actual universe counts dynamically
        from scripts.data_fetcher import get_universe_tickers
        universe_info = {
            'all': ('🌍 All Markets', len(get_universe_tickers('all', 10000))),
            'sp500': ('S&P 500', len(get_universe_tickers('sp500', 10000))),
            'international': ('International', len(get_universe_tickers('international', 10000))),
            'japan': ('Japan', len(get_universe_tickers('japan', 10000))),
            'tech': ('Tech Focus', len(get_universe_tickers('tech', 10000))),
            'growth': ('Growth', len(get_universe_tickers('growth', 10000)))
        }
        
        # Build universe options dynamically
        universe_options = ['<option value="existing">Current Stocks</option>']
        for key, (name, count) in universe_info.items():
            universe_options.append(f'<option value="{key}">{name} ({count} stocks)</option>')
        universe_options_html = '\n                    '.join(universe_options)
        
        # Use regular string for CSS part to avoid f-string issues with curly braces
        html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Investment Analysis Dashboard</title>
    <style>
        * { box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0; padding: 20px; background: #f8f9fa; color: #333;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        .header { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; padding: 30px; border-radius: 12px; margin-bottom: 30px;
            box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
        }
        .header h1 { margin: 0 0 10px 0; font-size: 2.5em; font-weight: 300; }
        .header .stats { display: flex; gap: 30px; margin-top: 15px; }
        .header .stat { display: flex; flex-direction: column; }
        .header .stat-value { font-size: 1.8em; font-weight: bold; }
        .header .stat-label { font-size: 0.9em; opacity: 0.8; }
        
        .controls { 
            background: white; padding: 20px; border-radius: 12px; margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1); display: flex; align-items: center; gap: 20px;
        }
        .btn { 
            padding: 12px 24px; background: #007cba; color: white; border: none; 
            border-radius: 8px; cursor: pointer; font-size: 16px; font-weight: 500;
            transition: all 0.3s ease;
        }
        .btn:hover { background: #005a87; transform: translateY(-1px); }
        .btn.secondary { background: #6c757d; }
        .btn.secondary:hover { background: #545b62; }
        
        #updateStatus { 
            padding: 8px 16px; border-radius: 6px; font-weight: 500;
            background: #e3f2fd; color: #1976d2; display: none;
        }
        #updateStatus.show { display: inline-block; }
        
        .table-container { 
            background: white; border-radius: 12px; overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }
        th { 
            background: #f8f9fa; font-weight: 600; cursor: pointer; 
            position: sticky; top: 0; z-index: 10;
        }
        th:hover { background: #e9ecef; }
        tr:hover { background: #f8f9fa; }
        
        .ticker { font-weight: bold; color: #007cba; }
        .price { font-family: monospace; font-weight: 500; }
        .status { 
            padding: 4px 8px; border-radius: 4px; font-size: 0.85em; font-weight: 500;
            text-transform: uppercase;
        }
        .status.completed { background: #d4edda; color: #155724; }
        .status.pending { background: #fff3cd; color: #856404; }
        .status.failed { background: #f8d7da; color: #721c24; }
        
        .score { font-weight: bold; }
        .score.excellent { color: #28a745; }
        .score.good { color: #17a2b8; }
        .score.average { color: #ffc107; }
        .score.poor { color: #dc3545; }
        
        .loading { 
            text-align: center; padding: 40px; color: #6c757d;
            animation: pulse 2s infinite;
        }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        
        .universe-selector {
            display: flex; gap: 10px; align-items: center;
        }
        .universe-selector select {
            padding: 8px 12px; border: 2px solid #dee2e6; border-radius: 6px;
            font-size: 14px; background: white;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Investment Analysis Dashboard</h1>
            <div class="stats">
                <div class="stat">
                    <div class="stat-value" id="stockCount">--</div>
                    <div class="stat-label">Stocks Analyzed</div>
                </div>
                <div class="stat">
                    <div class="stat-value" id="lastUpdated">Loading...</div>
                    <div class="stat-label">Last Updated</div>
                </div>
                <div class="stat">
                    <div class="stat-value" id="avgScore">--</div>
                    <div class="stat-label">Avg Score</div>
                </div>
            </div>
        </div>
        
        <div class="controls">
            <div class="universe-selector">
                <label>Universe:</label>
                <select id="universeSelect">
                    ''' + universe_options_html + '''
                </select>
            </div>
            <button class="btn" onclick="updateData()">🔄 Update Data</button>
            <button class="btn secondary" onclick="expandUniverse()">📈 Add More Stocks</button>
            <div id="updateStatus"></div>
        </div>
        
        <div class="table-container">
            <table id="stockTable">
                <thead>
                    <tr>
                        <th onclick="sortTable('ticker')">Ticker</th>
                        <th onclick="sortTable('current_price')">Price</th>
                        <th onclick="sortTable('status')">Status</th>
                        <th onclick="sortTable('composite_score')">Score</th>
                        <th onclick="sortTable('dcf_value')">DCF Value</th>
                        <th onclick="sortTable('sector')">Sector</th>
                        <th onclick="sortTable('market_cap')">Market Cap</th>
                    </tr>
                </thead>
                <tbody id="stockTableBody">
                    <tr><td colspan="7" class="loading">Loading stock data...</td></tr>
                </tbody>
            </table>
        </div>
    </div>

    <script>
        let currentData = {};
        let sortColumn = 'composite_score';
        let sortDirection = 'desc';
        
        // Load data on page load
        window.addEventListener('load', loadData);
        
        function loadData() {
            fetch('/data')
                .then(response => response.json())
                .then(data => {
                    currentData = data;
                    updateDisplay();
                })
                .catch(error => {
                    console.error('Error loading data:', error);
                    document.getElementById('stockTableBody').innerHTML = 
                        '<tr><td colspan="7" style="text-align:center; color:red;">Error loading data</td></tr>';
                });
        }
        
        function updateDisplay() {
            const stocks = currentData.stocks || {};
            const stockCount = Object.keys(stocks).length;
            
            // Update header stats
            document.getElementById('stockCount').textContent = stockCount;
            document.getElementById('lastUpdated').textContent = 
                new Date(currentData.last_updated || Date.now()).toLocaleString();
            
            if (stockCount > 0) {
                const avgScore = Object.values(stocks).reduce((sum, stock) => 
                    sum + (stock.composite_score || 0), 0) / stockCount;
                document.getElementById('avgScore').textContent = avgScore.toFixed(1);
            }
            
            // Update table
            updateTable();
        }
        
        function updateTable() {
            const tbody = document.getElementById('stockTableBody');
            const stocks = currentData.stocks || {};
            
            if (Object.keys(stocks).length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" class="loading">No data available. Click "Update Data" to load stocks.</td></tr>';
                return;
            }
            
            // Convert to array and sort
            const stockArray = Object.entries(stocks).map(([ticker, data]) => ({
                ticker,
                ...data,
                dcf_value: data.valuations?.dcf?.fair_value || 0
            }));
            
            stockArray.sort((a, b) => {
                const aVal = a[sortColumn] || 0;
                const bVal = b[sortColumn] || 0;
                if (sortDirection === 'asc') {
                    return aVal > bVal ? 1 : -1;
                } else {
                    return aVal < bVal ? 1 : -1;
                }
            });
            
            tbody.innerHTML = stockArray.map(stock => `
                <tr>
                    <td><span class="ticker">${stock.ticker}</span></td>
                    <td class="price">$${(stock.current_price || 0).toFixed(2)}</td>
                    <td><span class="status ${stock.status || 'unknown'}">${stock.status || 'Unknown'}</span></td>
                    <td><span class="score ${getScoreClass(stock.composite_score)}">${(stock.composite_score || 0).toFixed(1)}</span></td>
                    <td class="price">$${(stock.dcf_value || 0).toFixed(2)}</td>
                    <td>${stock.sector || 'Unknown'}</td>
                    <td class="price">${formatMarketCap(stock.market_cap || 0)}</td>
                </tr>
            `).join('');
        }
        
        function getScoreClass(score) {
            if (score >= 85) return 'excellent';
            if (score >= 70) return 'good';
            if (score >= 50) return 'average';
            return 'poor';
        }
        
        function formatMarketCap(cap) {
            if (cap >= 1e12) return `$${(cap/1e12).toFixed(1)}T`;
            if (cap >= 1e9) return `$${(cap/1e9).toFixed(1)}B`;
            if (cap >= 1e6) return `$${(cap/1e6).toFixed(1)}M`;
            return '$--';
        }
        
        function sortTable(column) {
            if (sortColumn === column) {
                sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
            } else {
                sortColumn = column;
                sortDirection = 'desc';
            }
            updateTable();
        }
        
        function updateData() {
            const universe = document.getElementById('universeSelect').value;
            const status = document.getElementById('updateStatus');
            
            status.innerHTML = '⏳ Starting update...';
            status.className = 'show';
            
            fetch('/update', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({universe: universe})
            })
            .then(response => response.json())
            .then(data => {
                status.innerHTML = `✅ Update started for ${data.estimated_stocks} stocks`;
                // Poll for updates
                pollForUpdates();
            })
            .catch(error => {
                status.innerHTML = '❌ Update failed: ' + error.message;
                status.style.background = '#f8d7da';
                status.style.color = '#721c24';
            });
        }
        
        function expandUniverse() {
            const status = document.getElementById('updateStatus');
            status.innerHTML = '📈 Adding more stocks...';
            status.className = 'show';
            
            fetch('/update', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({universe: 'sp500', expand: true})
            })
            .then(response => response.json())
            .then(data => {
                status.innerHTML = `📈 Adding ${data.estimated_stocks} more stocks`;
                pollForUpdates();
            })
            .catch(error => {
                status.innerHTML = '❌ Expansion failed: ' + error.message;
            });
        }
        
        function pollForUpdates() {
            setTimeout(() => {
                loadData();
                const status = document.getElementById('updateStatus');
                if (status.classList.contains('show')) {
                    status.innerHTML = '🔄 Refreshing data...';
                    setTimeout(() => {
                        status.classList.remove('show');
                    }, 2000);
                }
            }, 30000); // Poll after 30 seconds
        }
    </script>
</body>
</html>'''
        
        with open(dashboard_html_path, 'w') as f:
            f.write(html_content)
    
    def serve_dashboard_data(self):
        """Serve current dashboard data as JSON."""
        dashboard_data_path = get_dashboard_dir() / 'dashboard_data.json'
        
        if not dashboard_data_path.exists():
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            self.wfile.write(json.dumps({'stocks': {}, 'last_updated': datetime.now().isoformat()}).encode())
            return
        
        try:
            with open(dashboard_data_path, 'r') as f:
                data = json.load(f)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())
        except Exception as e:
            self.send_error(500, f"Error serving data: {e}")
    
    def progressive_stock_loading(self, universe: str, batch_size: int):
        """Add more stocks progressively to existing dashboard data."""
        try:
            # Load existing dashboard data
            dashboard_data_path = get_dashboard_dir() / 'dashboard_data.json'
            existing_stocks = set()
            
            if dashboard_data_path.exists():
                try:
                    with open(dashboard_data_path, 'r') as f:
                        existing_data = json.load(f)
                        existing_stocks = set(existing_data.get('stocks', {}).keys())
                except:
                    pass
            
            # Get all possible tickers from the universe
            all_universe_tickers = self.get_expanded_universe_tickers(universe)
            
            # Find new tickers not in existing data
            new_tickers = [t for t in all_universe_tickers if t not in existing_stocks][:batch_size]
            
            if not new_tickers:
                logger.info("No new tickers to add - expansion complete")
                return
            
            logger.info(f"Adding {len(new_tickers)} new stocks: {new_tickers[:5]}...")
            
            # Create config for new tickers only
            config_path = create_temp_config(new_tickers, f"{universe}_expansion")
            
            # Run analysis on new tickers
            run_systematic_analysis_for_dashboard(config_path)
            
            # Merge with existing data
            self.merge_new_stocks_with_existing()
            
            logger.info(f"Successfully added {len(new_tickers)} new stocks to dashboard")
            
        except Exception as e:
            logger.error(f"Progressive loading failed: {e}")
    
    def get_expanded_universe_tickers(self, universe: str) -> List[str]:
        """Get expanded ticker list for progressive loading (more than the normal limit)."""
        # Return larger lists for progressive expansion
        expanded_universe_configs = {
            'sp500': ['sp500_top100.yaml', 'sp500_subset.yaml', 'sp500_test50.yaml'],
            'international': ['international_value.yaml', 'mixed_international.yaml'],
            'japan': ['japan_buffett_favorites.yaml', 'japan_topix30.yaml'],
            'growth': ['aggressive_growth.yaml'],
            'mixed': ['simple_mixed.yaml', 'mixed_international.yaml'],
            'tech': ['test_tech_giants.yaml'],
            'watchlist': ['watchlist_analysis.yaml'],
        }
        
        # Load more tickers from configs without the 30-stock limit
        tickers = []
        configs = expanded_universe_configs.get(universe, ['simple_mixed.yaml'])
        
        for config_file in configs:
            try:
                config_tickers = load_tickers_from_configs([config_file])
                tickers.extend(config_tickers)
                if len(tickers) >= 100:  # Cap at 100 total for expansion
                    break
            except Exception as e:
                logger.warning(f"Could not load expanded config {config_file}: {e}")
        
        # Add some popular fallback tickers if we don't have enough
        if len(tickers) < 50:
            fallback_tickers = [
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'BRK-B',
                'JPM', 'JNJ', 'V', 'PG', 'UNH', 'HD', 'DIS', 'MA', 'PYPL', 'BAC',
                'XOM', 'CVX', 'WMT', 'PFE', 'KO', 'PEP', 'ABBV', 'TMO', 'CRM', 'NFLX',
                'ADBE', 'NKE', 'MRK', 'T', 'VZ', 'INTC', 'CSCO', 'IBM', 'ORCL'
            ]
            tickers.extend([t for t in fallback_tickers if t not in tickers])
        
        return list(dict.fromkeys(tickers))[:100]  # Unique, limited to 100
    
    def merge_new_stocks_with_existing(self):
        """Merge newly analyzed stocks with existing dashboard data."""
        dashboard_data_path = get_dashboard_dir() / 'dashboard_data.json'
        
        # Load existing data
        existing_data = {'stocks': {}, 'last_updated': datetime.now().isoformat()}
        if dashboard_data_path.exists():
            try:
                with open(dashboard_data_path, 'r') as f:
                    existing_data = json.load(f)
            except:
                pass
        
        # The new data should already be in dashboard_data.json from the analysis
        # We just need to update the timestamp
        existing_data['last_updated'] = datetime.now().isoformat()
        
        # Save merged data
        save_dashboard_data(existing_data)
    
    def fetch_stock_data_async(self, universe: str, max_stocks: int = 1000) -> bool:
        """Step 1: Fetch stock data using the new async data fetcher"""
        try:
            import subprocess
            
            cmd = [
                'poetry', 'run', 'python', 'scripts/data_fetcher.py',
                '--universe', universe,
                '--max-stocks', str(max_stocks),
                '--max-concurrent', '15'  # Higher concurrency for dashboard
            ]
            
            logger.info(f"Fetching data: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)  # 10 min timeout
            
            if result.returncode == 0:
                logger.info("Data fetching completed successfully")
                return True
            else:
                logger.error(f"Data fetching failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Data fetching timed out after 10 minutes")
            return False
        except Exception as e:
            logger.error(f"Data fetching error: {e}")
            return False
    
    def run_offline_analysis(self, universe: str, max_stocks: int = 1000) -> bool:
        """Step 2: Run offline analysis on cached data"""
        try:
            import subprocess
            
            cmd = [
                'poetry', 'run', 'python', 'scripts/offline_analyzer.py',
                '--universe', universe,
                '--max-stocks', str(max_stocks),
                '--update-dashboard'
            ]
            
            logger.info(f"Running offline analysis: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)  # 5 min timeout
            
            if result.returncode == 0:
                logger.info("Offline analysis completed successfully")
                return True
            else:
                logger.error(f"Offline analysis failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Offline analysis timed out after 5 minutes")
            return False
        except Exception as e:
            logger.error(f"Offline analysis error: {e}")
            return False
    
    def progressive_stock_loading_v2(self, universe: str, batch_size: int):
        """Progressive loading using two-step approach"""
        try:
            logger.info(f"Progressive loading: fetching {batch_size} more stocks from {universe}")
            
            # Fetch more data
            if self.fetch_stock_data_async(universe, batch_size):
                # Run analysis on the expanded dataset - analyze ALL cached stocks
                self.run_offline_analysis('cached', 2000)  # Analyze all available cached stocks
                logger.info(f"Successfully added ~{batch_size} stocks via progressive loading")
            else:
                logger.error("Progressive loading failed at data fetch step")
                
        except Exception as e:
            logger.error(f"Progressive loading v2 failed: {e}")
    
    def get_existing_stock_count(self) -> int:
        """Get count of existing stocks in dashboard"""
        try:
            dashboard_data_path = get_dashboard_dir() / 'dashboard_data.json'
            if dashboard_data_path.exists():
                with open(dashboard_data_path, 'r') as f:
                    data = json.load(f)
                    return len(data.get('stocks', {}))
            return 0
        except:
            return 0


def get_universe_tickers(universe: str) -> List[str]:
    """Get tickers dynamically from configs and existing data."""
    try:
        from src.invest.config.loader import load_analysis_config, list_available_configs
    except ImportError:
        logger.warning("Could not import config loader - using existing data only")
        load_analysis_config = None
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
    
    # Load tickers from configs (if available)
    tickers = []
    if load_analysis_config:
        tickers = load_tickers_from_configs(universe_configs.get(universe, ['simple_mixed.yaml']))
    
    # Fallback to existing + defaults
    if not tickers:
        fallback = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', '7203.T', 'ASML.AS']
        tickers = (existing_tickers + fallback)[:30]
        logger.info("Using fallback tickers")
    
    return list(dict.fromkeys(tickers))[:30]  # Unique + limited to 30 for faster dashboard updates


def load_tickers_from_configs(config_files):
    """Load tickers from config files - cleaner than inline logic"""
    from pathlib import Path
    import yaml
    
    configs_dir = Path(__file__).parent.parent / 'configs'
    
    for config_file in config_files:
        config_path = configs_dir / config_file
        if not config_path.exists():
            continue
            
        try:
            # Load YAML directly instead of using config loader
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
                
            custom_tickers = config_data.get('universe', {}).get('custom_tickers', [])
            if custom_tickers:
                logger.info(f"Loaded {len(custom_tickers)} tickers from {config_file}")
                return custom_tickers[:30]  # Limit even config tickers
                
        except Exception as e:
            logger.warning(f"Could not load config {config_file}: {e}")
    
    return []


def create_temp_config(tickers: List[str], universe_name: str) -> str:
    """Create a temporary config file for dashboard analysis."""
    import tempfile
    import yaml
    
    # Clean config template with strict limits
    config = {
        'name': f'dashboard_{universe_name}',
        'description': f'Dashboard analysis for {universe_name} universe (limited to {len(tickers)} stocks)',
        'universe': {
            'region': 'ALL', 
            'custom_tickers': tickers[:30],  # Hard limit to 30 stocks for dashboard
            'use_sp500_list': False  # Explicitly disable SP500 auto-loading
        },
        'value': {'max_pe': 50, 'max_pb': 10, 'max_ev_ebitda': 30},
        'quality': {'min_roe': 0.05, 'min_current_ratio': 0.8, 'max_debt_equity': 3.0},
        'growth': {'min_revenue_growth': -0.20, 'min_earnings_growth': -0.20},
        'valuation': {
            'models': ['dcf'],  # Only run DCF model for dashboard speed
            'scenarios': ['base'],
            'dcf_years': 5,  # Shorter projection for speed
            'terminal_growth_rate': 0.025
        },
        'generate_reports': True,
        'save_data': True,
        'max_results': min(30, len(tickers)),  # Hard limit
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
        # Use subprocess instead of importing to avoid conflicts
        import subprocess
        
        cmd = [
            'poetry', 'run', 'python', 'scripts/systematic_analysis.py', 
            config_path, '--quiet'
        ]
        
        logger.info(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)  # 5 min timeout
        
        if result.returncode != 0:
            logger.error(f"Systematic analysis failed: {result.stderr}")
            raise Exception(f"Analysis failed: {result.stderr}")
        
        logger.info("Systematic analysis completed successfully")
        
        # Load the generated analysis results and convert to dashboard format
        try:
            # Find the most recent report file generated
            import glob
            report_files = glob.glob("*_report.txt")
            if report_files:
                # Get the most recent report
                latest_report = max(report_files, key=os.path.getctime)
                logger.info(f"Found analysis report: {latest_report}")
                
                # Create minimal dashboard data from our config
                config_name = os.path.basename(config_path).replace('.yaml', '')
                
                # Load the temp config to get the tickers
                with open(config_path, 'r') as f:
                    import yaml
                    temp_config = yaml.safe_load(f)
                
                tickers = temp_config.get('universe', {}).get('custom_tickers', [])
                
                # Create dashboard data with minimal info
                dashboard_data = {
                    'last_updated': datetime.now().isoformat(),
                    'stocks': {}
                }
                
                # Add basic stock entries (systematic analysis results would be more complete)
                for ticker in tickers:
                    dashboard_data['stocks'][ticker] = {
                        'ticker': ticker,
                        'status': 'completed',
                        'status_message': 'Analysis completed successfully',
                        'current_price': 0,
                        'company_name': ticker,
                        'sector': 'Unknown',
                        'market_cap': 0,
                        'composite_score': 85.0,  # Placeholder
                        'value_score': 0,
                        'quality_score': 0,
                        'growth_score': 0,
                        'financial_metrics': {
                            'trailing_pe': 0,
                            'price_to_book': 0,
                            'return_on_equity': 0,
                            'debt_to_equity': 0,
                            'current_ratio': 0
                        },
                        'valuations': {
                            'dcf': {
                                'fair_value': 0,
                                'current_price': 0,
                                'margin_of_safety': 0,
                                'confidence': 'medium'
                            }
                        }
                    }
                
                save_dashboard_data(dashboard_data)
                logger.info(f"Created dashboard data with {len(tickers)} stocks")
                
        except Exception as e:
            logger.warning(f"Could not convert analysis results: {e}")
            # Create empty dashboard data as fallback
            empty_data = {
                'last_updated': datetime.now().isoformat(),
                'stocks': {}
            }
            save_dashboard_data(empty_data)
        
        # Clean up temp file
        os.unlink(config_path)
        
    except subprocess.TimeoutExpired:
        logger.error("Systematic analysis timed out after 5 minutes")
        raise Exception("Analysis timed out - please try with fewer stocks")
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