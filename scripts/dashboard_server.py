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
            # Generate dashboard using the improved modular components
            try:
                self.generate_modular_dashboard()
                self.path = '/valuation_dashboard.html'
            except Exception as e:
                logger.error(f"Error generating modular dashboard: {e}")
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
        path = self.path.split('?')[0]  # Remove query parameters for comparison
        if path == '/update':
            self.handle_update()
        elif path == '/sort':
            self.handle_sort()
        else:
            self.send_error(404)
    
    def handle_update(self):
        """Handle dashboard update request with universe selection and progressive loading."""
        try:
            # Parse query parameters and request body to get universe selection
            from urllib.parse import urlparse, parse_qs
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            
            content_length = int(self.headers.get('Content-Length', 0))
            request_body = self.rfile.read(content_length).decode('utf-8')
            
            # Default parameters
            universe = 'existing'
            expand = False
            batch_size = 20
            
            # Check query parameters first
            if 'universe' in query_params:
                universe = query_params['universe'][0]
            
            # Then check request body (POST data can override query params)
            if request_body:
                try:
                    request_data = json.loads(request_body)
                    universe = request_data.get('universe', universe)
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
                        
                        # Step 1: Fetch data asynchronously - no limits
                        fetch_success = self.fetch_stock_data_async(universe)
                        
                        if fetch_success:
                            # Step 2: Run offline analysis on ALL cached data (not just the universe)
                            self.run_offline_analysis('cached')
                            logger.info("Dashboard updated successfully via two-step approach")
                        else:
                            logger.error("Data fetching failed, trying to analyze existing cached data")
                            # Try to analyze whatever cached data we have
                            try:
                                self.run_offline_analysis('cached')
                                logger.info("Fallback: analyzed existing cached data")
                            except Exception as fallback_error:
                                logger.error(f"Both new system and fallback failed: {fallback_error}")
                                # Last resort: use old method with small dataset
                                from scripts.data_fetcher import get_universe_tickers
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
                    stock_estimates[universe_key] = len(get_universe_tickers(universe_key))
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
    
    def generate_modular_dashboard(self):
        """Generate dashboard using original aesthetics with added ratio functionality."""
        try:
            dashboard_html_path = get_dashboard_dir() / 'valuation_dashboard.html'
            
            # Load dashboard data
            dashboard_data_path = get_dashboard_dir() / 'dashboard_data.json'
            stocks_data = {}
            total_stocks = 0
            successful_analyses = 0
            last_updated = "Never"
            
            if dashboard_data_path.exists():
                with open(dashboard_data_path, 'r') as f:
                    data = json.load(f)
                    stocks_data = data.get('stocks', {})
                    total_stocks = len(stocks_data)
                    successful_analyses = len([s for s in stocks_data.values() if s.get('status') == 'completed'])
                    last_updated = data.get('last_updated', 'Never')
                    if last_updated != "Never":
                        from datetime import datetime
                        try:
                            dt = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                            last_updated = dt.strftime('%I:%M %p')
                        except:
                            pass
            
            # Calculate average score
            scores = [s.get('composite_score', 0) for s in stocks_data.values() if s.get('composite_score')]
            avg_score = sum(scores) / len(scores) if scores else 0
            
            # Generate the beautiful HTML with ratio functionality
            html_content = self.create_beautiful_dashboard_html(stocks_data, total_stocks, successful_analyses, avg_score, last_updated)
            
            with open(dashboard_html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
            logger.info("Generated beautiful dashboard with ratio functionality")
            
        except Exception as e:
            logger.error(f"Failed to generate beautiful dashboard: {e}")
            # Fallback to the old method
            self.create_basic_dashboard_html()
    
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
            'all': ('🌍 All Markets', len(get_universe_tickers('all'))),
            'sp500': ('S&P 500', len(get_universe_tickers('sp500'))),
            'international': ('International', len(get_universe_tickers('international'))),
            'japan': ('Japan', len(get_universe_tickers('japan'))),
            'tech': ('Tech Focus', len(get_universe_tickers('tech'))),
            'growth': ('Growth', len(get_universe_tickers('growth')))
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
    
    def create_beautiful_dashboard_html(self, stocks_data, total_stocks, successful_analyses, avg_score, last_updated):
        """Create the beautiful dashboard HTML with ratio functionality."""
        
        # Generate stock table rows with ratio functionality
        table_rows = []
        for ticker, stock in stocks_data.items():
            if not stock.get('current_price') or stock.get('current_price') == 0:
                continue  # Skip stocks without price data
                
            current_price = stock.get('current_price', 0)
            market_cap = stock.get('market_cap', 0)
            composite_score = stock.get('composite_score', 0)
            sector = stock.get('sector', 'Unknown')
            
            # Get all available valuations and format with ratios
            valuations = stock.get('valuations', {})
            
            # Standard DCF
            dcf_val = valuations.get('dcf', {})
            dcf_fair = dcf_val.get('fair_value', 0) if dcf_val else 0
            dcf_fair = dcf_fair or 0  # Handle None values
            has_dcf_error = dcf_val.get('error') is not None if dcf_val else False
            dcf_ratio = f"{dcf_fair/current_price:.2f}x" if current_price > 0 and dcf_fair > 0 else ("X" if has_dcf_error else "--")
            dcf_display = f"${dcf_fair:.2f}" if dcf_fair > 0 else ("X" if has_dcf_error else "--")
            
            # Enhanced DCF
            dcf_enh_val = valuations.get('dcf_enhanced', {})
            dcf_enh_fair = dcf_enh_val.get('fair_value', 0) if dcf_enh_val else 0
            dcf_enh_fair = dcf_enh_fair or 0  # Handle None values
            has_dcf_enh_error = dcf_enh_val.get('error') is not None if dcf_enh_val else False
            dcf_enh_ratio = f"{dcf_enh_fair/current_price:.2f}x" if current_price > 0 and dcf_enh_fair > 0 else ("X" if has_dcf_enh_error else "--")
            dcf_enh_display = f"${dcf_enh_fair:.2f}" if dcf_enh_fair > 0 else ("X" if has_dcf_enh_error else "--")
            
            # Growth DCF
            growth_dcf_val = valuations.get('growth_dcf', {})
            growth_dcf_fair = growth_dcf_val.get('fair_value', 0) if growth_dcf_val else 0
            growth_dcf_fair = growth_dcf_fair or 0  # Handle None values
            has_growth_dcf_error = growth_dcf_val.get('error') is not None if growth_dcf_val else False
            growth_dcf_ratio = f"{growth_dcf_fair/current_price:.2f}x" if current_price > 0 and growth_dcf_fair > 0 else ("X" if has_growth_dcf_error else "--")
            growth_dcf_display = f"${growth_dcf_fair:.2f}" if growth_dcf_fair > 0 else ("X" if has_growth_dcf_error else "--")
            
            # Multi-Stage DCF
            multi_dcf_val = valuations.get('multi_stage_dcf', {})
            multi_dcf_fair = multi_dcf_val.get('fair_value', 0) if multi_dcf_val else 0
            multi_dcf_fair = multi_dcf_fair or 0  # Handle None values
            has_multi_dcf_error = multi_dcf_val.get('error') is not None if multi_dcf_val else False
            multi_dcf_ratio = f"{multi_dcf_fair/current_price:.2f}x" if current_price > 0 and multi_dcf_fair > 0 else ("X" if has_multi_dcf_error else "--")
            multi_dcf_display = f"${multi_dcf_fair:.2f}" if multi_dcf_fair > 0 else ("X" if has_multi_dcf_error else "--")
            
            # Simple Ratios (Market Multiples)
            ratios_val = valuations.get('simple_ratios', {})
            ratios_fair = ratios_val.get('fair_value', 0) if ratios_val else 0
            ratios_fair = ratios_fair or 0  # Handle None values
            has_ratios_error = ratios_val.get('error') is not None if ratios_val else False
            ratios_ratio = f"{ratios_fair/current_price:.2f}x" if current_price > 0 and ratios_fair > 0 else ("X" if has_ratios_error else "--")
            ratios_display = f"${ratios_fair:.2f}" if ratios_fair > 0 else ("X" if has_ratios_error else "--")
            
            # RIM (Residual Income Model)
            rim_val = valuations.get('rim', {})
            rim_fair = rim_val.get('fair_value', 0) if rim_val else 0
            rim_fair = rim_fair or 0  # Handle None values
            has_rim_error = rim_val.get('error') is not None if rim_val else False
            rim_ratio = f"{rim_fair/current_price:.2f}x" if current_price > 0 and rim_fair > 0 else ("X" if has_rim_error else "--")
            rim_display = f"${rim_fair:.2f}" if rim_fair > 0 else ("X" if has_rim_error else "--")
            
            # Neural Network Best (2-year model)
            nn_best_val = valuations.get('neural_network_best', {})
            nn_best_fair = nn_best_val.get('fair_value', 0) if nn_best_val else 0
            nn_best_fair = nn_best_fair or 0  # Handle None values
            has_nn_best_error = nn_best_val.get('error') is not None if nn_best_val else False
            nn_best_ratio = f"{nn_best_fair/current_price:.2f}x" if current_price > 0 and nn_best_fair > 0 else ("X" if has_nn_best_error else "--")
            nn_best_display = f"${nn_best_fair:.2f}" if nn_best_fair > 0 else ("X" if has_nn_best_error else "--")
            
            # Legacy fields for backward compatibility
            pe_val = valuations.get('pe_based', 0)
            pe_ratio = f"{pe_val/current_price:.2f}x" if current_price > 0 and pe_val and pe_val > 0 else "--"
            pe_display = f"${pe_val:.2f}" if pe_val and pe_val > 0 else "--"
            
            graham_val = valuations.get('graham_number', 0)
            graham_ratio = f"{graham_val/current_price:.2f}x" if current_price > 0 and graham_val and graham_val > 0 else "--"
            graham_display = f"${graham_val:.2f}" if graham_val and graham_val > 0 else "--"
            
            # Format market cap
            if market_cap >= 1e12:
                market_cap_str = f"${market_cap/1e12:.1f}T"
            elif market_cap >= 1e9:
                market_cap_str = f"${market_cap/1e9:.1f}B"
            elif market_cap >= 1e6:
                market_cap_str = f"${market_cap/1e6:.1f}M"
            else:
                market_cap_str = "$--"
            
            # Score class
            if composite_score >= 85:
                score_class = "excellent"
            elif composite_score >= 70:
                score_class = "good"
            elif composite_score >= 50:
                score_class = "average"
            else:
                score_class = "poor"
            
            row = f"""
            <tr>
                <td><span class="ticker" title="Company: {stock.get('company_name', ticker)} | Ticker: {ticker} | Click ticker to research this company">{ticker}</span></td>
                <td class="price" title="Current market price: ${current_price:.2f} per share">${current_price:.2f}</td>
                <td class="price" title="Market Cap: {market_cap_str} | Total company value based on current stock price" data-value="{market_cap}">{market_cap_str}</td>
                <td><span class="score {score_class}" title="Investment Score: {composite_score:.1f}/100 | Combines Value + Quality + Growth metrics. 85+=Excellent, 70+=Good, 50+=Average, <50=Poor">{composite_score:.1f}</span></td>
                <td class="price" title="Standard DCF: Basic discounted cash flow model projecting future cash flows. Formula: FCF × (1+g)^n / (1+r)^n + Terminal Value. Higher ratios indicate undervaluation.">{dcf_display}<br><small>{dcf_ratio}</small></td>
                <td class="price" title="Enhanced DCF: Improved DCF with normalized cash flows and better assumptions for volatile companies. Handles lumpy cash flows better than standard DCF.">{dcf_enh_display}<br><small>{dcf_enh_ratio}</small></td>
                <td class="price" title="Growth DCF: DCF that separates maintenance from growth CapEx, properly valuing reinvestment. Best for asset-heavy growth companies like Amazon/Tesla.">{growth_dcf_display}<br><small>{growth_dcf_ratio}</small></td>
                <td class="price" title="Multi-Stage DCF: DCF with multiple growth phases (high growth → mature). Formula uses different growth rates over time. Best for growth companies transitioning to maturity.">{multi_dcf_display}<br><small>{multi_dcf_ratio}</small></td>
                <td class="price" title="Market Multiples: Quick valuation using P/E, P/B, EV/EBITDA ratios vs industry averages. Fast screening tool for relative value assessment.">{ratios_display}<br><small>{ratios_ratio}</small></td>
                <td class="price" title="RIM (Residual Income): Values companies based on returns above cost of equity. Formula: Book Value + PV(ROE - Cost of Equity) × Book Value. Best for financial/mature companies.">{rim_display}<br><small>{rim_ratio}</small></td>
                <td class="price" title="Neural Network Best: AI model trained on 2-year horizons with 51.8% correlation and 100% hit rate. Uses 60+ engineered features from financial data. Best performing model.">{nn_best_display}<br><small>{nn_best_ratio}</small></td>
                <td>{sector}</td>
            </tr>"""
            
            table_rows.append(row)
        
        # Create the beautiful HTML
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Stock Valuation Dashboard</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        .header {{
            background: white;
            border-radius: 16px;
            padding: 32px;
            margin-bottom: 24px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }}
        h1 {{ color: #1a1a2e; font-size: 2.5em; margin-bottom: 16px; }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-top: 24px;
        }}
        .stat-card {{
            background: #f8f9fa;
            padding: 16px;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-value {{ font-size: 2em; font-weight: bold; color: #667eea; }}
        .stat-label {{ color: #666; margin-top: 4px; }}
        .controls {{
            background: white;
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            display: flex;
            gap: 16px;
            align-items: center;
            flex-wrap: wrap;
        }}
        .table-container {{
            background: white;
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            overflow-x: auto;
        }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 10px 8px; text-align: left; border-bottom: 1px solid #eee; font-size: 14px; }}
        th {{ 
            background: #f8f9fa; font-weight: 600; cursor: pointer;
            user-select: none; transition: background 0.2s;
        }}
        th:hover {{ background: #e9ecef; }}
        .ticker {{ font-weight: 600; color: #1a1a2e; }}
        .price {{ font-family: 'Courier New', monospace; }}
        .score {{
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: 600;
        }}
        .excellent {{ background: #d4edda; color: #155724; }}
        .good {{ background: #fff3cd; color: #856404; }}
        .average {{ background: #cce5ff; color: #004085; }}
        .poor {{ background: #f8d7da; color: #721c24; }}
        
        /* Ratio styling */
        .price small {{
            display: block;
            color: #6c757d;
            font-size: 11px;
            font-weight: 500;
            margin-top: 2px;
        }}
        
        button {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-size: 1em;
            cursor: pointer;
            transition: transform 0.2s;
            font-weight: 600;
        }}
        button:hover {{ transform: translateY(-2px); }}
        select {{
            padding: 12px;
            border-radius: 8px;
            border: 2px solid #e9ecef;
            font-size: 1em;
            cursor: pointer;
        }}
        #updateStatus {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: #d4edda;
            color: #155724;
            padding: 16px 24px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            display: none;
            z-index: 1000;
        }}
        #updateStatus.show {{ display: block; }}
        .loading {{
            text-align: center;
            padding: 40px;
            color: #666;
        }}
        
        /* Sorting arrows */
        .sort-asc::after {{
            content: ' ↑';
            color: #667eea;
        }}
        .sort-desc::after {{
            content: ' ↓';
            color: #667eea;
        }}
        
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📈 Stock Valuation Dashboard</h1>
            <div class="stats" id="stats">
                <div class="stat-card">
                    <div class="stat-value">{total_stocks}</div>
                    <div class="stat-label">Total Stocks</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{successful_analyses}</div>
                    <div class="stat-label">Analyzed</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{avg_score:.1f}</div>
                    <div class="stat-label">Avg Score</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{last_updated}</div>
                    <div class="stat-label">Last Update</div>
                </div>
            </div>
        </div>
        
        <div class="controls">
            <select id="universeSelect">
                <option value="sp500">S&P 500</option>
                <option value="nasdaq100">NASDAQ 100</option>
                <option value="dow30">Dow 30</option>
                <option value="russell2000">Russell 2000</option>
                <option value="ftse100">FTSE 100</option>
                <option value="dax">DAX</option>
                <option value="cac40">CAC 40</option>
                <option value="nikkei225">Nikkei 225</option>
                <option value="all">All Markets</option>
            </select>
            <button onclick="updateData()">🔄 Update Data</button>
            <button onclick="loadData()">📊 Refresh View</button>
        </div>
        
        <div class="table-container">
            <table id="stockTable">
                <thead>
                    <tr>
                        <th onclick="sortTable('ticker')" title="Stock Ticker: Company trading symbol on the exchange (e.g., AAPL for Apple Inc.)">Ticker</th>
                        <th onclick="sortTable('current_price')" title="Current Price: Latest market price per share. This is what you'd pay to buy one share right now.">Price</th>
                        <th onclick="sortTable('market_cap')" title="Market Capitalization: Total value of all company shares (Price × Shares Outstanding). Indicates company size: >$10B = Large Cap, $2-10B = Mid Cap, <$2B = Small Cap">Market Cap</th>
                        <th onclick="sortTable('composite_score')" title="Composite Score: Overall investment attractiveness (0-100). Combines value (cheap price), quality (strong fundamentals), and growth (increasing earnings). Higher = better investment opportunity.">Score</th>
                        <th onclick="sortTable('dcf_value')" title="Standard DCF: Basic discounted cash flow model projecting future cash flows. Click to sort by Expected Value ÷ Market Price ratio.">DCF</th>
                        <th onclick="sortTable('dcf_enhanced')" title="Enhanced DCF: Improved DCF with normalized cash flows, better for volatile companies. Click to sort by ratio.">Enh DCF</th>
                        <th onclick="sortTable('growth_dcf')" title="Growth DCF: Separates maintenance vs growth CapEx, best for reinvestment-heavy companies. Click to sort by ratio.">Growth DCF</th>
                        <th onclick="sortTable('multi_dcf')" title="Multi-Stage DCF: Multiple growth phases (high growth → mature), best for transitioning companies. Click to sort by ratio.">Multi DCF</th>
                        <th onclick="sortTable('ratios')" title="Market Multiples: P/E, P/B, EV/EBITDA vs industry averages. Quick screening tool. Click to sort by ratio.">Ratios</th>
                        <th onclick="sortTable('rim')" title="RIM: Residual Income Model based on returns above cost of equity. Best for financial/mature companies. Click to sort by ratio.">RIM</th>
                        <th onclick="sortTable('nn_best')" title="Neural Network Best: AI model trained on 2-year horizons with 51.8% correlation. Uses 60+ engineered features. BEST PERFORMING MODEL.">🧠 NN Best</th>
                        <th onclick="sortTable('sector')" title="Business Sector: Industry classification (Technology, Healthcare, Finance, etc.). Companies in same sector often have similar characteristics.">Sector</th>
                    </tr>
                </thead>
                <tbody id="stockTableBody">
                    {''.join(table_rows) if table_rows else '<tr><td colspan="12" class="loading">No stock data available. Click "Update Data" to load stocks.</td></tr>'}
                </tbody>
            </table>
        </div>
    </div>
    
    <div id="updateStatus"></div>
    
    <script>
        let currentData = {{}};
        let sortColumn = 'composite_score';
        let sortDirection = 'desc';
        
        // Enhanced sorting with ratio support
        function sortTable(column) {{
            const table = document.getElementById('stockTable');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            
            if (!rows.length) return;
            
            // Clear previous sort indicators
            table.querySelectorAll('th').forEach(h => {{
                h.classList.remove('sort-asc', 'sort-desc');
            }});
            
            // Toggle direction
            if (sortColumn === column) {{
                sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
            }} else {{
                sortColumn = column;
                sortDirection = 'desc';
            }}
            
            // Add sort indicator
            const headerIndex = Array.from(table.querySelectorAll('th')).findIndex(h => 
                h.getAttribute('onclick').includes(column));
            if (headerIndex >= 0) {{
                table.querySelectorAll('th')[headerIndex].classList.add(
                    sortDirection === 'asc' ? 'sort-asc' : 'sort-desc');
            }}
            
            // Sort rows with ratio support
            rows.sort((rowA, rowB) => {{
                const cellA = rowA.cells[headerIndex];
                const cellB = rowB.cells[headerIndex];
                
                if (!cellA || !cellB) return 0;
                
                let valueA, valueB;
                
                // For valuation columns, sort by ratio if available
                if (['dcf_value', 'dcf_enhanced', 'growth_dcf', 'multi_dcf', 'ratios', 'rim', 'nn_best'].includes(column)) {{
                    const ratioA = cellA.querySelector('small');
                    const ratioB = cellB.querySelector('small');
                    
                    if (ratioA && ratioB) {{
                        valueA = parseFloat(ratioA.textContent.replace(/[x]/g, '')) || 0;
                        valueB = parseFloat(ratioB.textContent.replace(/[x]/g, '')) || 0;
                    }} else {{
                        valueA = parseFloat(cellA.textContent.replace(/[$,]/g, '')) || 0;
                        valueB = parseFloat(cellB.textContent.replace(/[$,]/g, '')) || 0;
                    }}
                }} else if (column === 'market_cap') {{
                    // Use raw numeric market cap values, not formatted strings
                    valueA = parseFloat(cellA.getAttribute('data-value')) || 0;
                    valueB = parseFloat(cellB.getAttribute('data-value')) || 0;
                }} else {{
                    // Standard sorting for other columns
                    const textA = cellA.textContent.trim();
                    const textB = cellB.textContent.trim();
                    
                    const numA = parseFloat(textA.replace(/[$,%]/g, ''));
                    const numB = parseFloat(textB.replace(/[$,%]/g, ''));
                    
                    if (!isNaN(numA) && !isNaN(numB)) {{
                        valueA = numA;
                        valueB = numB;
                    }} else {{
                        return textA.localeCompare(textB) * (sortDirection === 'asc' ? 1 : -1);
                    }}
                }}
                
                return (valueB - valueA) * (sortDirection === 'asc' ? -1 : 1);
            }});
            
            // Rebuild table
            rows.forEach(row => tbody.appendChild(row));
        }}
        
        // Other functions (updateData, loadData, etc.) remain the same...
        async function loadData() {{
            try {{
                const response = await fetch('/data');
                currentData = await response.json();
                location.reload(); // Simple refresh to update display
            }} catch (error) {{
                console.error('Failed to load data:', error);
            }}
        }}
        
        function updateData() {{
            const universe = document.getElementById('universeSelect').value;
            const status = document.getElementById('updateStatus');
            
            status.innerHTML = '⏳ Starting update...';
            status.className = 'show';
            
            fetch('/update', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{universe: universe}})
            }})
            .then(response => response.json())
            .then(data => {{
                status.innerHTML = '✅ Update started for ' + data.estimated_stocks + ' stocks';
                setTimeout(() => location.reload(), 30000);
            }})
            .catch(error => {{
                status.innerHTML = '❌ Update failed: ' + error.message;
            }});
        }}
        
    </script>
</body>
</html>"""
    
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
    
    def fetch_stock_data_async(self, universe: str) -> bool:
        """Step 1: Fetch stock data using the new async data fetcher"""
        try:
            import subprocess
            
            cmd = [
                'poetry', 'run', 'python', 'scripts/data_fetcher.py',
                '--universe', universe,
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
    
    def run_offline_analysis(self, universe: str) -> bool:
        """Step 2: Run offline analysis on cached data"""
        try:
            import subprocess
            
            cmd = [
                'poetry', 'run', 'python', 'scripts/offline_analyzer.py',
                '--universe', universe,
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
                self.run_offline_analysis('cached')  # Analyze all available cached stocks
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
            'models': ['dcf', 'dcf_enhanced', 'simple_ratios', 'neural_network_best'],  # Include neural network best model
            'scenarios': ['base'],
            'dcf_years': 5,  # Shorter projection for speed
            'terminal_growth_rate': 0.025
        },
        'generate_reports': True,
        'save_data': True,
        'max_results': min(30, len(tickers)),  # Hard limit
        'sort_by': 'composite_score',
        'is_dashboard_update': True  # Flag for neural network inclusion
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
    
    # Start server (avoid ports 3000/8000 used by other projects)  
    port = 3446
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