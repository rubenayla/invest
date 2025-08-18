from typing import List, Dict, Any
import logging
from ..config.schema import AnalysisConfig
from ..data.yahoo import get_universe_data, get_sp500_sample
from ..screening.quality import screen_quality
from ..screening.value import screen_value
from ..screening.growth import screen_growth
from ..screening.risk import screen_risk, apply_cyclical_adjustments
from ..dcf import calculate_dcf
# from ..rim import RIMModel  # Import when available

# Set up logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


class AnalysisPipeline:
    """Systematic investment analysis pipeline."""
    
    def __init__(self, config: AnalysisConfig):
        self.config = config
        self.results = {}
        
    def run_analysis(self) -> Dict[str, Any]:
        """Execute the complete analysis pipeline."""
        logger.info(f"Starting analysis: {self.config.name}")
        
        # Step 1: Get stock universe
        logger.info("Step 1: Building stock universe...")
        stocks_data = self._get_universe()
        logger.info(f"Universe contains {len(stocks_data)} stocks")
        
        if not stocks_data:
            logger.error("No stocks found in universe")
            return {"error": "No stocks found in universe"}
        
        # Step 2: Apply cyclical adjustments if needed
        if self.config.risk.cyclical_adjustment:
            logger.info("Applying cyclical adjustments...")
            stocks_data = apply_cyclical_adjustments(stocks_data, self.config.risk)
        
        # Step 3: Quality screening
        logger.info("Step 2: Quality assessment...")
        quality_results = screen_quality(stocks_data, self.config.quality)
        
        # Step 4: Value screening
        logger.info("Step 3: Value assessment...")
        value_results = screen_value(stocks_data, self.config.value)
        
        # Step 5: Growth screening
        logger.info("Step 4: Growth assessment...")
        growth_results = screen_growth(stocks_data, self.config.growth)
        
        # Step 6: Risk screening
        logger.info("Step 5: Risk assessment...")
        risk_results = screen_risk(stocks_data, self.config.risk)
        
        # Step 7: Combine results
        logger.info("Step 6: Combining screening results...")
        combined_results = self._combine_screening_results(
            stocks_data, quality_results, value_results, growth_results, risk_results
        )
        
        # Step 8: Apply filters and ranking
        logger.info("Step 7: Filtering and ranking...")
        filtered_results = self._apply_filters(combined_results)
        ranked_results = self._rank_results(combined_results)  # Rank ALL results, not just filtered
        
        # Step 9: Run valuation models on top candidates
        logger.info("Step 8: Running valuation models...")
        final_results = self._run_valuations(ranked_results[:self.config.max_results])
        
        # Step 10: Generate summary
        summary = self._generate_summary(final_results)
        
        # Include all analyzed stocks in results
        self.results = {
            'config': self.config.dict(),
            'summary': summary,
            'stocks': final_results,
            'all_stocks': combined_results,  # Include ALL analyzed stocks
            'total_universe': len(stocks_data),
            'passed_screening': len(filtered_results),
            'final_results': len(final_results)
        }
        
        logger.info(f"Analysis complete: {len(final_results)} stocks selected from {len(combined_results)} analyzed")
        return self.results
    
    def _get_universe(self) -> List[Dict]:
        """Build the stock universe based on configuration."""
        universe_config = self.config.universe
        
        if universe_config.custom_tickers:
            tickers = universe_config.custom_tickers
        elif hasattr(universe_config, 'pre_screening_universe') and universe_config.pre_screening_universe == "sp500":
            from ..data.yahoo import get_sp500_tickers
            tickers = get_sp500_tickers()
        elif universe_config.region == "US":
            from ..data.yahoo import get_sp500_sample
            tickers = get_sp500_sample()
        else:
            # For non-US, use a smaller sample for now
            tickers = ['ASML', 'SAP', 'NESN.SW'] if universe_config.region == "EU" else ['TSM']
        
        # Optimization: If we need top N by market cap, pre-filter tickers first
        if hasattr(universe_config, 'top_n_by_market_cap') and universe_config.top_n_by_market_cap:
            logger.info(f"Pre-filtering to top {universe_config.top_n_by_market_cap} stocks by market cap...")
            
            # Get basic market cap data for sorting (faster than full data)
            # Limit to 150 tickers max to avoid timeout (150 * 0.7s = ~105s < 2min timeout)
            max_fetch = min(len(tickers), max(150, universe_config.top_n_by_market_cap * 1.5))
            logger.info(f"Fetching market cap data for top {max_fetch} tickers...")
            
            ticker_market_caps = []
            for i, ticker in enumerate(tickers[:max_fetch]):
                try:
                    import yfinance as yf
                    stock = yf.Ticker(ticker)
                    info = stock.info
                    market_cap = info.get('marketCap', 0)
                    if market_cap and market_cap > 0:
                        ticker_market_caps.append((ticker, market_cap))
                    
                    # Log progress every 25 tickers
                    if (i + 1) % 25 == 0:
                        logger.info(f"Processed {i + 1}/{max_fetch} tickers for market cap...")
                        
                except Exception as e:
                    logger.warning(f"Failed to get market cap for {ticker}: {e}")
                    continue
            
            # Sort by market cap and take top N
            ticker_market_caps.sort(key=lambda x: x[1], reverse=True)
            tickers = [ticker for ticker, _ in ticker_market_caps[:universe_config.top_n_by_market_cap]]
            logger.info(f"Pre-filtered to {len(tickers)} tickers by market cap")
        
        # Get full stock data for filtered tickers
        stocks_data = []
        logger.info(f"Fetching full stock data for {len(tickers)} tickers...")
        for i, ticker in enumerate(tickers):
            try:
                from ..data.yahoo import get_stock_data
                stock_data = get_stock_data(ticker)
                if stock_data:
                    # Check filters and add filter status
                    stock_data['passes_universe_filters'] = self._passes_universe_filters(stock_data, universe_config)
                    stocks_data.append(stock_data)
                
                # Log progress every 20 tickers
                if (i + 1) % 20 == 0:
                    passed_count = sum(1 for s in stocks_data if s['passes_universe_filters'])
                    logger.info(f"Processed {i + 1}/{len(tickers)} tickers for full data... ({passed_count} passed filters)")
                    
            except Exception as e:
                logger.warning(f"Failed to get data for {ticker}: {e}")
                continue

        return stocks_data
    
    def _passes_universe_filters(self, stock_data: Dict, universe_config) -> bool:
        """Check if stock passes universe-level filters."""
        market_cap = stock_data.get('market_cap', 0)
        sector = stock_data.get('sector', '')
        
        # Market cap filters
        passes_filters = True
        filter_reasons = []
        
        # Market cap filter
        if universe_config.min_market_cap and (not market_cap or market_cap < universe_config.min_market_cap * 1e6):
            passes_filters = False
            filter_reasons.append(f"Market cap too low: {market_cap/1e6:.2f}M")
        
        if universe_config.max_market_cap and market_cap and market_cap > universe_config.max_market_cap * 1e6:
            passes_filters = False
            filter_reasons.append(f"Market cap too high: {market_cap/1e6:.2f}M")
        
        # Sector filters
        if universe_config.exclude_sectors and sector in universe_config.exclude_sectors:
            passes_filters = False
            filter_reasons.append(f"Excluded sector: {sector}")
        
        if universe_config.sectors and sector not in universe_config.sectors:
            passes_filters = False
            filter_reasons.append(f"Not in allowed sectors: {sector}")
        
        # Detailed logging
        if not passes_filters:
            logger.info(f"Filtering out {stock_data.get('ticker', 'Unknown')}: {', '.join(filter_reasons)}")
        
        return passes_filters
    
    def _combine_screening_results(self, stocks_data: List[Dict], quality_results: List[Dict],
                                  value_results: List[Dict], growth_results: List[Dict],
                                  risk_results: List[Dict]) -> List[Dict]:
        """Combine all screening results into unified records."""
        combined = []
        
        # Create lookup dictionaries
        quality_lookup = {r['ticker']: r for r in quality_results}
        value_lookup = {r['ticker']: r for r in value_results}
        growth_lookup = {r['ticker']: r for r in growth_results}
        risk_lookup = {r['ticker']: r for r in risk_results}
        
        for stock in stocks_data:
            ticker = stock.get('ticker', '')
            
            combined_record = {
                'ticker': ticker,
                'basic_data': stock,
                'quality': quality_lookup.get(ticker, {}),
                'value': value_lookup.get(ticker, {}),
                'growth': growth_lookup.get(ticker, {}),
                'risk': risk_lookup.get(ticker, {})
            }
            
            # Calculate composite score
            quality_score = quality_lookup.get(ticker, {}).get('quality_score', 0)
            value_score = value_lookup.get(ticker, {}).get('value_score', 0)
            growth_score = growth_lookup.get(ticker, {}).get('growth_score', 0)
            risk_score = risk_lookup.get(ticker, {}).get('overall_risk_score', 100)  # Higher risk = lower score
            
            # Composite score (weighted average, risk is inverted)
            composite_score = (
                quality_score * 0.3 +
                value_score * 0.3 +
                growth_score * 0.25 +
                (100 - risk_score) * 0.15  # Invert risk score
            )
            
            combined_record['composite_score'] = composite_score
            combined_record['scores'] = {
                'quality': quality_score,
                'value': value_score,
                'growth': growth_score,
                'risk': risk_score,
                'composite': composite_score
            }
            
            combined.append(combined_record)
        
        return combined
    
    def _apply_filters(self, combined_results: List[Dict]) -> List[Dict]:
        """Apply minimum score filters and mark pass/fail status."""
        filtered = []
        
        # Apply minimum thresholds (configurable)
        min_quality = 40
        min_value = 30
        min_growth = 20
        max_risk = 80
        min_composite = 50
        
        for result in combined_results:
            scores = result.get('scores', {})
            
            # Check if passes filters
            passes_filters = (
                scores.get('quality', 0) >= min_quality and
                scores.get('value', 0) >= min_value and
                scores.get('growth', 0) >= min_growth and
                scores.get('risk', 100) <= max_risk and
                scores.get('composite', 0) >= min_composite
            )
            
            # Add pass/fail flag to result
            result['passes_filters'] = passes_filters
            
            if passes_filters:
                filtered.append(result)
        
        return filtered
    
    def _rank_results(self, filtered_results: List[Dict]) -> List[Dict]:
        """Rank results based on configuration."""
        sort_key = self.config.sort_by
        
        if sort_key == 'composite_score':
            return sorted(filtered_results, key=lambda x: x.get('composite_score', 0), reverse=True)
        elif sort_key == 'quality_score':
            return sorted(filtered_results, key=lambda x: x.get('scores', {}).get('quality', 0), reverse=True)
        elif sort_key == 'value_score':
            return sorted(filtered_results, key=lambda x: x.get('scores', {}).get('value', 0), reverse=True)
        elif sort_key == 'growth_score':
            return sorted(filtered_results, key=lambda x: x.get('scores', {}).get('growth', 0), reverse=True)
        else:
            # Default to composite score
            return sorted(filtered_results, key=lambda x: x.get('composite_score', 0), reverse=True)
    
    def _run_valuations(self, top_results: List[Dict]) -> List[Dict]:
        """Run valuation models on top candidates."""
        for result in top_results:
            ticker = result['ticker']
            stock_data = result['basic_data']
            
            try:
                valuations = {}
                
                # Run DCF if configured
                if 'dcf' in self.config.valuation.models:
                    dcf_result = self._run_dcf_valuation(stock_data)
                    if dcf_result:
                        valuations['dcf'] = dcf_result
                
                # Run RIM if configured
                if 'rim' in self.config.valuation.models:
                    rim_result = self._run_rim_valuation(stock_data)
                    if rim_result:
                        valuations['rim'] = rim_result
                
                result['valuations'] = valuations
                
            except Exception as e:
                logger.warning(f"Valuation failed for {ticker}: {e}")
                result['valuations'] = {}
        
        return top_results
    
    def _run_dcf_valuation(self, stock_data: Dict) -> Dict:
        """Run DCF valuation using the existing DCF function."""
        try:
            ticker = stock_data.get('ticker', '')
            if not ticker:
                return None
            
            # Use the existing DCF function
            dcf_result = calculate_dcf(ticker, verbose=False)
            
            return {
                'fair_value': dcf_result.get('fair_value_per_share', 0),
                'current_price': dcf_result.get('current_price', 0),
                'upside_downside': dcf_result.get('margin_of_safety', 0),
                'model': 'DCF',
                'confidence': 'medium',
                'enterprise_value': dcf_result.get('enterprise_value', 0)
            }
        except Exception as e:
            logger.warning(f"DCF valuation failed for {stock_data.get('ticker', 'unknown')}: {e}")
            return None
    
    def _run_rim_valuation(self, stock_data: Dict) -> Dict:
        """Run RIM valuation (placeholder implementation)."""
        # This would integrate with your existing RIM model
        current_price = stock_data.get('current_price', 0)
        book_value = stock_data.get('price_to_book', 0)
        
        if not current_price or not book_value:
            return None
            
        # Very rough RIM approximation
        fair_value = current_price * 0.95  # Placeholder logic
        
        return {
            'fair_value': fair_value,
            'current_price': current_price,
            'upside_downside': (fair_value / current_price - 1) if current_price > 0 else 0,
            'model': 'RIM',
            'confidence': 'medium'
        }
    
    def _generate_summary(self, final_results: List[Dict]) -> Dict:
        """Generate analysis summary."""
        if not final_results:
            return {
                'top_picks': [],
                'average_scores': {},
                'sector_breakdown': {},
                'key_insights': ["No stocks passed the screening criteria"]
            }
        
        # Calculate average scores
        avg_quality = sum(r.get('scores', {}).get('quality', 0) for r in final_results) / len(final_results)
        avg_value = sum(r.get('scores', {}).get('value', 0) for r in final_results) / len(final_results)
        avg_growth = sum(r.get('scores', {}).get('growth', 0) for r in final_results) / len(final_results)
        avg_risk = sum(r.get('scores', {}).get('risk', 0) for r in final_results) / len(final_results)
        
        # Sector breakdown
        sectors = {}
        for result in final_results:
            sector = result.get('basic_data', {}).get('sector', 'Unknown')
            sectors[sector] = sectors.get(sector, 0) + 1
        
        # Count total and filtered stocks
        if 'total_universe' in self.results:
            total_stocks = self.results['total_universe']
            filtered_out_count = sum(1 for stock in stocks_data if not stock.get('passes_universe_filters', False))
            # Add filter-out reasons to key insights
        
        # Top picks (top 5)
        top_picks = [
            {
                'ticker': r['ticker'],
                'composite_score': r.get('composite_score', 0),
                'sector': r.get('basic_data', {}).get('sector', 'Unknown')
            }
            for r in final_results[:5]
        ]
        
        return {
            'top_picks': top_picks,
            'average_scores': {
                'quality': round(avg_quality, 1),
                'value': round(avg_value, 1),
                'growth': round(avg_growth, 1),
                'risk': round(avg_risk, 1)
            },
            'sector_breakdown': sectors,
            'key_insights': [
                f"Found {len(final_results)} stocks meeting criteria",
                f"Average composite score: {sum(r.get('composite_score', 0) for r in final_results) / len(final_results):.1f}",
                f"Most represented sector: {max(sectors.items(), key=lambda x: x[1])[0] if sectors else 'None'}"
            ]
        }