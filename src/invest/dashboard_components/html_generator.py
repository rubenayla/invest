"""
HTMLGenerator - Generates dashboard HTML templates and content.

This component is responsible for:
- Generating complete HTML dashboard templates
- Formatting stock data for display
- Creating progress indicators and status displays
- Providing responsive and interactive UI elements
"""

import logging
import math
from pathlib import Path
from typing import Any, Dict, List, Tuple

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
            <div style="margin-top: 15px; display: flex; gap: 10px; justify-content: center;">
                <a href="https://rubenayla.github.io/invest/models/" target="_blank" rel="noopener noreferrer" style="color: white; text-decoration: none; background: rgba(33,150,243,0.8); padding: 8px 16px; border-radius: 6px; font-weight: 500; transition: background 0.3s;" onmouseover="this.style.background='rgba(33,150,243,1)'" onmouseout="this.style.background='rgba(33,150,243,0.8)'">📚 Model Documentation</a>
                <button onclick="exportToCSV()" style="color: white; background: rgba(40,167,69,0.8); border: none; padding: 8px 16px; border-radius: 6px; font-weight: 500; cursor: pointer; transition: background 0.3s;" onmouseover="this.style.background='rgba(40,167,69,1)'" onmouseout="this.style.background='rgba(40,167,69,0.8)'">📥 Export to CSV</button>
            </div>
        </header>

        {progress_html}

        <div class="controls">
            <div class="universe-selector">
                <label for="universe">Select Universe:</label>
                <select id="universe">
                    <option value="all_universes">All Universes Combined</option>
                    <option value="nyse">NYSE - All Listed Companies</option>
                    <option value="sp500">S&P 500</option>
                    <option value="russell2000">Russell 2000 Sample</option>
                    <option value="global_mix">Global Mix (US+International)</option>
                    <option value="small_cap_focus">Small Cap Focus</option>
                    <option value="japan_major">Japan Major Stocks</option>
                    <option value="uk_ftse">UK FTSE 100</option>
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
                <li><strong>Models:</strong> DCF (Cash Flow), Enhanced DCF (Dividends), Growth DCF (Reinvestment-Adjusted), Ratios (Multiples), RIM (Book Value), Multi-Stage DCF (Growth Phases), Black-Scholes-Merton (Structural equity option model), GBM (Gradient Boosted Machine ranking models - 6 variants: Full 1y/3y, Lite 1y/3y, Opportunistic 1y/3y)</li>
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
            <table class="stock-table results-table" id="stockTable">
                <thead>
                    <tr>
                        <th title="Stock ticker symbol">Stock</th>
                        <th title="Current market price per share">Price</th>
                        <th title="Analysis completion status">Status</th>
                        <th title="Discounted Cash Flow - Values future cash flows discounted to present value">DCF</th>
                        <th title="Enhanced DCF with Dividend Policy - Accounts for dividend vs reinvestment strategies">Enh. DCF</th>
                        <th title="Growth-Adjusted DCF - Separates maintenance CapEx from growth CapEx, solving traditional DCF bias against reinvestment">Growth DCF</th>
                        <th title="Simple Ratios - P/E, P/B, and other multiple-based valuations">Ratios</th>
                        <th title="Residual Income Model - Values excess returns above cost of equity based on book value">RIM</th>
                        <th title="Multi-Stage DCF - Models different growth phases over time">Multi-DCF</th>
                        <th title="Black-Scholes-Merton structural model - values equity as a call option on firm assets">B-S</th>
                        <th title="Gradient Boosted Machine 1-year ranking (LightGBM with 464 features, Rank IC 0.61)">GBM 1y</th>
                        <th title="Gradient Boosted Machine 3-year ranking (LightGBM with 464 features, Rank IC 0.59)">GBM 3y</th>
                        <th title="Gradient Boosted Machine Lite 1-year ranking (LightGBM with 247 features, Rank IC 0.59)">GBM Lite 1y</th>
                        <th title="Gradient Boosted Machine Lite 3-year ranking (LightGBM with 247 features, Rank IC 0.61)">GBM Lite 3y</th>
                        <th title="Opportunistic GBM 1-year - Peak return prediction within 2 years (Rank IC 0.61)">GBM Opp 1y</th>
                        <th title="Opportunistic GBM 3-year - Peak return prediction within 3 years (Rank IC 0.64)">GBM Opp 3y</th>
                        <!-- NN column disabled: near-zero test correlation (2026-02-21) -->
                        <th title="Consensus valuation - Average of all successful model results">Consensus</th>
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
        stock_data.get("status_message", "Unknown")
        company_name = stock_data.get("company_name", ticker)

        # Create meaningful status based on what actually worked
        working_models = []
        failed_models = []

        model_names = {
            "dcf": "DCF",
            "dcf_enhanced": "Enh.DCF",
            "growth_dcf": "Growth",
            "simple_ratios": "Ratios",
            "rim": "RIM",
            "multi_stage_dcf": "Multi",
            "black_scholes": "B-S",
            "gbm_1y": "GBM1y",
            "gbm_3y": "GBM3y",
            "gbm_lite_1y": "GBM-Lite1y",
            "gbm_lite_3y": "GBM-Lite3y",
            "gbm_opportunistic_1y": "GBM-Opp1y",
            "gbm_opportunistic_3y": "GBM-Opp3y",
            # "multi_horizon_nn": "NN",  # Disabled: near-zero test correlation (2026-02-21)
            "ensemble": "Consensus"
        }

        for model_key, result in valuations.items():
            # Skip non-dict values like current_price
            if not isinstance(result, dict):
                continue
            model_name = model_names.get(model_key, model_key.upper())
            if result and result.get("fair_value"):
                working_models.append(model_name)
            else:
                failed_models.append(model_name)

        # Create better status
        if working_models:
            if len(working_models) >= 3:
                new_status = "completed"
                new_message = f"✅ Working: {', '.join(working_models[:3])}{'...' if len(working_models) > 3 else ''}"
            else:
                new_status = "partial"
                new_message = f"⚠️ Working: {', '.join(working_models)} | Failed: {', '.join(failed_models[:2])}"
        else:
            new_status = "failed"
            new_message = f"❌ All models failed or unsuitable for {ticker}"

        # Format status
        status_html = self._format_status_cell(new_status, new_message)

        # Format valuation columns
        dcf_html = self._format_valuation_cell(valuations.get("dcf", {}), current_price)
        enh_dcf_html = self._format_valuation_cell(valuations.get("dcf_enhanced", {}), current_price)
        growth_dcf_html = self._format_valuation_cell(valuations.get("growth_dcf", {}), current_price)
        ratios_html = self._format_valuation_cell(valuations.get("simple_ratios", {}), current_price)
        rim_html = self._format_valuation_cell(valuations.get("rim", {}), current_price)
        multi_dcf_html = self._format_valuation_cell(valuations.get("multi_stage_dcf", {}), current_price)
        black_scholes_html = self._format_valuation_cell(valuations.get("black_scholes", {}), current_price, show_confidence=True)

        # Format GBM predictions (6 models)
        gbm_1y_html = self._format_valuation_cell(valuations.get("gbm_1y", {}), current_price, show_confidence=True)
        gbm_3y_html = self._format_valuation_cell(valuations.get("gbm_3y", {}), current_price, show_confidence=True)
        gbm_lite_1y_html = self._format_valuation_cell(valuations.get("gbm_lite_1y", {}), current_price, show_confidence=True)
        gbm_lite_3y_html = self._format_valuation_cell(valuations.get("gbm_lite_3y", {}), current_price, show_confidence=True)
        gbm_opp_1y_html = self._format_valuation_cell(valuations.get("gbm_opportunistic_1y", {}), current_price, show_confidence=True)
        gbm_opp_3y_html = self._format_valuation_cell(valuations.get("gbm_opportunistic_3y", {}), current_price, show_confidence=True)
        # NN column disabled: near-zero test correlation (2026-02-21)
        # nn_html = self._format_valuation_cell(valuations.get("multi_horizon_nn", {}), current_price, show_confidence=True)

        # Calculate consensus
        consensus_html = self._format_consensus_cell(valuations, current_price)

        return f'''
        <tr class="stock-row {status}">
            <td><strong title="{company_name}">{ticker}</strong></td>
            <td>{self._safe_format(current_price, prefix="$")}</td>
            <td>{status_html}</td>
            <td>{dcf_html}</td>
            <td>{enh_dcf_html}</td>
            <td>{growth_dcf_html}</td>
            <td>{ratios_html}</td>
            <td>{rim_html}</td>
            <td>{multi_dcf_html}</td>
            <td>{black_scholes_html}</td>
            <td>{gbm_1y_html}</td>
            <td>{gbm_3y_html}</td>
            <td>{gbm_lite_1y_html}</td>
            <td>{gbm_lite_3y_html}</td>
            <td>{gbm_opp_1y_html}</td>
            <td>{gbm_opp_3y_html}</td>
            <td>{consensus_html}</td>
        </tr>'''

    def _format_status_cell(self, status: str, message: str) -> str:
        """Format the status cell with icon and tooltip."""
        status_icons = {
            "completed": "✅",
            "partial": "⚠️",
            "failed": "❌",
            "analyzing": "🔄",
            "pending": "⏳",
            "data_missing": "❌",
            "rate_limited": "🚫",
            "model_failed": "⚠️",
        }

        icon = status_icons.get(status, "❓")

        # Custom display names for better readability
        display_names = {
            "completed": "Complete",
            "partial": "Partial",
            "failed": "Failed",
            "analyzing": "Running",
            "pending": "Pending"
        }

        display_name = display_names.get(status, status.replace("_", " ").title())

        return f'<span title="{message}">{icon} {display_name}</span>'

    def _format_valuation_cell(self, valuation: Dict, current_price: float = None, show_confidence: bool = False) -> str:
        """Format a valuation cell with fair value, margin, and ratio."""
        if valuation.get("failed", False):
            reason = valuation.get("failure_reason", "Model failed")
            reason[:30] + "..." if len(reason) > 30 else reason
            return f'<span title="{reason}">❌</span>'

        fair_value = valuation.get("fair_value")
        margin = valuation.get("margin_of_safety")

        if fair_value is None or fair_value == 0:
            # Show error message in tooltip if available
            error_msg = valuation.get("error_message") or valuation.get("error", "No valuation available")
            return f'<span title="{error_msg}">-</span>'

        fair_value_str = self._safe_format(fair_value, prefix="$")
        margin_str = self._safe_percent(margin)

        # Calculate ratio if current price is available
        ratio_str = ""
        if current_price and current_price > 0:
            ratio = fair_value / current_price
            ratio_str = f'<div class="ratio">{ratio:.2f}x</div>'

        # Color code the margin
        margin_class = self._get_margin_class(margin)

        confidence_badge = ''
        if show_confidence:
            conf = valuation.get('confidence')
            conf_value = None
            if isinstance(conf, (int, float)):
                conf_value = conf
            elif isinstance(conf, str):
                conf_lower = conf.lower()
                mapping = {'high': 0.9, 'medium': 0.5, 'low': 0.2}
                conf_value = mapping.get(conf_lower, None)
            if conf_value is None:
                details = valuation.get('details', {})
                percentile = details.get('ranking_percentile')
                if isinstance(percentile, (int, float)):
                    percentile = percentile / 100 if percentile > 1 else percentile
                    conf_value = max(percentile, 1 - percentile)
            if conf_value is not None:
                conf_value = min(max(conf_value, 0.0), 1.0)
                conf_label = f'{conf_value * 100:.1f}%'
                # color: high green, medium yellow, low red
                if conf_value >= 0.75:
                    conf_style = 'background: #d4edda; color: #155724'
                elif conf_value >= 0.4:
                    conf_style = 'background: #fff3cd; color: #856404'
                else:
                    conf_style = 'background: #f8d7da; color: #721c24'
                confidence_badge = f'<div class="confidence-badge" style="{conf_style}; font-size: 10px; padding: 2px 4px; border-radius: 3px; margin-top: 2px; font-weight: 600;">Confidence: {conf_label}</div>'

        return f'''
        <div class="valuation-cell">
            <div class="fair-value">{fair_value_str}</div>
            <div class="margin {margin_class}">{margin_str}</div>
            {ratio_str}
            {confidence_badge}
        </div>'''

    def _format_nn_cell(self, valuation: Dict, current_price: float = None) -> str:
        """Format neural network valuation cell with confidence indicator."""
        if not valuation or not valuation.get('suitable'):
            reason = valuation.get('error', 'No prediction') if valuation else 'No data'
            reason[:30] + '...' if len(reason) > 30 else reason
            return f'<span title="{reason}">-</span>'

        fair_value = valuation.get('fair_value')
        margin = valuation.get('margin_of_safety')
        valuation.get('confidence', 'unknown')

        if fair_value is None or fair_value == 0:
            return '-'

        # Get details for tooltip
        details = valuation.get('details', {})
        conf_std = details.get('confidence_std', 0)
        conf_lower = details.get('confidence_lower_95', 0)
        conf_upper = details.get('confidence_upper_95', 0)

        fair_value_str = self._safe_format(fair_value, prefix='$')
        margin_str = self._safe_percent(margin)

        # Confidence badge - show std as percentage instead of categorical label
        # Color based on std thresholds: <5% = green, <15% = yellow, >=15% = red
        if conf_std < 0.05:
            conf_style = 'background: #d4edda; color: #155724'  # Green
        elif conf_std < 0.15:
            conf_style = 'background: #fff3cd; color: #856404'  # Yellow
        else:
            conf_style = 'background: #f8d7da; color: #721c24'  # Red

        conf_label = f'σ={conf_std:.1%}'  # Show actual std percentage

        # Tooltip with detailed confidence info
        tooltip = f'Uncertainty (Std): {conf_std:.1%} | 95% CI: [{conf_lower:.1f}%, {conf_upper:.1f}%]'

        # Calculate ratio if current price is available
        ratio_str = ''
        if current_price and current_price > 0:
            ratio = fair_value / current_price
            ratio_str = f'<div class="ratio">{ratio:.2f}x</div>'

        # Color code the margin
        margin_class = self._get_margin_class(margin)

        return f'''
        <div class="valuation-cell" title="{tooltip}">
            <div class="fair-value">{fair_value_str}</div>
            <div class="margin {margin_class}">{margin_str}</div>
            {ratio_str}
            <div class="confidence-badge" style="{conf_style}; font-size: 10px; padding: 2px 4px; border-radius: 3px; margin-top: 2px; font-weight: 600;">{conf_label}</div>
        </div>'''

    def _format_multi_horizon_cells(self, nn_valuation: Dict, current_price: float) -> Tuple[str, str, str, str, str]:
        """Format multi-horizon NN predictions into 5 separate cells (1m, 3m, 6m, 1y, 2y)."""
        if not nn_valuation or not nn_valuation.get('suitable'):
            empty = '-'
            return empty, empty, empty, empty, empty

        details = nn_valuation.get('details', {})
        predictions = details.get('predictions', {})
        fair_values = details.get('fair_values', {})
        confidence_scores = details.get('confidence_scores', {})

        horizons = [
            ('1m', '1-month'),
            ('3m', '3-month'),
            ('6m', '6-month'),
            ('1y', '1-year'),
            ('2y', '2-year')
        ]

        cells = []
        for horizon_key, horizon_label in horizons:
            prediction = predictions.get(horizon_key)
            fair_value = fair_values.get(horizon_key)
            confidence = confidence_scores.get(horizon_key, 0)

            if prediction is None or fair_value is None:
                cells.append('-')
                continue

            # Calculate margin of safety
            margin = (fair_value - current_price) / current_price if current_price > 0 else 0

            # Format values
            pred_str = f'{prediction:.2f}%'
            fv_str = self._safe_format(fair_value, prefix='$')
            margin_str = self._safe_percent(margin)
            conf_str = f'{confidence * 100:.1f}%'

            # Color code the margin
            margin_class = self._get_margin_class(margin)

            # Create tooltip with all details
            tooltip = f'{horizon_label}: Return {pred_str}, FV {fv_str}, Margin {margin_str}, Confidence {conf_str}'

            cells.append(f'''
            <div class="nn-cell" title="{tooltip}">
                <div class="prediction">{pred_str}</div>
                <div class="margin {margin_class}">{margin_str}</div>
            </div>''')

        return tuple(cells)

    def _format_consensus_cell(self, valuations: Dict, current_price: float) -> str:
        """Format the consensus cell with log-return weighted valuation."""
        from ..valuation.consensus import compute_consensus_from_dicts

        consensus = compute_consensus_from_dicts(valuations, current_price)
        if consensus is None:
            return "-"

        avg_fair_value = consensus.fair_value
        avg_margin = consensus.margin_of_safety
        avg_ratio = avg_fair_value / current_price if current_price > 0 else 0

        avg_fair_value_str = self._safe_format(avg_fair_value, prefix="$")
        avg_margin_str = self._safe_percent(avg_margin)
        avg_ratio_str = f"{avg_ratio:.2f}x" if avg_ratio > 0 else "-"
        margin_class = self._get_margin_class(avg_margin)

        # Confidence badge based on consensus confidence label
        conf_label = consensus.confidence
        if conf_label == 'high':
            conf_style = 'background: #d4edda; color: #155724'
        elif conf_label == 'medium':
            conf_style = 'background: #fff3cd; color: #856404'
        else:
            conf_style = 'background: #f8d7da; color: #721c24'
        confidence_badge = f'<div class="confidence-badge" style="{conf_style}; font-size: 10px; padding: 2px 4px; border-radius: 3px; margin-top: 2px; font-weight: 600;">{conf_label.title()}</div>'

        return f'''
        <div class="consensus-cell">
            <div class="fair-value"><strong>{avg_fair_value_str}</strong></div>
            <div class="margin {margin_class}"><strong>{avg_margin_str}</strong></div>
            <div class="ratio"><strong>{avg_ratio_str}</strong></div>
            {confidence_badge}
            <div class="model-count">({consensus.num_models} models)</div>
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
            for key, val in valuations.items():
                # Skip non-dict values like current_price
                if not isinstance(val, dict):
                    continue
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
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
        }

        .container {
            width: 100%;
            margin: 0;
            padding: 20px;
            background: rgba(255, 255, 255, 0.95);
            min-height: 100vh;
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
            overflow-y: auto;
            height: calc(100vh - 220px);
            min-height: 180px;
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
            position: sticky;
            top: 0;
            z-index: 10;
            background: #34495e;
            color: white;
            padding: 12px 8px;
            text-align: left;
            cursor: pointer;
            user-select: none;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .stock-table th:hover {
            background: #2c3e50;
        }

        .stock-table th.sorted,
        .stock-table th.sort-asc,
        .stock-table th.sort-desc {
            background: #2c3e50;
        }

        .stock-table th.sort-asc::after {
            content: ' ↑';
            color: #bdc3c7;
        }

        .stock-table th.sort-desc::after {
            content: ' ↓';
            color: #bdc3c7;
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

        .ratio {
            font-size: 11px;
            color: #6c757d;
            font-weight: 500;
            margin-top: 1px;
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
            .table-container { height: 60vh; min-height: 140px; }
        }"""

    def _get_javascript(self) -> str:
        """Get JavaScript for dashboard interactivity."""
        return """
        let isUpdating = false;

        // Simple, reliable table sorting
        document.addEventListener('DOMContentLoaded', function() {
            const table = document.getElementById('stockTable');
            if (!table) return;

            // Add click handlers to all headers
            const headers = table.querySelectorAll('th');
            headers.forEach((header, columnIndex) => {
                header.style.cursor = 'pointer';
                header.style.userSelect = 'none';
                header.addEventListener('click', () => sortTableByColumn(columnIndex));
            });
        });

        function sortTableByColumn(columnIndex) {
            const table = document.getElementById('stockTable');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));

            // Determine sort direction
            const header = table.querySelectorAll('th')[columnIndex];
            const isAscending = !header.classList.contains('sort-asc');

            // Clear all sort classes
            table.querySelectorAll('th').forEach(h => {
                h.classList.remove('sort-asc', 'sort-desc');
            });

            // Add sort class to current header
            header.classList.add(isAscending ? 'sort-asc' : 'sort-desc');

            // Sort rows
            rows.sort((rowA, rowB) => {
                const cellA = rowA.cells[columnIndex];
                const cellB = rowB.cells[columnIndex];

                if (!cellA || !cellB) return 0;

                let textA = cellA.textContent.trim();
                let textB = cellB.textContent.trim();

                // Check for empty/placeholder values - always put these last
                const isEmptyA = textA === '-' || textA === 'N/A' || textA === '';
                const isEmptyB = textB === '-' || textB === 'N/A' || textB === '';

                if (isEmptyA && isEmptyB) return 0;  // Both empty, equal
                if (isEmptyA) return 1;              // A is empty, put it last
                if (isEmptyB) return -1;             // B is empty, put it last

                // Extract ratio values from ratio divs if they exist
                const ratioA = cellA.querySelector('.ratio');
                const ratioB = cellB.querySelector('.ratio');
                const marginA = cellA.querySelector('.margin');
                const marginB = cellB.querySelector('.margin');

                let comparison = 0;

                if (ratioA && ratioB) {
                    // Both have ratio data - sort by expected value to market price ratio
                    const ratioValueA = parseFloat(ratioA.textContent.replace(/[x]/g, ''));
                    const ratioValueB = parseFloat(ratioB.textContent.replace(/[x]/g, ''));

                    if (!isNaN(ratioValueA) && !isNaN(ratioValueB)) {
                        comparison = ratioValueB - ratioValueA; // Higher ratios first (more undervalued)
                    } else {
                        // Fallback to margin percentage if ratio values are invalid
                        const percentA = parseFloat(marginA?.textContent.replace(/[%+]/g, '') || '0');
                        const percentB = parseFloat(marginB?.textContent.replace(/[%+]/g, '') || '0');
                        comparison = percentB - percentA;
                    }
                } else if (marginA && marginB) {
                    // Fallback to margin percentage sorting
                    const percentA = parseFloat(marginA.textContent.replace(/[%+]/g, ''));
                    const percentB = parseFloat(marginB.textContent.replace(/[%+]/g, ''));
                    comparison = percentB - percentA;
                } else if (marginA || marginB) {
                    // One has percentage, one doesn't - percentage goes first
                    comparison = marginA ? -1 : 1;
                } else {
                    // No percentages, sort by dollar values or text
                    const numA = parseFloat(textA.replace(/[$,%]/g, ''));
                    const numB = parseFloat(textB.replace(/[$,%]/g, ''));

                    if (!isNaN(numA) && !isNaN(numB)) {
                        comparison = numB - numA; // Higher values first
                    } else {
                        comparison = textA.localeCompare(textB);
                    }
                }

                return isAscending ? comparison : -comparison;
            });

            // Rebuild table
            rows.forEach(row => tbody.appendChild(row));
        }

        function updateDashboard() {
            if (isUpdating) return;

            const universe = document.getElementById('universe').value;
            const customTickers = document.getElementById('customTickers').value;
            const button = document.getElementById('updateButton');
            const progressSection = document.getElementById('progressSection');

            // Show progress section and disable button
            if (progressSection) progressSection.style.display = 'block';
            if (button) {
                button.disabled = true;
                button.textContent = '🔄 Updating...';
            }
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
                location.reload();
            }, 3000);

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

        // Export to CSV function
        function exportToCSV() {
            const table = document.getElementById('stockTable');
            if (!table) {
                alert('No table found to export');
                return;
            }

            const rows = [];

            // Get headers
            const headers = [];
            table.querySelectorAll('thead th').forEach(th => {
                headers.push(th.textContent.trim().replace(/[↑↓]/g, ''));
            });
            rows.push(headers);

            // Get all visible rows (respects filtering)
            table.querySelectorAll('tbody tr').forEach(tr => {
                if (tr.style.display !== 'none') {
                    const row = [];
                    tr.querySelectorAll('td').forEach(td => {
                        // Clean up cell content
                        let text = td.textContent.trim();
                        // Remove extra whitespace
                        text = text.replace(/\\s+/g, ' ');
                        // Escape quotes and wrap in quotes if contains comma
                        if (text.includes(',') || text.includes('"') || text.includes('\\n')) {
                            text = '"' + text.replace(/"/g, '""') + '"';
                        }
                        row.push(text);
                    });
                    rows.push(row);
                }
            });

            // Create CSV content
            const csvContent = rows.map(row => row.join(',')).join('\\n');

            // Create blob and download
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            const url = URL.createObjectURL(blob);

            // Generate filename with current date
            const date = new Date().toISOString().split('T')[0];
            link.setAttribute('href', url);
            link.setAttribute('download', `dashboard_export_${date}.csv`);
            link.style.visibility = 'hidden';

            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            console.log(`Exported ${rows.length - 1} rows to CSV`);
        }


        // Auto-refresh when update is in progress
        document.addEventListener('DOMContentLoaded', function() {
            const progressSection = document.getElementById('progressSection');
            if (progressSection && progressSection.style.display !== 'none') {
                // If progress is visible, start polling
                setTimeout(startProgressPolling, 3000);
            }
        });"""
