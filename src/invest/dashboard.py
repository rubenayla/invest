"""
Investment Dashboard - Live updating HTML dashboard showing valuation model comparisons.

Simple approach:
1. Show existing data immediately
2. Update incrementally as new data comes in
3. Don't block on slow models/stocks
"""

import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .dcf import calculate_dcf
from .dcf_enhanced import calculate_enhanced_dcf
from .simple_ratios import calculate_simple_ratios_valuation
from .rim import calculate_rim
from .multi_stage_dcf import calculate_multi_stage_dcf
from .config.constants import ANALYSIS_LIMITS

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
                with open(self.data_file, "r") as f:
                    data = json.load(f)
                    logger.info(f"Loaded existing data for {len(data.get('stocks', {}))} stocks")
                    return data
            except Exception as e:
                logger.warning(f"Could not load existing data: {e}")

        return {
            "last_updated": None,
            "stocks": {},
            "model_status": {
                "dcf": "not_run",
                "dcf_enhanced": "not_run",
                "simple_ratios": "not_run",
                "rim": "not_run",
                "multi_stage_dcf": "not_run",
            },
        }

    def _initialize_stocks(self, tickers: List[str]):
        """Initialize all stocks with pending status."""
        for ticker in tickers:
            if ticker not in self.data["stocks"]:
                self.data["stocks"][ticker] = {
                    "ticker": ticker,
                    "status": "pending",
                    "status_message": "Waiting to be analyzed",
                    "current_price": None,
                    "valuations": {},
                    "models_attempted": 0,
                    "models_completed": 0,
                    "last_attempt": None,
                }
            # Reset status for existing stocks
            else:
                self.data["stocks"][ticker]["status"] = "pending"
                self.data["stocks"][ticker]["status_message"] = "Waiting to be analyzed"
                self.data["stocks"][ticker]["models_attempted"] = 0
                self.data["stocks"][ticker]["models_completed"] = 0

    def _prioritize_stock_updates(self, tickers: List[str]) -> List[str]:
        """Prioritize stocks based on update needs and data freshness."""

        def get_priority_score(ticker):
            """Calculate priority score for stock (lower = higher priority)."""
            stock_data = self.data["stocks"].get(ticker, {})

            # Priority 1: Never analyzed (no valuations)
            if not stock_data.get("valuations"):
                return (1, ticker)

            # Priority 2: Incomplete analysis (< 5 models)
            completed_models = len(stock_data.get("valuations", {}))
            if completed_models < 5:
                return (2, -completed_models, ticker)  # Fewer models = higher priority

            # Priority 3: Failed previously (rate limited, data missing)
            status = stock_data.get("status", "pending")
            if status in ["rate_limited", "data_missing", "model_failed"]:
                return (3, ticker)

            # Priority 4: Older data (parse last_attempt timestamp)
            last_attempt = stock_data.get("last_attempt")
            if last_attempt:
                # More recent = lower priority (higher timestamp sort value)
                return (4, last_attempt, ticker)

            # Priority 5: Complete and recent (lowest priority)
            return (5, ticker)

        # Sort by priority score
        prioritized = sorted(tickers, key=get_priority_score)

        # Log prioritization for debugging
        logger.info(f"Prioritized {len(prioritized)} stocks:")
        logger.info(
            f"  Never analyzed: {len([t for t in tickers if not self.data['stocks'].get(t, {}).get('valuations')])}"
        )
        logger.info(
            f"  Incomplete: {len([t for t in tickers if 0 < len(self.data['stocks'].get(t, {}).get('valuations', {})) < 5])}"
        )
        logger.info(
            f"  Failed previously: {len([t for t in tickers if self.data['stocks'].get(t, {}).get('status') in ['rate_limited', 'data_missing', 'model_failed']])}"
        )

        return prioritized

    def update_dashboard(self, tickers: List[str], timeout_per_stock: int = ANALYSIS_LIMITS.DEFAULT_TIMEOUT_PER_STOCK):
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

        # Initialize all stocks with pending status
        self._initialize_stocks(tickers)

        # Generate initial HTML with all stocks
        self._generate_html()
        print(f"Dashboard available at: {self.html_file.absolute()}")

        # Prioritize stocks that need updates
        prioritized_tickers = self._prioritize_stock_updates(tickers)

        # Update each stock incrementally with fewer workers to avoid rate limits
        with ThreadPoolExecutor(max_workers=2) as executor:
            # Submit all valuation tasks in priority order
            future_to_info = {}

            for ticker in prioritized_tickers:
                # DCF
                future = executor.submit(self._safe_valuation, ticker, "dcf", timeout_per_stock)
                future_to_info[future] = (ticker, "dcf")

                # Enhanced DCF
                future = executor.submit(
                    self._safe_valuation, ticker, "dcf_enhanced", timeout_per_stock
                )
                future_to_info[future] = (ticker, "dcf_enhanced")

                # Simple Ratios
                future = executor.submit(
                    self._safe_valuation, ticker, "simple_ratios", timeout_per_stock
                )
                future_to_info[future] = (ticker, "simple_ratios")

                # RIM (Residual Income Model)
                future = executor.submit(self._safe_valuation, ticker, "rim", timeout_per_stock)
                future_to_info[future] = (ticker, "rim")
                
                # Multi-Stage DCF
                future = executor.submit(self._safe_valuation, ticker, "multi_stage_dcf", timeout_per_stock)
                future_to_info[future] = (ticker, "multi_stage_dcf")

            # Process results as they complete
            completed_count = 0
            total_tasks = len(future_to_info)

            # Initialize progress tracking
            self.data["progress"] = {
                "completed": 0,
                "total": total_tasks,
                "status": "running",
                "current_ticker": "",
                "stocks_completed": 0,
                "total_stocks": len(tickers),
            }

            for future in as_completed(future_to_info, timeout=timeout_per_stock * len(tickers)):
                ticker, model = future_to_info[future]
                completed_count += 1

                # Update progress tracking
                self.data["progress"]["completed"] = completed_count
                self.data["progress"]["current_ticker"] = ticker
                stocks_with_data = len(
                    [t for t in self.data["stocks"] if self.data["stocks"][t].get("valuations")]
                )
                self.data["progress"]["stocks_completed"] = stocks_with_data

                # Update stock status to analyzing
                self._update_stock_status(ticker, "analyzing", f"Processing {model} model")

                try:
                    result = future.result()
                    if result and not result.get("failed", False):
                        # Successful valuation
                        self._update_stock_data(ticker, model, result)
                        self._generate_html()  # Update HTML immediately
                        logger.info(
                            f"✅ Updated {ticker} {model} ({completed_count}/{total_tasks})"
                        )
                    elif result and result.get("failed", False):
                        # Model rejected/failed - still save the failure result
                        self._update_stock_data(ticker, model, result)
                        self._generate_html()
                        logger.warning(f"❌ Model rejected for {ticker} {model}: {result.get('failure_reason', 'Unknown reason')}")
                    else:
                        self._handle_failed_valuation(ticker, model, "Model returned no result")
                        logger.warning(f"❌ Failed {ticker} {model}")

                except Exception as e:
                    self._handle_failed_valuation(ticker, model, str(e))
                    logger.error(f"❌ Error {ticker} {model}: {e}")

                # Save progress
                self._save_data()

        # Mark analysis as completed
        self.data["progress"]["status"] = "completed"
        self.data["progress"]["completed"] = total_tasks
        self.data["last_updated"] = datetime.now().isoformat()
        self._save_data()
        self._generate_html()

        logger.info("Dashboard update complete!")

    def _safe_valuation(self, ticker: str, model: str, timeout: int) -> Optional[Dict]:
        """Run valuation with timeout protection."""
        try:
            if model == "dcf":
                result = calculate_dcf(ticker, verbose=False)
            elif model == "dcf_enhanced":
                result = calculate_enhanced_dcf(ticker, verbose=False)
            elif model == "simple_ratios":
                # Simple ratios needs basic stock data
                import yfinance as yf

                stock = yf.Ticker(ticker)
                info = stock.info
                stock_data = {
                    "ticker": ticker,
                    "current_price": info.get("currentPrice"),
                    "pe_ratio": info.get("trailingPE"),
                    "pb_ratio": info.get("priceToBook"),
                    "ps_ratio": info.get("priceToSalesTrailing12Months"),
                    "dividend_yield": info.get("dividendYield"),
                    "ev_ebitda": info.get("enterpriseToEbitda"),
                    "peg_ratio": info.get("pegRatio"),
                    "sector": info.get("sector"),
                }
                result = calculate_simple_ratios_valuation(stock_data)
            elif model == "rim":
                result = calculate_rim(ticker, verbose=False)
            elif model == "multi_stage_dcf":
                result = calculate_multi_stage_dcf(ticker, verbose=False)
            elif model == "monte_carlo":
                # Use smaller iteration count for dashboard to avoid timeouts
                result = calculate_monte_carlo_valuation(ticker, iterations=500, verbose=False)
            else:
                return None

            # Convert any pandas Series to Python types
            if result:
                result = self._clean_result(result)

            return result

        except Exception as e:
            logger.warning(f"Valuation failed for {ticker} {model}: {e}")
            # Return failure result instead of None to show in dashboard
            return {
                "failed": True,
                "failure_reason": str(e),
                "fair_value": None,
                "margin_of_safety": None
            }

    def _clean_result(self, result: Dict) -> Dict:
        """Clean result to ensure all values are Python types, not pandas Series."""
        cleaned = {}
        for key, value in result.items():
            if hasattr(value, "item"):  # pandas scalar
                cleaned[key] = value.item()
            elif hasattr(value, "iloc") and len(value) > 0:  # pandas Series with data
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

    def _format_stock_analysis_summary(self, stocks_dict) -> str:
        """Format detailed stock analysis summary with breakdown by status."""
        if not stocks_dict:
            return "<p><strong>📊 Stocks:</strong> No stocks loaded</p>"
        
        # Count stocks by status
        status_counts = {}
        completed_stocks = 0
        failed_stocks = 0
        analyzing_stocks = 0
        pending_stocks = 0
        
        # Convert dict to items if needed
        if isinstance(stocks_dict, dict):
            stock_items = list(stocks_dict.items())
        else:
            stock_items = list(stocks_dict)
            
        for ticker, stock_data in stock_items:
            status = stock_data.get("status", "pending")
            valuations = stock_data.get("valuations", {})
            
            # Count by completion status
            if status == "completed":
                completed_stocks += 1
            elif status in ["data_missing", "rate_limited", "model_failed"]:
                failed_stocks += 1
            elif status == "analyzing":
                analyzing_stocks += 1
            else:
                pending_stocks += 1
            
            # Track detailed status counts
            status_counts[status] = status_counts.get(status, 0) + 1
        
        total_stocks = len(stock_items)
        
        # Create summary with color-coded status
        return f"""
        <div style="background: #f8f9fa; padding: 12px; border-radius: 6px; margin: 8px 0;">
            <p style="margin: 0 0 8px 0;"><strong>📊 Stock Analysis Summary:</strong></p>
            <div style="display: flex; flex-wrap: wrap; gap: 15px; font-size: 0.9em;">
                <div><strong>🎯 Total:</strong> <span style="color: #2c3e50;">{total_stocks}</span></div>
                <div><strong>✅ Completed:</strong> <span style="color: #27ae60;">{completed_stocks}</span></div>
                <div><strong>🔄 Analyzing:</strong> <span style="color: #f39c12;">{analyzing_stocks}</span></div>
                <div><strong>⏳ Pending:</strong> <span style="color: #95a5a6;">{pending_stocks}</span></div>
                <div><strong>❌ Failed:</strong> <span style="color: #e74c3c;">{failed_stocks}</span></div>
            </div>
            <div style="margin-top: 8px; padding: 6px; background: #ecf0f1; border-radius: 3px; font-size: 0.85em; color: #7f8c8d;">
                <strong>Progress:</strong> {completed_stocks + analyzing_stocks}/{total_stocks} stocks have started analysis ({((completed_stocks + analyzing_stocks) / total_stocks * 100):.1f}%)
            </div>
        </div>
        """

    def _format_progress_display(self, progress: Dict) -> str:
        """Format progress information for HTML display."""
        status = progress.get("status", "not_started")

        if status == "not_started":
            return "<p><strong>📊 Analysis Status:</strong> Ready to start</p>"

        elif status == "running":
            completed = progress.get("completed", 0)
            total = progress.get("total", 0)
            stocks_done = progress.get("stocks_completed", 0)
            total_stocks = progress.get("total_stocks", 0)
            current = progress.get("current_ticker", "")

            if total > 0:
                task_percent = (completed / total) * 100
                stock_percent = (stocks_done / total_stocks) * 100 if total_stocks > 0 else 0

                return f"""
                <p><strong>🔄 Analysis Running:</strong></p>
                <div style="background: #3498db; color: white; padding: 8px; border-radius: 4px; margin: 5px 0;">
                    <div>📈 <strong>Tasks:</strong> {completed:,}/{total:,} ({task_percent:.1f}%)</div>
                    <div>🏢 <strong>Stocks:</strong> {stocks_done}/{total_stocks} ({stock_percent:.1f}%)</div>
                    <div>⚡ <strong>Current:</strong> {current}</div>
                    <div style="background: rgba(255,255,255,0.2); height: 6px; border-radius: 3px; margin-top: 5px;">
                        <div style="background: #27ae60; height: 100%; width: {task_percent:.1f}%; border-radius: 3px;"></div>
                    </div>
                </div>
                """
            else:
                return "<p><strong>🔄 Analysis Starting...</strong></p>"

        elif status == "completed":
            total = progress.get("total", 0)
            return f"""
            <p><strong>✅ Analysis Complete!</strong> Processed {total:,} tasks</p>
            """

        return "<p><strong>📊 Analysis Status:</strong> Unknown</p>"

    def _update_stock_status(self, ticker: str, status: str, message: str):
        """Update stock status and message."""
        if ticker in self.data["stocks"]:
            self.data["stocks"][ticker]["status"] = status
            self.data["stocks"][ticker]["status_message"] = message
            self.data["stocks"][ticker]["last_attempt"] = datetime.now().isoformat()

    def _handle_failed_valuation(self, ticker: str, model: str, error_message: str):
        """Handle failed valuation attempt."""
        if ticker not in self.data["stocks"]:
            return

        self.data["stocks"][ticker]["models_attempted"] += 1

        # Determine failure type and status
        if "Rate limited" in error_message or "Too Many Requests" in error_message:
            status = "rate_limited"
            message = "API rate limit exceeded"
        elif "Missing essential" in error_message:
            status = "data_missing"
            message = "Essential financial data unavailable"
        else:
            status = "model_failed"
            message = f"Model calculation failed: {error_message[:50]}..."

        self._update_stock_status(ticker, status, message)

    def _update_stock_data(self, ticker: str, model: str, result: Dict):
        """Update stock data with new valuation."""
        if ticker not in self.data["stocks"]:
            self.data["stocks"][ticker] = {
                "ticker": ticker,
                "status": "pending",
                "status_message": "Waiting to be analyzed",
                "current_price": result.get("current_price", 0),
                "valuations": {},
                "models_attempted": 0,
                "models_completed": 0,
                "last_attempt": None,
            }

        # Normalize margin of safety to decimal format
        margin_value = result.get("margin_of_safety", result.get("upside_potential", 0))

        # Simple ratios returns percentage format (multiply by 100), others return decimal
        if model == "simple_ratios" and margin_value != 0:
            margin_value = margin_value / 100  # Convert -63.81 to -0.6381

        # Store valuation result with failure handling
        valuation_data = {
            "fair_value": result.get("fair_value_per_share", result.get("valuation_price", 0)),
            "current_price": result.get("current_price", 0),
            "margin_of_safety": margin_value,
            "confidence": result.get("confidence", "medium"),
            "last_updated": datetime.now().isoformat(),
            # Model-specific data
            "model_data": result,
        }
        
        # If model failed, add failure info at top level for dashboard display
        if result.get("failed", False):
            valuation_data["failed"] = True
            valuation_data["failure_reason"] = result.get("failure_reason", "Model failed")
        
        self.data["stocks"][ticker]["valuations"][model] = valuation_data

        # Update completion tracking
        self.data["stocks"][ticker]["models_completed"] += 1
        self.data["stocks"][ticker]["models_attempted"] += 1

        # Update current price
        if result.get("current_price"):
            self.data["stocks"][ticker]["current_price"] = result["current_price"]

        # Update status based on completion
        completed = self.data["stocks"][ticker]["models_completed"]
        if completed >= 5:
            self._update_stock_status(
                ticker, "completed", f"All {completed} models completed successfully"
            )
        else:
            self._update_stock_status(ticker, "analyzing", f"{completed}/5 models completed")

        # Update model status
        self.data["model_status"][model] = "completed"

    def _save_data(self):
        """Save dashboard data to JSON."""
        try:
            with open(self.data_file, "w") as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save data: {e}")

    def _generate_html(self):
        """Generate HTML dashboard."""
        html_content = self._create_html_template()

        try:
            with open(self.html_file, "w") as f:
                f.write(html_content)
        except Exception as e:
            logger.error(f"Could not write HTML: {e}")

    def _create_html_template(self) -> str:
        """Create HTML dashboard template with current data."""
        last_updated = self.data.get("last_updated", "Never")
        stocks = self.data.get("stocks", {})
        progress = self.data.get(
            "progress",
            {
                "status": "not_started",
                "completed": 0,
                "total": 0,
                "stocks_completed": 0,
                "total_stocks": 0,
            },
        )

        # Sort stocks by status priority, then by best valuation
        def get_sort_key(stock_item):
            """Get sort key for stock (status priority + best margin)."""
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

            # Best margin of safety
            valuations = stock_data.get("valuations", {})
            margins = []
            for model_data in valuations.values():
                margin = model_data.get("margin_of_safety")
                if margin is not None:
                    margins.append(margin)

            best_margin = max(margins) if margins else -999

            # Return tuple: (status_priority, -best_margin) for sorting
            return (status_priority, -best_margin)

        # Sort stocks by status then by valuation
        sorted_stocks = sorted(stocks.items(), key=get_sort_key)

        # Generate stock table rows
        table_rows = ""
        for ticker, stock_data in sorted_stocks:
            current_price = stock_data.get("current_price", 0)
            valuations = stock_data.get("valuations", {})
            status = stock_data.get("status", "pending")
            status_message = stock_data.get("status_message", "Unknown")

            # Get valuations for each model
            dcf_val = valuations.get("dcf", {})
            enh_dcf_val = valuations.get("dcf_enhanced", {})
            ratios_val = valuations.get("simple_ratios", {})
            rim_val = valuations.get("rim", {})
            multi_stage_val = valuations.get("multi_stage_dcf", {})

            # Use class methods for safe formatting

            # Format valuation cells with proper handling for missing data and failures
            def format_valuation_cell(val_dict):
                # Check if model failed
                if val_dict.get("failed", False):
                    failure_reason = val_dict.get("failure_reason", "Model failed")
                    # Truncate long error messages for display
                    short_reason = failure_reason[:50] + "..." if len(failure_reason) > 50 else failure_reason
                    return f'<span title="{failure_reason}">❌</span>', f'<span title="{failure_reason}">❌</span>'
                
                fair_value = val_dict.get("fair_value")
                if fair_value is None or fair_value == 0:
                    return "-", "-"
                return f"${self._safe_format(fair_value)}", self._safe_percent(
                    val_dict.get("margin_of_safety")
                )

            dcf_value, dcf_margin = format_valuation_cell(dcf_val)
            enh_dcf_value, enh_dcf_margin = format_valuation_cell(enh_dcf_val)
            ratios_value, ratios_margin = format_valuation_cell(ratios_val)
            rim_value, rim_margin = format_valuation_cell(rim_val)
            multi_stage_value, multi_stage_margin = format_valuation_cell(multi_stage_val)

            # Format status with appropriate styling
            status_icons = {
                "completed": "✅",
                "analyzing": "🔄",
                "pending": "⏳",
                "data_missing": "❌",
                "rate_limited": "🚫",
                "model_failed": "⚠️",
            }
            status_names = {
                "completed": "Completed",
                "analyzing": "Analyzing",
                "pending": "Pending",
                "data_missing": "Data Missing",
                "rate_limited": "Rate Limited",
                "model_failed": "Model Failed",
            }
            status_icon = status_icons.get(status, "❓")
            status_name = status_names.get(status, "Unknown")
            status_class = f"status-{status.replace('_', '-')}"

            # Combine status name with message for tooltip
            tooltip_text = f"{status_name}: {status_message}"

            # Format current price based on availability
            price_display = f"${self._safe_format(current_price)}" if current_price else "-"

            table_rows += f"""
            <tr class="{status_class}">
                <td class="ticker">{ticker}</td>
                <td class="status" title="{tooltip_text}">{status_icon}</td>
                <td class="price">{price_display}</td>
                <td class="valuation">{dcf_value}</td>
                <td class="margin">{dcf_margin}</td>
                <td class="valuation">{enh_dcf_value}</td>
                <td class="margin">{enh_dcf_margin}</td>
                <td class="valuation">{ratios_value}</td>
                <td class="margin">{ratios_margin}</td>
                <td class="valuation">{rim_value}</td>
                <td class="margin">{rim_margin}</td>
                <td class="valuation">{multi_stage_value}</td>
                <td class="margin">{multi_stage_margin}</td>
            </tr>
            """

        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Investment Valuation Dashboard</title>
    <meta charset="utf-8">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
        .status {{ background: #ecf0f1; padding: 15px; border-radius: 8px; margin-bottom: 20px; }}
        table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        th {{ background: #34495e; color: white; padding: 12px; text-align: left; }}
        th.sortable {{ cursor: pointer; user-select: none; position: relative; }}
        th.sortable:hover {{ background: #2c3e50; }}
        th.sortable::after {{ content: ' ↕️'; font-size: 12px; opacity: 0.7; }}
        th.sortable.asc::after {{ content: ' ▲'; }}
        th.sortable.desc::after {{ content: ' ▼'; }}
        td {{ padding: 10px; border-bottom: 1px solid #ecf0f1; }}
        .ticker {{ font-weight: bold; color: #2c3e50; }}
        .status {{ text-align: center; font-size: 1.2em; cursor: help; }}
        .price {{ color: #27ae60; font-weight: bold; }}
        .valuation {{ color: #3498db; }}
        .margin {{ font-weight: bold; }}
        .positive {{ color: #27ae60; }}
        .negative {{ color: #e74c3c; }}
        .model-header {{ background: #3498db !important; }}
        .last-updated {{ color: #7f8c8d; font-size: 0.9em; }}
        .placeholder {{ color: #95a5a6; font-style: italic; }}
        .loading {{ color: #f39c12; font-style: italic; }}

        /* Status-based row styling */
        .status-completed {{ background-color: rgba(39, 174, 96, 0.1); }}
        .status-analyzing {{ background-color: rgba(52, 152, 219, 0.1); }}
        .status-pending {{ background-color: rgba(241, 196, 15, 0.1); }}
        .status-data-missing {{ background-color: rgba(231, 76, 60, 0.1); }}
        .status-rate-limited {{ background-color: rgba(155, 89, 182, 0.1); }}
        .status-model-failed {{ background-color: rgba(230, 126, 34, 0.1); }}

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
        <p>Comparing 5 valuation models: DCF, Enhanced DCF, Simple Ratios, RIM, and Multi-Stage DCF</p>
    </div>

    <div class="status">
        <p><strong>Last Updated:</strong> <span class="last-updated">{last_updated}</span></p>
        {self._format_stock_analysis_summary(stocks)}

        <div id="progress-section">
            {self._format_progress_display(progress)}
        </div>

        <div style="display: flex; align-items: center; gap: 10px; margin: 10px 0;">
            <p style="margin: 0;"><em>Auto-refresh:</em></p>
            <button onclick="toggleAutoRefresh()" class="refresh-btn" id="autoRefreshBtn" style="font-size: 0.8em;">
                ⏸️ Pause
            </button>
            <span id="refreshStatus" style="font-size: 0.9em; color: #7f8c8d;">Active (10s)</span>
        </div>

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
            
            <div style="margin: 12px 0; padding: 8px; background: #2c3e50; border-radius: 3px;">
                <label for="universeSelect" style="font-size: 0.9em; color: #ecf0f1; margin-right: 8px;">
                    📈 Stock Universe:
                </label>
                <select id="universeSelect" style="padding: 4px 8px; border-radius: 3px; border: none; background: #ecf0f1; font-size: 0.9em;">
                    <option value="all_universes">🌎 ALL UNIVERSES (~900+ stocks) ⚡</option>
                    <option value="sp500">🇺🇸 S&P 500 (~500 stocks)</option>
                    <option value="russell2000">🇺🇸 Russell 2000 Sample (~80 stocks)</option>
                    <option value="sp600">🇺🇸 S&P SmallCap 600 (~60 stocks)</option>
                    <option value="nasdaq_small">🇺🇸 NASDAQ Small Cap (~60 stocks)</option>
                    <option value="growth_stocks">🚀 Emerging Growth (~60 stocks)</option>
                    <option value="japan_major">🇯🇵 Japan Major (~35 stocks)</option>
                    <option value="japan_topix30">🇯🇵 TOPIX Core 30 (~30 stocks)</option>
                    <option value="japan_buffett">🇯🇵 Buffett's Japan (~15 stocks)</option>
                    <option value="uk_ftse">🇬🇧 UK FTSE 100 (~22 stocks)</option>
                    <option value="germany_dax">🇩🇪 German DAX (~14 stocks)</option>
                    <option value="international_buffett">🌍 Buffett International (~40 stocks)</option>
                    <option value="global_mix">🌍 Global Mix (~180 stocks)</option>
                    <option value="small_cap_focus">🔍 Small Cap Focus (~100 stocks)</option>
                </select>
            </div>
            
            <button onclick="updateDashboard()"
                    class="refresh-btn" style="margin-top: 8px;" id="updateBtn">
                🔄 Update Data
            </button>
        </div>
    </div>

    <table>
        <thead>
            <tr>
                <th rowspan="2" class="sortable" onclick="sortTable(0, 'text')">
                    <span class="tooltip">Ticker
                        <span class="tooltiptext">Stock symbol traded on the exchange</span>
                    </span>
                </th>
                <th rowspan="2" class="sortable" onclick="sortTable(1, 'text')">
                    <span class="tooltip">Status
                        <span class="tooltiptext">Analysis status: ✅ Completed, 🔄 Analyzing, ⏳ Pending, ❌ Data Missing, 🚫 Rate Limited, ⚠️ Model Failed</span>
                    </span>
                </th>
                <th rowspan="2" class="sortable" onclick="sortTable(2, 'number')">
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
                <th colspan="2" class="model-header">
                    <span class="tooltip">RIM (Residual Income Model)
                        <span class="tooltiptext">Values companies based on ROE vs Cost of Equity. Excellent for financial companies and mature businesses with stable book values.</span>
                    </span>
                </th>
                <th colspan="2" class="model-header">
                    <span class="tooltip">Multi-Stage DCF
                        <span class="tooltiptext">Advanced DCF with realistic growth phases: High Growth → Transition → Terminal. Adapts to company size, industry maturity, and competitive position.</span>
                    </span>
                </th>
            </tr>
            <tr>
                <th class="sortable" onclick="sortTable(3, 'currency')">
                    <span class="tooltip">Fair Value
                        <span class="tooltiptext">Estimated intrinsic value per share based on the model's assumptions and calculations</span>
                    </span>
                </th>
                <th class="sortable" onclick="sortTable(4, 'percent')">
                    <span class="tooltip">Upside/Downside
                        <span class="tooltiptext">Percentage difference between fair value and current price. Positive = undervalued (potential upside), Negative = overvalued (potential downside)</span>
                    </span>
                </th>
                <th class="sortable" onclick="sortTable(5, 'currency')">
                    <span class="tooltip">Fair Value
                        <span class="tooltiptext">Enhanced DCF estimated intrinsic value considering dividend policy and reinvestment efficiency</span>
                    </span>
                </th>
                <th class="sortable" onclick="sortTable(6, 'percent')">
                    <span class="tooltip">Upside/Downside
                        <span class="tooltiptext">Enhanced DCF margin of safety. Shows how much the stock could gain/lose based on dividend-aware valuation</span>
                    </span>
                </th>
                <th class="sortable" onclick="sortTable(7, 'currency')">
                    <span class="tooltip">Fair Value
                        <span class="tooltiptext">Ratio-based fair value using sector-adjusted P/E, P/B, P/S multiples and dividend yield expectations</span>
                    </span>
                </th>
                <th class="sortable" onclick="sortTable(8, 'percent')">
                    <span class="tooltip">Upside/Downside
                        <span class="tooltiptext">Simple ratios margin of safety. Based on how current ratios compare to historical/sector averages</span>
                    </span>
                </th>
                <th class="sortable" onclick="sortTable(9, 'currency')">
                    <span class="tooltip">Fair Value
                        <span class="tooltiptext">RIM fair value based on book value plus present value of residual income (ROE above cost of equity)</span>
                    </span>
                </th>
                <th class="sortable" onclick="sortTable(10, 'percent')">
                    <span class="tooltip">Upside/Downside
                        <span class="tooltiptext">RIM margin of safety. Perfect for banks and asset-heavy companies where book value is meaningful</span>
                    </span>
                </th>
                <th class="sortable" onclick="sortTable(11, 'currency')">
                    <span class="tooltip">Fair Value
                        <span class="tooltiptext">Multi-stage DCF fair value using realistic growth phases adapted to company size and industry maturity</span>
                    </span>
                </th>
                <th class="sortable" onclick="sortTable(12, 'percent')">
                    <span class="tooltip">Upside/Downside
                        <span class="tooltiptext">Multi-stage DCF margin of safety. More realistic than linear growth models for most companies</span>
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
            <li><strong>RIM:</strong> Residual Income Model - perfect for banks and asset-heavy companies</li>
            <li><strong>Multi-Stage DCF:</strong> Advanced DCF with realistic growth phases - adapts to company maturity</li>
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
            const universeSelect = document.getElementById('universeSelect');
            const selectedUniverse = universeSelect ? universeSelect.value : 'sp500';
            const universeName = universeSelect ? universeSelect.options[universeSelect.selectedIndex].text : 'S&P 500';
            
            const originalText = btn.innerHTML;
            btn.innerHTML = '⏳ Updating...';
            btn.disabled = true;

            try {{
                // Make request to update endpoint with selected universe
                const response = await fetch('/update', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                    }},
                    body: JSON.stringify({{
                        universe: selectedUniverse
                    }})
                }});

                if (response.ok) {{
                    const result = await response.json();
                    btn.innerHTML = `🚀 Analyzing ${{universeName}}...`;
                    btn.style.background = '#f39c12';
                    
                    // Show universe info in console for debugging
                    console.log(`Started analysis of ${{result.estimated_stocks}} stocks from ${{result.universe}}`);
                    
                    setTimeout(() => {{
                        btn.innerHTML = '🔄 Update Data';
                        btn.style.background = '#3498db';
                        btn.disabled = false;
                    }}, 5000);
                    // Don't reload immediately - let user see progress
                }} else {{
                    throw new Error('Update failed');
                }}
            }} catch (error) {{
                btn.innerHTML = '❌ Update failed - use command line';
                console.error('Update error:', error);
                setTimeout(() => {{
                    btn.innerHTML = originalText;
                    btn.disabled = false;
                }}, 3000);
            }}
        }}

        // Table sorting functionality
        function sortTable(columnIndex, dataType) {{
            const table = document.querySelector('table');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            const headers = table.querySelectorAll('th.sortable');
            const currentHeader = headers[columnIndex];

            // Determine sort direction
            let ascending = true;
            if (currentHeader.classList.contains('asc')) {{
                ascending = false;
            }}

            // Clear all sort indicators
            headers.forEach(header => {{
                header.classList.remove('asc', 'desc');
            }});

            // Set current sort indicator
            currentHeader.classList.add(ascending ? 'asc' : 'desc');

            // Save sort state to localStorage
            localStorage.setItem('dashboardSortColumn', columnIndex);
            localStorage.setItem('dashboardSortDirection', ascending ? 'asc' : 'desc');

            // Sort rows based on data type
            rows.sort((a, b) => {{
                const aCell = a.cells[columnIndex];
                const bCell = b.cells[columnIndex];
                let aValue = aCell.textContent.trim();
                let bValue = bCell.textContent.trim();

                // Handle placeholder values
                if (aValue === '-' || aValue === 'Loading...') aValue = ascending ? 'zzz' : '';
                if (bValue === '-' || bValue === 'Loading...') bValue = ascending ? 'zzz' : '';

                let comparison = 0;

                switch (dataType) {{
                    case 'number':
                    case 'currency':
                        // Remove $ and convert to number
                        const aNum = parseFloat(aValue.replace(/[$,]/g, '')) || 0;
                        const bNum = parseFloat(bValue.replace(/[$,]/g, '')) || 0;
                        comparison = aNum - bNum;
                        break;

                    case 'percent':
                        // Remove % and convert to number
                        const aPercent = parseFloat(aValue.replace('%', '')) || 0;
                        const bPercent = parseFloat(bValue.replace('%', '')) || 0;
                        comparison = aPercent - bPercent;
                        break;

                    case 'text':
                    default:
                        comparison = aValue.localeCompare(bValue);
                        break;
                }}

                return ascending ? comparison : -comparison;
            }});

            // Clear tbody and re-append sorted rows
            tbody.innerHTML = '';
            rows.forEach(row => tbody.appendChild(row));
        }}

        // Auto-refresh control
        let autoRefreshInterval = null;
        let autoRefreshActive = true;

        function startAutoRefresh() {{
            if (autoRefreshInterval) clearInterval(autoRefreshInterval);
            autoRefreshInterval = setInterval(() => {{
                window.location.reload();
            }}, 10000); // 10 seconds
        }}

        function stopAutoRefresh() {{
            if (autoRefreshInterval) {{
                clearInterval(autoRefreshInterval);
                autoRefreshInterval = null;
            }}
        }}

        function toggleAutoRefresh() {{
            const btn = document.getElementById('autoRefreshBtn');
            const status = document.getElementById('refreshStatus');

            if (autoRefreshActive) {{
                // Pause
                stopAutoRefresh();
                btn.innerHTML = '▶️ Play';
                status.textContent = 'Paused';
                status.style.color = '#e74c3c';
                autoRefreshActive = false;
            }} else {{
                // Play
                startAutoRefresh();
                btn.innerHTML = '⏸️ Pause';
                status.textContent = 'Active (10s)';
                status.style.color = '#27ae60';
                autoRefreshActive = true;
            }}
        }}

        // Restore sort state from localStorage
        function restoreSortState() {{
            const savedColumn = localStorage.getItem('dashboardSortColumn');
            const savedDirection = localStorage.getItem('dashboardSortDirection');

            if (savedColumn !== null) {{
                const columnIndex = parseInt(savedColumn);
                const headers = document.querySelectorAll('th.sortable');

                // Get data type from onclick attribute
                const onclickAttr = headers[columnIndex]?.getAttribute('onclick');
                if (onclickAttr) {{
                    const match = onclickAttr.match(/sortTable\\(\\d+,\\s*'([^']+)'\\)/);
                    if (match) {{
                        const dataType = match[1];

                        // Apply saved direction to header first
                        if (savedDirection === 'desc') {{
                            headers[columnIndex].classList.add('asc'); // Add asc so sortTable will flip to desc
                        }}

                        // Sort the table
                        sortTable(columnIndex, dataType);
                    }}
                }}
            }}
        }}

        // Start auto-refresh by default
        startAutoRefresh();

        // Restore sort state after page loads
        restoreSortState();
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
        tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "JNJ", "JPM", "PG", "KO"]

    dashboard = ValuationDashboard()
    dashboard.update_dashboard(tickers)

    return str(dashboard.html_file.absolute())


if __name__ == "__main__":
    # Example usage
    html_path = create_dashboard()
    print(f"Dashboard created: {html_path}")
    print("Open in browser to view live updates!")
