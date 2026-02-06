"""
Scoring Engine for Opportunity Scanner

Uses continuous scoring functions (sigmoid-like curves) instead of pass/fail checklists.
A stock with P/E=19 isn't discarded - it just scores slightly lower than P/E=17.
"""

import math
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List

from ..data.stock_data_reader import StockDataReader
from ..valuation.db_utils import get_db_connection, get_latest_predictions


@dataclass
class OpportunityScore:
    """Complete opportunity score for a stock."""
    ticker: str
    company_name: str
    opportunity_score: float  # 0-100 composite
    quality_score: float      # 0-100
    value_score: float        # 0-100
    growth_score: float       # 0-100
    risk_score: float         # 0-100 (higher = less risky)
    catalyst_score: float     # 0-100

    # Key metrics for display
    current_price: float = 0.0
    dcf_fair_value: Optional[float] = None
    rim_fair_value: Optional[float] = None
    ensemble_fair_value: Optional[float] = None

    # Supporting data
    key_metrics: Dict[str, Any] = field(default_factory=dict)
    component_details: Dict[str, Any] = field(default_factory=dict)


class ScoringEngine:
    """
    Continuous scoring engine for stock opportunities.

    Core principle: Use smooth curves instead of binary thresholds.
    """

    # Default component weights (sum to 1.0)
    DEFAULT_WEIGHTS = {
        'quality': 0.25,
        'value': 0.30,
        'growth': 0.20,
        'risk': 0.10,
        'catalyst': 0.15,
    }

    def __init__(self, weights: Optional[Dict[str, float]] = None):
        """
        Initialize scoring engine with optional custom weights.

        Parameters
        ----------
        weights : dict, optional
            Custom weights for each component. Must sum to 1.0.
        """
        self.weights = weights or self.DEFAULT_WEIGHTS
        self._validate_weights()
        self.reader = StockDataReader()

    def _validate_weights(self) -> None:
        """Ensure weights sum to 1.0."""
        total = sum(self.weights.values())
        if not 0.99 <= total <= 1.01:
            raise ValueError(f"Weights must sum to 1.0, got {total}")

    @staticmethod
    def normalize(
        value: float,
        min_val: float,
        target: float,
        max_val: float,
        inverse: bool = False
    ) -> float:
        """
        Normalize a value to 0-100 using a smooth sigmoid-like curve.

        Parameters
        ----------
        value : float
            The raw value to normalize
        min_val : float
            Below this: 0-20 points
        target : float
            At target: ~70 points (good)
        max_val : float
            At max: ~100 points (exceptional)
        inverse : bool
            If True, lower values are better (e.g., P/E ratio)

        Returns
        -------
        float
            Score from 0 to 100
        """
        if value is None or math.isnan(value):
            return 50.0  # Neutral score for missing data

        if inverse:
            # Flip the scale for metrics where lower is better
            value = min_val + max_val - value

        if value <= min_val:
            # Below minimum: 0-20 points (linear)
            return max(0, 20 * (value / min_val)) if min_val > 0 else 0

        if value >= max_val:
            # Above maximum: cap at 100
            return 100.0

        if value <= target:
            # Between min and target: 20-70 points (smooth curve)
            progress = (value - min_val) / (target - min_val)
            # Use smoothstep for smoother transition
            smooth = progress * progress * (3 - 2 * progress)
            return 20 + smooth * 50

        # Between target and max: 70-100 points (smooth curve)
        progress = (value - target) / (max_val - target)
        smooth = progress * progress * (3 - 2 * progress)
        return 70 + smooth * 30

    def score_quality(self, data: Dict[str, Any]) -> tuple[float, Dict[str, Any]]:
        """
        Score business quality metrics.

        Sources: ROE, ROIC, current ratio, debt/equity, margins
        """
        details = {}
        scores = []

        # ROE: 5% min, 15% target, 30% exceptional
        roe = data.get('financials', {}).get('returnOnEquity')
        if roe is not None:
            roe_score = self.normalize(roe * 100, 5, 15, 30)
            scores.append(roe_score)
            details['roe'] = {'value': roe * 100, 'score': roe_score}

        # Current Ratio: 0.8 min, 1.5 target, 3.0 max
        current_ratio = data.get('financials', {}).get('currentRatio')
        if current_ratio is not None:
            cr_score = self.normalize(current_ratio, 0.8, 1.5, 3.0)
            scores.append(cr_score)
            details['current_ratio'] = {'value': current_ratio, 'score': cr_score}

        # Debt/Equity: 2.0 max, 0.5 target, 0 ideal (inverse)
        debt_equity = data.get('financials', {}).get('debtToEquity')
        if debt_equity is not None:
            # Convert from percentage if needed
            de = debt_equity / 100 if debt_equity > 5 else debt_equity
            de_score = self.normalize(de, 0, 0.5, 2.0, inverse=True)
            scores.append(de_score)
            details['debt_equity'] = {'value': de, 'score': de_score}

        # Operating Margins: 0% min, 15% target, 40% exceptional
        op_margin = data.get('financials', {}).get('operatingMargins')
        if op_margin is not None:
            om_score = self.normalize(op_margin * 100, 0, 15, 40)
            scores.append(om_score)
            details['operating_margin'] = {'value': op_margin * 100, 'score': om_score}

        # Profit Margins: 0% min, 10% target, 30% exceptional
        profit_margin = data.get('financials', {}).get('profitMargins')
        if profit_margin is not None:
            pm_score = self.normalize(profit_margin * 100, 0, 10, 30)
            scores.append(pm_score)
            details['profit_margin'] = {'value': profit_margin * 100, 'score': pm_score}

        final_score = sum(scores) / len(scores) if scores else 50.0
        return final_score, details

    def score_value(
        self,
        data: Dict[str, Any],
        valuations: Dict[str, Any]
    ) -> tuple[float, Dict[str, Any]]:
        """
        Score valuation attractiveness.

        Sources: P/E, P/B, EV/EBITDA + DCF/RIM/Ensemble upside
        """
        details = {}
        scores = []

        # P/E Ratio: 30 max, 15 target, 8 exceptional (inverse - lower is better)
        pe = data.get('financials', {}).get('trailingPE')
        if pe is not None and pe > 0:
            pe_score = self.normalize(pe, 8, 15, 30, inverse=True)
            scores.append(pe_score)
            details['pe'] = {'value': pe, 'score': pe_score}

        # P/B Ratio: 5 max, 2.5 target, 1 exceptional (inverse)
        pb = data.get('financials', {}).get('priceToBook')
        if pb is not None and pb > 0:
            pb_score = self.normalize(pb, 1, 2.5, 5, inverse=True)
            scores.append(pb_score)
            details['pb'] = {'value': pb, 'score': pb_score}

        # Model upside scoring (heavier weight)
        upside_scores = []

        for model in ['dcf', 'dcf_enhanced', 'rim', 'ensemble']:
            if model in valuations and valuations[model].get('suitable'):
                upside = valuations[model].get('upside_pct', 0)
                # Upside: -20% min, 20% target, 50% exceptional
                upside_score = self.normalize(upside, -20, 20, 50)
                upside_scores.append(upside_score)
                details[f'{model}_upside'] = {'value': upside, 'score': upside_score}

        if upside_scores:
            # Weight model upside more heavily (50% of value score)
            avg_upside = sum(upside_scores) / len(upside_scores)
            ratio_avg = sum(scores) / len(scores) if scores else 50.0
            final_score = ratio_avg * 0.5 + avg_upside * 0.5
        else:
            final_score = sum(scores) / len(scores) if scores else 50.0

        return final_score, details

    def score_growth(self, data: Dict[str, Any]) -> tuple[float, Dict[str, Any]]:
        """
        Score growth potential.

        Sources: Revenue/earnings CAGR, FCF growth, trends
        """
        details = {}
        scores = []

        # Revenue Growth: -5% min, 10% target, 30% exceptional
        rev_growth = data.get('financials', {}).get('revenueGrowth')
        if rev_growth is not None:
            rg_score = self.normalize(rev_growth * 100, -5, 10, 30)
            scores.append(rg_score)
            details['revenue_growth'] = {'value': rev_growth * 100, 'score': rg_score}

        # Earnings Growth: -10% min, 15% target, 40% exceptional
        earn_growth = data.get('financials', {}).get('earningsGrowth')
        if earn_growth is not None:
            eg_score = self.normalize(earn_growth * 100, -10, 15, 40)
            scores.append(eg_score)
            details['earnings_growth'] = {'value': earn_growth * 100, 'score': eg_score}

        # Price trend 30d as growth momentum proxy: -10% min, 5% target, 15% max
        price_trend = data.get('price_data', {}).get('price_trend_30d')
        if price_trend is not None:
            pt_score = self.normalize(price_trend * 100, -10, 5, 15)
            scores.append(pt_score * 0.5)  # Lower weight for short-term trend
            details['price_trend_30d'] = {'value': price_trend * 100, 'score': pt_score}

        final_score = sum(scores) / len(scores) if scores else 50.0
        return final_score, details

    def score_risk(self, data: Dict[str, Any]) -> tuple[float, Dict[str, Any]]:
        """
        Score risk level (higher score = LOWER risk = better).

        Sources: Beta, volatility, financial leverage
        """
        details = {}
        scores = []

        # Debt/Equity as risk indicator: 2 max (risky), 0.5 target, 0 ideal
        debt_equity = data.get('financials', {}).get('debtToEquity')
        if debt_equity is not None:
            de = debt_equity / 100 if debt_equity > 5 else debt_equity
            # Inverse: lower debt = higher score (less risky)
            de_risk_score = self.normalize(de, 0, 0.5, 2.0, inverse=True)
            scores.append(de_risk_score)
            details['debt_equity_risk'] = {'value': de, 'score': de_risk_score}

        # Current ratio as liquidity safety: 0.5 min (risky), 1.5 target, 3.0 safe
        current_ratio = data.get('financials', {}).get('currentRatio')
        if current_ratio is not None:
            cr_score = self.normalize(current_ratio, 0.5, 1.5, 3.0)
            scores.append(cr_score)
            details['liquidity'] = {'value': current_ratio, 'score': cr_score}

        # Sector-based risk adjustment
        sector = data.get('info', {}).get('sector', '')
        sector_risk = {
            'Consumer Staples': 80,
            'Utilities': 75,
            'Healthcare': 70,
            'Communication Services': 60,
            'Industrials': 55,
            'Consumer Discretionary': 50,
            'Technology': 50,
            'Materials': 45,
            'Financials': 45,
            'Energy': 40,
            'Real Estate': 55,
        }
        sector_score = sector_risk.get(sector, 50)
        scores.append(sector_score)
        details['sector_stability'] = {'value': sector, 'score': sector_score}

        final_score = sum(scores) / len(scores) if scores else 50.0
        return final_score, details

    def score_catalyst(self, data: Dict[str, Any]) -> tuple[float, Dict[str, Any]]:
        """
        Score timing/momentum signals.

        Sources: 52w-high discount, RSI proxy, momentum signals
        """
        details = {}
        scores = []

        # 52-week high discount: more discount = better buying opportunity
        current_price = data.get('info', {}).get('currentPrice') or data.get('price_data', {}).get('current_price')
        price_52w_high = data.get('price_data', {}).get('price_52w_high')

        if current_price and price_52w_high and price_52w_high > 0:
            discount = (price_52w_high - current_price) / price_52w_high * 100
            # Discount: 0% min (at high), 15% target, 40% exceptional
            discount_score = self.normalize(discount, 0, 15, 40)
            scores.append(discount_score)
            details['52w_discount'] = {'value': discount, 'score': discount_score}

        # 52-week low buffer: distance from 52w low (safety)
        price_52w_low = data.get('price_data', {}).get('price_52w_low')
        if current_price and price_52w_low and price_52w_low > 0:
            buffer = (current_price - price_52w_low) / price_52w_low * 100
            # Buffer: 0% min, 30% target, 80% max (not catching falling knife)
            buffer_score = self.normalize(buffer, 0, 30, 80)
            scores.append(buffer_score * 0.5)  # Lower weight
            details['52w_low_buffer'] = {'value': buffer, 'score': buffer_score}

        # 30-day trend as momentum proxy
        price_trend = data.get('price_data', {}).get('price_trend_30d')
        if price_trend is not None:
            # Slight negative to neutral is ideal for buying
            # -5% to +5% is target zone
            trend_pct = price_trend * 100
            if -5 <= trend_pct <= 5:
                trend_score = 70  # Consolidation = good
            elif trend_pct < -15:
                trend_score = 40  # Falling knife risk
            elif trend_pct > 15:
                trend_score = 50  # Already moved
            else:
                trend_score = 60  # Moderate movement
            scores.append(trend_score)
            details['momentum'] = {'value': trend_pct, 'score': trend_score}

        final_score = sum(scores) / len(scores) if scores else 50.0
        return final_score, details

    def score_stock(self, ticker: str) -> Optional[OpportunityScore]:
        """
        Calculate complete opportunity score for a stock.

        Parameters
        ----------
        ticker : str
            Stock ticker symbol

        Returns
        -------
        OpportunityScore or None if data not available
        """
        # Load stock data
        data = self.reader.get_stock_data(ticker)
        if not data:
            return None

        # Get valuation predictions
        conn = get_db_connection()
        valuations = get_latest_predictions(conn, ticker)
        conn.close()

        # Calculate component scores
        quality_score, quality_details = self.score_quality(data)
        value_score, value_details = self.score_value(data, valuations)
        growth_score, growth_details = self.score_growth(data)
        risk_score, risk_details = self.score_risk(data)
        catalyst_score, catalyst_details = self.score_catalyst(data)

        # Calculate weighted composite score
        opportunity_score = (
            quality_score * self.weights['quality'] +
            value_score * self.weights['value'] +
            growth_score * self.weights['growth'] +
            risk_score * self.weights['risk'] +
            catalyst_score * self.weights['catalyst']
        )

        # Extract key metrics for display
        info = data.get('info', {})
        financials = data.get('financials', {})

        key_metrics = {
            'pe': financials.get('trailingPE'),
            'pb': financials.get('priceToBook'),
            'roe': (financials.get('returnOnEquity') or 0) * 100,
            'debt_equity': financials.get('debtToEquity'),
            'current_ratio': financials.get('currentRatio'),
            'revenue_growth': (financials.get('revenueGrowth') or 0) * 100,
            'earnings_growth': (financials.get('earningsGrowth') or 0) * 100,
            'sector': info.get('sector'),
        }

        # Get fair values from valuations
        dcf_fv = None
        rim_fv = None
        ensemble_fv = None

        for model, pred in valuations.items():
            if pred.get('suitable'):
                if 'dcf' in model.lower() and dcf_fv is None:
                    dcf_fv = pred.get('fair_value')
                elif 'rim' in model.lower() and rim_fv is None:
                    rim_fv = pred.get('fair_value')
                elif 'ensemble' in model.lower():
                    ensemble_fv = pred.get('fair_value')

        return OpportunityScore(
            ticker=ticker,
            company_name=info.get('longName') or info.get('shortName') or ticker,
            opportunity_score=round(opportunity_score, 1),
            quality_score=round(quality_score, 1),
            value_score=round(value_score, 1),
            growth_score=round(growth_score, 1),
            risk_score=round(risk_score, 1),
            catalyst_score=round(catalyst_score, 1),
            current_price=info.get('currentPrice') or data.get('price_data', {}).get('current_price') or 0,
            dcf_fair_value=dcf_fv,
            rim_fair_value=rim_fv,
            ensemble_fair_value=ensemble_fv,
            key_metrics=key_metrics,
            component_details={
                'quality': quality_details,
                'value': value_details,
                'growth': growth_details,
                'risk': risk_details,
                'catalyst': catalyst_details,
            }
        )

    def score_universe(self, tickers: List[str]) -> List[OpportunityScore]:
        """
        Score all stocks in a universe.

        Parameters
        ----------
        tickers : list
            List of ticker symbols

        Returns
        -------
        list
            Sorted list of OpportunityScore objects (highest first)
        """
        scores = []
        for ticker in tickers:
            score = self.score_stock(ticker)
            if score:
                scores.append(score)

        # Sort by opportunity score (highest first)
        scores.sort(key=lambda x: x.opportunity_score, reverse=True)
        return scores
