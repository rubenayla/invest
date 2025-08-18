"""
Investment Dashboard - Live updating HTML dashboard showing valuation model comparisons.

Simple approach:
1. Show existing data immediately 
2. Update incrementally as new data comes in
3. Don't block on slow models/stocks
"""

import json
import os
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

from .dcf import calculate_dcf
from .dcf_enhanced import calculate_enhanced_dcf  
from .simple_ratios import calculate_simple_ratios_valuation

logger = logging.getLogger(__name__)

class ValuationDashboard:
    """Live updating investment dashboard."""
    
    def __init__(self, output_dir: str = "dashboard"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.html_file = self.output_dir / "valuation_dashboard.html"
        self.data_file = self.output_dir / "dashboard_data.json"
        
        # Load existing data if available
        self.data = self._load_existing_data()
        
    def _load_existing_data(self) -> Dict:
        """Load existing dashboard data."""
        if self.data_file.exists():
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    logger.info(f"Loaded existing data for {len(data.get('stocks', {}))} stocks")
                    return data
            except Exception as e:
                logger.warning(f"Could not load existing data: {e}")
        
        return {
            'last_updated': None,
            'stocks': {},
            'model_status': {
                'dcf': 'not_run',
                'dcf_enhanced': 'not_run', 
                'simple_ratios': 'not_run'
            }
        }
    
    def update_dashboard(self, tickers: List[str], timeout_per_stock: int = 30):
        """
        Update dashboard with latest valuations.
        
        Parameters
        ----------
        tickers : List[str]
            Stock tickers to analyze
        timeout_per_stock : int
            Max seconds per stock per model (prevents hanging)
        """
        logger.info(f"Updating dashboard for {len(tickers)} stocks")
        
        # Generate initial HTML with existing data
        self._generate_html()
        print(f"Dashboard available at: {self.html_file.absolute()}")
        
        # Update each stock incrementally
        with ThreadPoolExecutor(max_workers=3) as executor:
            # Submit all valuation tasks
            future_to_info = {}
            
            for ticker in tickers:
                # DCF
                future = executor.submit(self._safe_valuation, ticker, 'dcf', timeout_per_stock)
                future_to_info[future] = (ticker, 'dcf')
                
                # Enhanced DCF
                future = executor.submit(self._safe_valuation, ticker, 'dcf_enhanced', timeout_per_stock)
                future_to_info[future] = (ticker, 'dcf_enhanced')
                
                # Simple Ratios
                future = executor.submit(self._safe_valuation, ticker, 'simple_ratios', timeout_per_stock)
                future_to_info[future] = (ticker, 'simple_ratios')
            
            # Process results as they complete
            completed_count = 0
            total_tasks = len(future_to_info)
            
            for future in as_completed(future_to_info, timeout=timeout_per_stock * len(tickers)):
                ticker, model = future_to_info[future]
                completed_count += 1
                
                try:
                    result = future.result()
                    if result:
                        self._update_stock_data(ticker, model, result)
                        self._generate_html()  # Update HTML immediately
                        logger.info(f"✅ Updated {ticker} {model} ({completed_count}/{total_tasks})")
                    else:
                        logger.warning(f"❌ Failed {ticker} {model}")
                        
                except Exception as e:
                    logger.error(f"❌ Error {ticker} {model}: {e}")
                
                # Save progress
                self._save_data()
        
        self.data['last_updated'] = datetime.now().isoformat()
        self._save_data()
        self._generate_html()
        
        logger.info("Dashboard update complete!")
    
    def _safe_valuation(self, ticker: str, model: str, timeout: int) -> Optional[Dict]:
        """Run valuation with timeout protection."""
        try:
            if model == 'dcf':
                result = calculate_dcf(ticker, verbose=False)
            elif model == 'dcf_enhanced':
                result = calculate_enhanced_dcf(ticker, verbose=False)
            elif model == 'simple_ratios':
                # Simple ratios needs basic stock data
                import yfinance as yf
                stock = yf.Ticker(ticker)
                info = stock.info
                stock_data = {
                    'ticker': ticker,
                    'current_price': info.get('currentPrice'),
                    'pe_ratio': info.get('trailingPE'),
                    'pb_ratio': info.get('priceToBook'),
                    'ps_ratio': info.get('priceToSalesTrailing12Months'),
                    'dividend_yield': info.get('dividendYield'),
                    'ev_ebitda': info.get('enterpriseToEbitda'),
                    'peg_ratio': info.get('pegRatio'),
                    'sector': info.get('sector')
                }
                result = calculate_simple_ratios_valuation(stock_data)
            else:
                return None
            
            # Convert any pandas Series to Python types
            if result:
                result = self._clean_result(result)
            
            return result
            
        except Exception as e:
            logger.warning(f"Valuation failed for {ticker} {model}: {e}")
            return None
    
    def _clean_result(self, result: Dict) -> Dict:
        """Clean result to ensure all values are Python types, not pandas Series."""
        cleaned = {}
        for key, value in result.items():
            if hasattr(value, 'item'):  # pandas scalar
                cleaned[key] = value.item()
            elif hasattr(value, 'iloc') and len(value) > 0:  # pandas Series with data
                cleaned[key] = float(value.iloc[0])
            elif value is None:
                cleaned[key] = 0.0  # Default for None values
            else:
                cleaned[key] = value
        return cleaned
    
    def _safe_format(self, value: Any, format_str: str = ".2f", placeholder: str = "-") -> str:
        """Safely format numeric values with proper type handling."""
        try:
            if value is None or value == 0.0:
                return placeholder
            float_val = float(value)
            if float_val == 0.0:
                return placeholder
            return f"{float_val:{format_str}}"
        except (ValueError, TypeError):
            return placeholder
    
    def _safe_percent(self, value: Any, placeholder: str = "-") -> str:
        """Safely format percentage values with proper type handling."""
        try:
            if value is None:
                return placeholder
            
            float_val = float(value)
            if float_val == 0.0:
                return placeholder
                
            # All values from our models are already in decimal format (0.15 = 15%)
            # No need to divide by 100
            return f"{float_val:.1%}"
        except (ValueError, TypeError):
            return placeholder
    
    def _update_stock_data(self, ticker: str, model: str, result: Dict):
        """Update stock data with new valuation."""
        if ticker not in self.data['stocks']:
            self.data['stocks'][ticker] = {
                'ticker': ticker,
                'current_price': result.get('current_price', 0),
                'valuations': {}
            }
        
        # Normalize margin of safety to decimal format
        margin_value = result.get('margin_of_safety', result.get('upside_potential', 0))
        
        # Simple ratios returns percentage format (multiply by 100), others return decimal
        if model == 'simple_ratios' and margin_value != 0:
            margin_value = margin_value / 100  # Convert -63.81 to -0.6381
        
        # Store valuation result
        self.data['stocks'][ticker]['valuations'][model] = {
            'fair_value': result.get('fair_value_per_share', result.get('valuation_price', 0)),
            'current_price': result.get('current_price', 0),
            'margin_of_safety': margin_value,
            'confidence': result.get('confidence', 'medium'),
            'last_updated': datetime.now().isoformat(),
            
            # Model-specific data
            'model_data': result
        }
        
        # Update current price
        if result.get('current_price'):
            self.data['stocks'][ticker]['current_price'] = result['current_price']
        
        # Update model status
        self.data['model_status'][model] = 'completed'
    
    def _save_data(self):
        """Save dashboard data to JSON."""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save data: {e}")
    
    def _generate_html(self):
        """Generate HTML dashboard."""
        html_content = self._create_html_template()
        
        try:
            with open(self.html_file, 'w') as f:
                f.write(html_content)
        except Exception as e:
            logger.error(f"Could not write HTML: {e}")
    
    def _create_html_template(self) -> str:
        """Create HTML dashboard template with current data."""
        last_updated = self.data.get('last_updated', 'Never')
        stocks = self.data.get('stocks', {})
        
        # Generate stock table rows
        table_rows = ""
        for ticker, stock_data in stocks.items():
            current_price = stock_data.get('current_price', 0)
            valuations = stock_data.get('valuations', {})
            
            # Get valuations for each model
            dcf_val = valuations.get('dcf', {})
            enh_dcf_val = valuations.get('dcf_enhanced', {})
            ratios_val = valuations.get('simple_ratios', {})
            
            # Use class methods for safe formatting
            
            # Format valuation cells with proper handling for missing data
            def format_valuation_cell(val_dict):
                fair_value = val_dict.get('fair_value')
                if fair_value is None or fair_value == 0:
                    return "-", "-"
                return f"${self._safe_format(fair_value)}", self._safe_percent(val_dict.get('margin_of_safety'))
            
            dcf_value, dcf_margin = format_valuation_cell(dcf_val)
            enh_dcf_value, enh_dcf_margin = format_valuation_cell(enh_dcf_val) 
            ratios_value, ratios_margin = format_valuation_cell(ratios_val)
            
            table_rows += f"""
            <tr>
                <td class="ticker">{ticker}</td>
                <td class="price">${self._safe_format(current_price, placeholder="Loading...")}</td>
                <td class="valuation">{dcf_value}</td>
                <td class="margin">{dcf_margin}</td>
                <td class="valuation">{enh_dcf_value}</td>
                <td class="margin">{enh_dcf_margin}</td>
                <td class="valuation">{ratios_value}</td>
                <td class="margin">{ratios_margin}</td>
            </tr>
            """
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Investment Valuation Dashboard</title>
    <meta charset="utf-8">
    <meta http-equiv="refresh" content="10">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .status {{ background: #ecf0f1; padding: 15px; border-radius: 8px; margin-bottom: 20px; }}
        table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        th {{ background: #34495e; color: white; padding: 12px; text-align: left; }}
        td {{ padding: 10px; border-bottom: 1px solid #ecf0f1; }}
        .ticker {{ font-weight: bold; color: #2c3e50; }}
        .price {{ color: #27ae60; font-weight: bold; }}
        .valuation {{ color: #3498db; }}
        .margin {{ font-weight: bold; }}
        .positive {{ color: #27ae60; }}
        .negative {{ color: #e74c3c; }}
        .model-header {{ background: #3498db !important; }}
        .last-updated {{ color: #7f8c8d; font-size: 0.9em; }}
        .placeholder {{ color: #95a5a6; font-style: italic; }}
        .loading {{ color: #f39c12; font-style: italic; }}
        
        /* Tooltip styles */
        .tooltip {{
            position: relative;
            cursor: help;
            border-bottom: 1px dotted #666;
        }}
        
        .tooltip .tooltiptext {{
            visibility: hidden;
            width: 280px;
            background-color: #2c3e50;
            color: white;
            text-align: left;
            border-radius: 6px;
            padding: 10px;
            position: fixed;
            z-index: 999999;
            bottom: auto;
            top: auto;
            left: 50%;
            margin-left: -140px;
            opacity: 0;
            transition: opacity 0.3s;
            font-size: 0.9em;
            line-height: 1.4;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
            pointer-events: none;
        }}
        
        .tooltip .tooltiptext::after {{
            content: "";
            position: absolute;
            top: 100%;
            left: 50%;
            margin-left: -5px;
            border-width: 5px;
            border-style: solid;
            border-color: #2c3e50 transparent transparent transparent;
        }}
        
        .tooltip:hover .tooltiptext {{
            visibility: visible;
            opacity: 1;
        }}
        
        /* Override any table stacking context */
        table {{
            position: relative;
            z-index: 1;
        }}
        
        th {{
            position: relative;
            z-index: 2;
        }}
        
        /* Refresh button hover effect */
        .refresh-btn {{
            background: #3498db;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.9em;
            transition: background-color 0.2s ease;
        }}
        
        .refresh-btn:hover {{
            background: #2980b9;
        }}
        
        .refresh-btn:active {{
            background: #21618c;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 Investment Valuation Dashboard</h1>
        <p>Comparing DCF, Enhanced DCF, and Simple Ratios valuation models</p>
    </div>
    
    <div class="status">
        <p><strong>Last Updated:</strong> <span class="last-updated">{last_updated}</span></p>
        <p><strong>Stocks Analyzed:</strong> {len(stocks)}</p>
        <p><em>Auto-refreshes every 10 seconds while updating...</em></p>
        
        <div style="margin-top: 15px; padding: 10px; background: #34495e; border-radius: 5px; color: white;">
            <p style="margin: 0; font-size: 0.9em;">
                <strong>🚀 To start dashboard:</strong> 
                <code style="background: #2c3e50; padding: 2px 8px; border-radius: 3px; font-family: monospace;">
                    poetry run python scripts/dashboard_server.py
                </code>
            </p>
            <p style="margin: 8px 0 0 0; font-size: 0.8em; color: #bdc3c7;">
                Then visit <strong>http://localhost:8080</strong> and use the update button below
            </p>
            <button onclick="updateDashboard()" 
                    class="refresh-btn" style="margin-top: 8px;" id="updateBtn">
                🔄 Update Data
            </button>
        </div>
    </div>
    
    <table>
        <thead>
            <tr>
                <th rowspan="2">
                    <span class="tooltip">Ticker
                        <span class="tooltiptext">Stock symbol traded on the exchange</span>
                    </span>
                </th>
                <th rowspan="2">
                    <span class="tooltip">Current Price
                        <span class="tooltiptext">Latest market price per share from live data feeds</span>
                    </span>
                </th>
                <th colspan="2" class="model-header">
                    <span class="tooltip">Traditional DCF
                        <span class="tooltiptext">Standard Discounted Cash Flow model. Projects future cash flows and discounts to present value. Assumes all companies reinvest equally efficiently.</span>
                    </span>
                </th>
                <th colspan="2" class="model-header">
                    <span class="tooltip">Enhanced DCF
                        <span class="tooltiptext">Improved DCF that accounts for dividend policy and capital allocation efficiency. Separates value from dividends vs reinvestment based on company-specific ROIC.</span>
                    </span>
                </th>
                <th colspan="2" class="model-header">
                    <span class="tooltip">Simple Ratios
                        <span class="tooltiptext">Benjamin Graham-style valuation using P/E, P/B, P/S ratios with sector adjustments. Based on mean reversion of fundamental multiples.</span>
                    </span>
                </th>
            </tr>
            <tr>
                <th>
                    <span class="tooltip">Fair Value
                        <span class="tooltiptext">Estimated intrinsic value per share based on the model's assumptions and calculations</span>
                    </span>
                </th>
                <th>
                    <span class="tooltip">Upside/Downside
                        <span class="tooltiptext">Percentage difference between fair value and current price. Positive = undervalued (potential upside), Negative = overvalued (potential downside)</span>
                    </span>
                </th>
                <th>
                    <span class="tooltip">Fair Value
                        <span class="tooltiptext">Enhanced DCF estimated intrinsic value considering dividend policy and reinvestment efficiency</span>
                    </span>
                </th>
                <th>
                    <span class="tooltip">Upside/Downside
                        <span class="tooltiptext">Enhanced DCF margin of safety. Shows how much the stock could gain/lose based on dividend-aware valuation</span>
                    </span>
                </th>
                <th>
                    <span class="tooltip">Fair Value
                        <span class="tooltiptext">Ratio-based fair value using sector-adjusted P/E, P/B, P/S multiples and dividend yield expectations</span>
                    </span>
                </th>
                <th>
                    <span class="tooltip">Upside/Downside
                        <span class="tooltiptext">Simple ratios margin of safety. Based on how current ratios compare to historical/sector averages</span>
                    </span>
                </th>
            </tr>
        </thead>
        <tbody>
            {table_rows}
        </tbody>
    </table>
    
    <div class="status" style="margin-top: 20px;">
        <h3>📊 Model Comparison Notes:</h3>
        <ul>
            <li><strong>Traditional DCF:</strong> Standard discounted cash flow analysis</li>
            <li><strong>Enhanced DCF:</strong> Accounts for dividend policy and reinvestment efficiency</li>
            <li><strong>Simple Ratios:</strong> Benjamin Graham-style ratio-based valuation</li>
        </ul>
        <p style="margin-top: 15px; font-size: 0.9em; color: #7f8c8d;">
            💡 <strong>Tip:</strong> Hover over column headers for detailed explanations of each metric
        </p>
    </div>
    
    <script>
        // Color-code margins and handle placeholders
        document.querySelectorAll('.margin').forEach(cell => {{
            const text = cell.textContent.trim();
            if (text === '-') {{
                cell.classList.add('placeholder');
            }} else {{
                const value = parseFloat(text);
                if (value > 0) {{
                    cell.classList.add('positive');
                }} else if (value < 0) {{
                    cell.classList.add('negative');
                }}
            }}
        }});
        
        // Style placeholder values
        document.querySelectorAll('.valuation').forEach(cell => {{
            if (cell.textContent.trim() === '-') {{
                cell.classList.add('placeholder');
            }}
        }});
        
        // Style loading prices
        document.querySelectorAll('.price').forEach(cell => {{
            if (cell.textContent.includes('Loading')) {{
                cell.classList.add('loading');
            }}
        }});
        
        // Dynamic tooltip positioning
        document.querySelectorAll('.tooltip').forEach(tooltip => {{
            const tooltipText = tooltip.querySelector('.tooltiptext');
            
            tooltip.addEventListener('mouseenter', function(e) {{
                const rect = tooltip.getBoundingClientRect();
                tooltipText.style.left = (rect.left + rect.width/2 - 140) + 'px';
                tooltipText.style.top = (rect.top - 10) + 'px';
                tooltipText.style.transform = 'translateY(-100%)';
            }});
        }});
        
        // Dashboard update function
        async function updateDashboard() {{
            const btn = document.getElementById('updateBtn');
            const originalText = btn.innerHTML;
            btn.innerHTML = '⏳ Updating...';
            btn.disabled = true;
            
            try {{
                // Make request to update endpoint
                const response = await fetch('/update', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                    }}
                }});
                
                if (response.ok) {{
                    btn.innerHTML = '✅ Updated!';
                    setTimeout(() => {{
                        window.location.reload();
                    }}, 1000);
                }} else {{
                    throw new Error('Update failed');
                }}
            }} catch (error) {{
                btn.innerHTML = '❌ Update failed - use command line';
                console.error('Update error:', error);
            }}
            
            setTimeout(() => {{
                btn.innerHTML = originalText;
                btn.disabled = false;
            }}, 3000);
        }}
    </script>
</body>
</html>
        """


def create_dashboard(tickers: List[str] = None) -> str:
    """
    Create and update valuation dashboard.
    
    Parameters
    ----------
    tickers : List[str], optional
        Tickers to analyze. If None, uses default set.
        
    Returns
    -------
    str
        Path to generated HTML dashboard
    """
    if tickers is None:
        tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'JNJ', 'JPM', 'PG', 'KO']
    
    dashboard = ValuationDashboard()
    dashboard.update_dashboard(tickers)
    
    return str(dashboard.html_file.absolute())


if __name__ == "__main__":
    # Example usage
    html_path = create_dashboard()
    print(f"Dashboard created: {html_path}")
    print("Open in browser to view live updates!")