"""
HTMLGenerator - Generates dashboard HTML templates and content.

This component is responsible for:
- Generating complete HTML dashboard templates
- Formatting stock data for display
- Creating progress indicators and status displays
- Providing responsive and interactive UI elements
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class HTMLGenerator:
    """Generates HTML content for the investment dashboard."""
    
    def __init__(self, output_dir: str = "dashboard"):
        """Initialize the HTML generator."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.html_file = self.output_dir / "valuation_dashboard.html"
    
    def generate_dashboard_html(self, stocks_data: Dict, progress_data: Dict, metadata: Dict = None) -> str:
        """
        Generate complete HTML dashboard.
        
        Parameters
        ----------
        stocks_data : Dict
            Dictionary of stock data keyed by ticker
        progress_data : Dict
            Progress tracking information
        metadata : Dict, optional
            Additional metadata for the dashboard
            
        Returns
        -------
        str
            Complete HTML content
        """
        last_updated = metadata.get("last_updated", "Never") if metadata else "Never"
        
        # Generate main content sections
        progress_html = self._generate_progress_section(progress_data)
        summary_html = self._generate_summary_section(stocks_data)
        table_html = self._generate_stock_table(stocks_data)
        
        # Create complete HTML document
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Investment Valuation Dashboard</title>
    <style>
        {self._get_css_styles()}
    </style>
</head>
<body>
    <div class="container">
        <header class="dashboard-header">
            <h1>🔍 Investment Valuation Dashboard</h1>
            <p class="subtitle">Multi-model stock analysis with real-time updates</p>
            <div class="last-updated">Last Updated: <span id="lastUpdated">{last_updated}</span></div>
        </header>
        
        {progress_html}
        
        <div class="controls">
            <div class="universe-selector">
                <label for="universe">Select Universe:</label>
                <select id="universe">
                    <option value="sp500">S&P 500 (Top 25)</option>
                    <option value="dow30">Dow Jones 30</option>
                    <option value="nasdaq100">NASDAQ 100 (Top 25)</option>
                    <option value="custom">Custom Tickers</option>
                </select>
                <input type="text" id="customTickers" placeholder="AAPL,MSFT,GOOGL..." style="display:none;">
            </div>
            <button id="updateButton" onclick="updateDashboard()">🔄 Update Data</button>
        </div>
        
        {summary_html}
        
        <div class="stock-analysis">
            <h2>📈 Stock Analysis Results</h2>
            {table_html}
        </div>
        
        <footer class="dashboard-footer">
            <p>💡 <strong>How to read this dashboard:</strong></p>
            <ul>
                <li><strong>Fair Value:</strong> Estimated intrinsic value per share from each model</li>
                <li><strong>Margin of Safety:</strong> How much upside/downside vs current price</li>
                <li><strong>Models:</strong> DCF (Cash Flow), Enhanced DCF (Dividends), Ratios (Multiples), RIM (Book Value), Multi-Stage DCF (Growth Phases)</li>
                <li><strong>Consensus:</strong> Average of all successful models</li>
            </ul>
            <p class="disclaimer">⚠️ This is for educational purposes. Not investment advice. Do your own research.</p>
        </footer>
    </div>
    
    <script>
        {self._get_javascript()}
    </script>
</body>
</html>"""
        
        return html_content
    
    def _generate_progress_section(self, progress_data: Dict) -> str:
        """Generate the progress section HTML."""
        status = progress_data.get("status", "idle")
        completed = progress_data.get("completed_tasks", 0)
        total = progress_data.get("total_tasks", 0)
        completion_pct = progress_data.get("completion_percentage", 0)
        current_ticker = progress_data.get("current_ticker", "")
        current_model = progress_data.get("current_model", "")
        
        if status == "idle":
            return '''
            <div class="progress-section" style="display: none;" id="progressSection">
                <div class="progress-bar">
                    <div class="progress-fill" style="width: 0%"></div>
                </div>
                <div class="progress-text">Ready to update</div>
            </div>'''
        
        progress_text = f"{completed}/{total} tasks ({completion_pct:.1f}%)"
        if current_ticker and current_model:
            progress_text += f" • Current: {current_ticker} {current_model}"
        
        return f'''
        <div class="progress-section" id="progressSection">
            <div class="progress-bar">
                <div class="progress-fill" style="width: {completion_pct}%"></div>
            </div>
            <div class="progress-text" id="progressText">{progress_text}</div>
        </div>'''
    
    def _generate_summary_section(self, stocks_data: Dict) -> str:
        """Generate the analysis summary section."""
        total_stocks = len(stocks_data)
        completed_stocks = len([s for s in stocks_data.values() if s.get("models_completed", 0) > 0])
        
        # Calculate model success rates
        model_counts = {}
        for stock in stocks_data.values():
            for model in stock.get("valuations", {}):
                model_counts[model] = model_counts.get(model, 0) + 1
        
        summary_items = []
        summary_items.append(f"<div class='summary-item'><strong>{total_stocks}</strong><br>Total Stocks</div>")
        summary_items.append(f"<div class='summary-item'><strong>{completed_stocks}</strong><br>Analyzed</div>")
        
        for model, count in model_counts.items():
            model_name = model.replace('_', ' ').title()
            summary_items.append(f"<div class='summary-item'><strong>{count}</strong><br>{model_name}</div>")
        
        return f'''
        <div class="analysis-summary">
            <h2>📊 Analysis Summary</h2>
            <div class="summary-grid">
                {''.join(summary_items)}
            </div>
        </div>'''
    
    def _generate_stock_table(self, stocks_data: Dict) -> str:
        """Generate the stock analysis table."""
        if not stocks_data:
            return '<p class="no-data">No stock data available. Click "Update Data" to start analysis.</p>'
        
        # Sort stocks by status and performance
        sorted_stocks = self._sort_stocks_for_display(stocks_data)
        
        # Generate table rows
        table_rows = []
        for ticker, stock_data in sorted_stocks:
            row_html = self._generate_stock_row(ticker, stock_data)
            table_rows.append(row_html)
        
        return f'''
        <div class="table-container">
            <table class="stock-table" id="stockTable">
                <thead>
                    <tr>
                        <th onclick="sortTable(0)">Stock 🔄</th>
                        <th onclick="sortTable(1)">Price 🔄</th>
                        <th onclick="sortTable(2)">Status 🔄</th>
                        <th title="Discounted Cash Flow">DCF 🔄</th>
                        <th title="Enhanced DCF with Dividends">Enh. DCF 🔄</th>
                        <th title="Simple Ratios (P/E, P/B)">Ratios 🔄</th>
                        <th title="Residual Income Model">RIM 🔄</th>
                        <th title="Multi-Stage DCF">Multi-DCF 🔄</th>
                        <th onclick="sortTable(8)">Consensus 🔄</th>
                    </tr>
                </thead>
                <tbody>
                    {''.join(table_rows)}
                </tbody>
            </table>
        </div>'''
    
    def _generate_stock_row(self, ticker: str, stock_data: Dict) -> str:
        """Generate a single stock table row."""
        current_price = stock_data.get("current_price", 0)
        valuations = stock_data.get("valuations", {})
        status = stock_data.get("status", "pending")
        status_message = stock_data.get("status_message", "Unknown")
        
        # Format status
        status_html = self._format_status_cell(status, status_message)
        
        # Format valuation columns
        dcf_html = self._format_valuation_cell(valuations.get("dcf", {}))
        enh_dcf_html = self._format_valuation_cell(valuations.get("dcf_enhanced", {}))
        ratios_html = self._format_valuation_cell(valuations.get("simple_ratios", {}))
        rim_html = self._format_valuation_cell(valuations.get("rim", {}))
        multi_dcf_html = self._format_valuation_cell(valuations.get("multi_stage_dcf", {}))
        
        # Calculate consensus
        consensus_html = self._format_consensus_cell(valuations, current_price)
        
        return f'''
        <tr class="stock-row {status}">
            <td><strong>{ticker}</strong></td>
            <td>{self._safe_format(current_price, prefix="$")}</td>
            <td>{status_html}</td>
            <td>{dcf_html}</td>
            <td>{enh_dcf_html}</td>
            <td>{ratios_html}</td>
            <td>{rim_html}</td>
            <td>{multi_dcf_html}</td>
            <td>{consensus_html}</td>
        </tr>'''
    
    def _format_status_cell(self, status: str, message: str) -> str:
        """Format the status cell with icon and tooltip."""
        status_icons = {
            "completed": "✅",
            "analyzing": "🔄", 
            "pending": "⏳",
            "data_missing": "❌",
            "rate_limited": "🚫",
            "model_failed": "⚠️",
        }
        
        icon = status_icons.get(status, "❓")
        display_name = status.replace("_", " ").title()
        
        return f'<span title="{message}">{icon} {display_name}</span>'
    
    def _format_valuation_cell(self, valuation: Dict) -> str:
        """Format a valuation cell with fair value and margin."""
        if valuation.get("failed", False):
            reason = valuation.get("failure_reason", "Model failed")
            short_reason = reason[:30] + "..." if len(reason) > 30 else reason
            return f'<span title="{reason}">❌</span>'
        
        fair_value = valuation.get("fair_value")
        margin = valuation.get("margin_of_safety")
        
        if fair_value is None or fair_value == 0:
            return "-"
        
        fair_value_str = self._safe_format(fair_value, prefix="$")
        margin_str = self._safe_percent(margin)
        
        # Color code the margin
        margin_class = self._get_margin_class(margin)
        
        return f'''
        <div class="valuation-cell">
            <div class="fair-value">{fair_value_str}</div>
            <div class="margin {margin_class}">{margin_str}</div>
        </div>'''
    
    def _format_consensus_cell(self, valuations: Dict, current_price: float) -> str:
        """Format the consensus cell with average valuation."""
        fair_values = []
        for val in valuations.values():
            if not val.get("failed", False):
                fv = val.get("fair_value")
                if fv and isinstance(fv, (int, float)) and fv > 0:
                    fair_values.append(fv)
        
        if not fair_values:
            return "-"
        
        avg_fair_value = sum(fair_values) / len(fair_values)
        avg_margin = (avg_fair_value - current_price) / current_price if current_price > 0 else 0
        
        avg_fair_value_str = self._safe_format(avg_fair_value, prefix="$")
        avg_margin_str = self._safe_percent(avg_margin)
        margin_class = self._get_margin_class(avg_margin)
        
        return f'''
        <div class="consensus-cell">
            <div class="fair-value"><strong>{avg_fair_value_str}</strong></div>
            <div class="margin {margin_class}"><strong>{avg_margin_str}</strong></div>
            <div class="model-count">({len(fair_values)} models)</div>
        </div>'''
    
    def _sort_stocks_for_display(self, stocks_data: Dict) -> List[Tuple[str, Dict]]:
        """Sort stocks for optimal display order."""
        def get_sort_key(stock_item):
            ticker, stock_data = stock_item
            status = stock_data.get("status", "pending")
            
            # Status priority (lower = higher priority)
            status_priority = {
                "completed": 1,
                "analyzing": 2,
                "pending": 3,
                "data_missing": 4,
                "rate_limited": 5,
                "model_failed": 6,
            }.get(status, 7)
            
            # Best margin of safety for secondary sort
            valuations = stock_data.get("valuations", {})
            margins = []
            for val in valuations.values():
                if not val.get("failed", False):
                    margin = val.get("margin_of_safety")
                    if margin is not None:
                        margins.append(margin)
            
            best_margin = max(margins) if margins else -999
            
            return (status_priority, -best_margin)
        
        return sorted(stocks_data.items(), key=get_sort_key)
    
    def _get_margin_class(self, margin: float) -> str:
        """Get CSS class for margin color coding."""
        if margin is None:
            return ""
        elif margin > 0.3:
            return "margin-excellent"
        elif margin > 0.15:
            return "margin-good"
        elif margin > -0.15:
            return "margin-neutral"
        else:
            return "margin-poor"
    
    def _safe_format(self, value: Any, format_str: str = ".2f", placeholder: str = "-", prefix: str = "") -> str:
        """Safely format a numeric value."""
        try:
            if value is None:
                return placeholder
            formatted = f"{float(value):{format_str}}"
            return f"{prefix}{formatted}"
        except (ValueError, TypeError):
            return placeholder
    
    def _safe_percent(self, value: Any, placeholder: str = "-") -> str:
        """Safely format a percentage value."""
        try:
            if value is None:
                return placeholder
            return f"{float(value) * 100:+.1f}%"
        except (ValueError, TypeError):
            return placeholder
    
    def save_html(self, html_content: str):
        """Save HTML content to file."""
        try:
            with open(self.html_file, "w", encoding="utf-8") as f:
                f.write(html_content)
            logger.info(f"Dashboard HTML saved to {self.html_file}")
        except Exception as e:
            logger.error(f"Failed to save HTML: {e}")
    
    def _get_css_styles(self) -> str:
        """Get CSS styles for the dashboard."""
        return """
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background: rgba(255, 255, 255, 0.95);
            min-height: 100vh;
            box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
        }
        
        .dashboard-header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }
        
        .dashboard-header h1 {
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 2.5em;
        }
        
        .subtitle {
            color: #7f8c8d;
            font-size: 1.2em;
            margin-bottom: 10px;
        }
        
        .last-updated {
            color: #95a5a6;
            font-size: 0.9em;
        }
        
        .progress-section {
            margin-bottom: 20px;
            padding: 15px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }
        
        .progress-bar {
            width: 100%;
            height: 20px;
            background: #ecf0f1;
            border-radius: 10px;
            overflow: hidden;
            margin-bottom: 10px;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #3498db, #2ecc71);
            transition: width 0.3s ease;
        }
        
        .progress-text {
            text-align: center;
            font-weight: 500;
            color: #2c3e50;
        }
        
        .controls {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding: 15px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }
        
        .universe-selector select, .universe-selector input {
            padding: 8px 12px;
            border: 2px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
            margin-left: 10px;
        }
        
        #updateButton {
            background: linear-gradient(135deg, #3498db, #2980b9);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 500;
            transition: transform 0.2s;
        }
        
        #updateButton:hover {
            transform: translateY(-2px);
        }
        
        .analysis-summary {
            margin-bottom: 20px;
            padding: 20px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }
        
        .summary-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        
        .summary-item {
            text-align: center;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 6px;
            border-left: 4px solid #3498db;
        }
        
        .stock-analysis {
            margin-bottom: 30px;
        }
        
        .table-container {
            overflow-x: auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }
        
        .stock-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }
        
        .stock-table th {
            background: #34495e;
            color: white;
            padding: 12px 8px;
            text-align: left;
            cursor: pointer;
            user-select: none;
        }
        
        .stock-table th:hover {
            background: #2c3e50;
        }
        
        .stock-table td {
            padding: 10px 8px;
            border-bottom: 1px solid #ecf0f1;
        }
        
        .stock-row:hover {
            background: #f8f9fa;
        }
        
        .stock-row.completed {
            background: rgba(46, 204, 113, 0.1);
        }
        
        .stock-row.analyzing {
            background: rgba(52, 152, 219, 0.1);
        }
        
        .valuation-cell {
            text-align: center;
        }
        
        .fair-value {
            font-weight: 500;
            margin-bottom: 2px;
        }
        
        .margin {
            font-size: 12px;
            padding: 2px 6px;
            border-radius: 3px;
            font-weight: 500;
        }
        
        .margin-excellent {
            background: #d4edda;
            color: #155724;
        }
        
        .margin-good {
            background: #fff3cd;
            color: #856404;
        }
        
        .margin-neutral {
            background: #e2e3e5;
            color: #383d41;
        }
        
        .margin-poor {
            background: #f8d7da;
            color: #721c24;
        }
        
        .consensus-cell {
            text-align: center;
            border-left: 3px solid #3498db;
            padding-left: 8px;
        }
        
        .model-count {
            font-size: 11px;
            color: #7f8c8d;
            margin-top: 2px;
        }
        
        .dashboard-footer {
            margin-top: 30px;
            padding: 20px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
        }
        
        .dashboard-footer ul {
            margin: 10px 0 10px 20px;
        }
        
        .disclaimer {
            margin-top: 15px;
            padding: 10px;
            background: #fff3cd;
            border-radius: 5px;
            color: #856404;
            font-size: 14px;
        }
        
        .no-data {
            text-align: center;
            padding: 40px;
            color: #7f8c8d;
            font-style: italic;
        }
        
        @media (max-width: 768px) {
            .container { padding: 10px; }
            .controls { flex-direction: column; gap: 15px; }
            .summary-grid { grid-template-columns: repeat(2, 1fr); }
            .stock-table { font-size: 12px; }
            .stock-table th, .stock-table td { padding: 6px 4px; }
        }"""
    
    def _get_javascript(self) -> str:
        """Get JavaScript for dashboard interactivity."""
        return """
        let isUpdating = false;
        
        function updateDashboard() {
            if (isUpdating) return;
            
            const universe = document.getElementById('universe').value;
            const customTickers = document.getElementById('customTickers').value;
            const button = document.getElementById('updateButton');
            const progressSection = document.getElementById('progressSection');
            
            // Show progress section and disable button
            progressSection.style.display = 'block';
            button.disabled = true;
            button.textContent = '🔄 Updating...';
            isUpdating = true;
            
            const requestData = { universe: universe };
            if (universe === 'custom' && customTickers) {
                requestData.tickers = customTickers.split(',').map(t => t.trim().toUpperCase());
            }
            
            fetch('/update', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestData)
            })
            .then(response => response.json())
            .then(data => {
                console.log('Update started:', data);
                startProgressPolling();
            })
            .catch(error => {
                console.error('Update failed:', error);
                resetUpdateButton();
            });
        }
        
        function startProgressPolling() {
            const pollInterval = setInterval(() => {
                // Reload the page to get updated data
                location.reload();
            }, 3000);
            
            // Stop polling after 10 minutes
            setTimeout(() => {
                clearInterval(pollInterval);
                resetUpdateButton();
            }, 600000);
        }
        
        function resetUpdateButton() {
            const button = document.getElementById('updateButton');
            button.disabled = false;
            button.textContent = '🔄 Update Data';
            isUpdating = false;
        }
        
        // Universe selector handling
        document.getElementById('universe').addEventListener('change', function() {
            const customInput = document.getElementById('customTickers');
            if (this.value === 'custom') {
                customInput.style.display = 'inline-block';
                customInput.required = true;
            } else {
                customInput.style.display = 'none';
                customInput.required = false;
            }
        });
        
        // Table sorting functionality
        function sortTable(columnIndex) {
            const table = document.getElementById('stockTable');
            const tbody = table.tBodies[0];
            const rows = Array.from(tbody.rows);
            
            // Determine sort direction
            const currentSort = table.getAttribute('data-sort');
            const isAsc = currentSort !== columnIndex + '-asc';
            
            rows.sort((a, b) => {
                const aVal = a.cells[columnIndex].textContent.trim();
                const bVal = b.cells[columnIndex].textContent.trim();
                
                // Try numeric comparison first
                const aNum = parseFloat(aVal.replace(/[$%,]/g, ''));
                const bNum = parseFloat(bVal.replace(/[$%,]/g, ''));
                
                if (!isNaN(aNum) && !isNaN(bNum)) {
                    return isAsc ? aNum - bNum : bNum - aNum;
                }
                
                // Fallback to string comparison
                return isAsc ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
            });
            
            // Re-append sorted rows
            rows.forEach(row => tbody.appendChild(row));
            
            // Update sort indicator
            table.setAttribute('data-sort', columnIndex + (isAsc ? '-asc' : '-desc'));
        }
        
        // Auto-refresh when update is in progress
        document.addEventListener('DOMContentLoaded', function() {
            const progressSection = document.getElementById('progressSection');
            if (progressSection && progressSection.style.display !== 'none') {
                // If progress is visible, start polling
                setTimeout(startProgressPolling, 3000);
            }
        });"""