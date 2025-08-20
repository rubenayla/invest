"""
DCF Model implementations consolidated under the unified structure.

This module contains all DCF-based valuation models:
- Standard DCF
- Enhanced DCF 
- Multi-Stage DCF

All inherit from the base ValuationModel class for consistency.
"""

import numpy as np
import yfinance as yf
from typing import Dict, Any, List, Optional
from datetime import datetime

from .base import ValuationModel, ValuationResult
from ..config.constants import VALUATION_DEFAULTS
from ..exceptions import InsufficientDataError, ModelNotSuitableError


class DCFModel(ValuationModel):
    """Standard Discounted Cash Flow valuation model."""
    
    def __init__(self):
        super().__init__('dcf')
        self.projection_years = VALUATION_DEFAULTS.DCF_PROJECTION_YEARS
    
    def is_suitable(self, ticker: str, data: Dict[str, Any]) -> bool:
        """DCF is suitable for most companies with positive free cash flow."""
        try:
            # Check if we have basic financial data
            cashflow = data.get('cashflow')
            if cashflow is None or cashflow.empty:
                return False
            
            # Check for free cash flow data
            fcf = self._get_free_cash_flow(data)
            if fcf is None or fcf <= 0:
                return False
            
            return True
        except:
            return False
    
    def _validate_inputs(self, ticker: str, data: Dict[str, Any]) -> None:
        """Validate required DCF inputs."""
        required_fields = ['cashflow', 'balance_sheet', 'info']
        
        for field in required_fields:
            if field not in data or data[field] is None:
                raise InsufficientDataError(f'Missing {field} data for DCF valuation')
        
        # Validate we can calculate free cash flow
        fcf = self._get_free_cash_flow(data)
        if fcf is None or fcf <= 0:
            raise InsufficientDataError(f'Cannot calculate positive free cash flow for {ticker}')
    
    def _calculate_valuation(self, ticker: str, data: Dict[str, Any]) -> ValuationResult:
        """Perform DCF calculation."""
        # Extract key inputs
        fcf = self._get_free_cash_flow(data)
        wacc = self._estimate_wacc(data)
        growth_rate = self._estimate_growth_rate(data)
        terminal_growth = VALUATION_DEFAULTS.TERMINAL_GROWTH_RATE
        
        # Project future cash flows
        projected_fcfs = self._project_cash_flows(fcf, growth_rate, self.projection_years)
        
        # Calculate terminal value
        terminal_fcf = projected_fcfs[-1] * (1 + terminal_growth)
        terminal_value = terminal_fcf / (wacc - terminal_growth)
        
        # Discount everything to present value
        pv_fcfs = [fcf / (1 + wacc)**i for i, fcf in enumerate(projected_fcfs, 1)]
        pv_terminal = terminal_value / (1 + wacc)**self.projection_years
        
        # Calculate enterprise value
        enterprise_value = sum(pv_fcfs) + pv_terminal
        
        # Convert to equity value
        equity_value = self._convert_to_equity_value(enterprise_value, data)
        shares_outstanding = self._get_shares_outstanding(data)
        fair_value_per_share = equity_value / shares_outstanding
        
        # Get current price and calculate margin of safety
        current_price = self._get_current_price(data)
        margin_of_safety = None
        if current_price and current_price > 0:
            margin_of_safety = (fair_value_per_share - current_price) / current_price
        
        # Create result
        result = ValuationResult(
            ticker=ticker,
            model=self.name,
            fair_value=fair_value_per_share,
            current_price=current_price,
            margin_of_safety=margin_of_safety,
            enterprise_value=enterprise_value
        )
        
        # Add detailed inputs/outputs
        result.inputs = {
            'free_cash_flow': fcf,
            'wacc': wacc,
            'growth_rate': growth_rate,
            'terminal_growth': terminal_growth,
            'projection_years': self.projection_years,
        }
        
        result.outputs = {
            'projected_fcfs': projected_fcfs,
            'pv_fcfs': pv_fcfs,
            'terminal_value': terminal_value,
            'pv_terminal': pv_terminal,
            'equity_value': equity_value,
            'shares_outstanding': shares_outstanding,
        }
        
        return result
    
    def _get_free_cash_flow(self, data: Dict[str, Any]) -> Optional[float]:
        """Calculate or extract free cash flow."""
        cashflow = data.get('cashflow')
        if cashflow is None or cashflow.empty:
            return None
        
        # Try to get operating cash flow and capex
        operating_cf = self._get_most_recent_value(
            cashflow.loc['Total Cash From Operating Activities'] if 'Total Cash From Operating Activities' in cashflow.index else None
        )
        
        capex = self._get_most_recent_value(
            cashflow.loc['Capital Expenditures'] if 'Capital Expenditures' in cashflow.index else None
        )
        
        if operating_cf is not None and capex is not None:
            # CapEx is typically negative, so we add it (which subtracts the absolute value)
            return operating_cf + capex
        
        # Fallback to free cash flow if available
        fcf = self._get_most_recent_value(
            cashflow.loc['Free Cash Flow'] if 'Free Cash Flow' in cashflow.index else None
        )
        
        return fcf
    
    def _estimate_wacc(self, data: Dict[str, Any]) -> float:
        """Estimate Weighted Average Cost of Capital."""
        # Simplified WACC estimation
        # In practice, this would be more sophisticated
        info = data.get('info', {})
        
        # Try to get beta and risk-free rate
        beta = self._safe_float(info.get('beta'), 1.0)
        
        # Use reasonable defaults
        risk_free_rate = VALUATION_DEFAULTS.RISK_FREE_RATE
        market_premium = VALUATION_DEFAULTS.EQUITY_RISK_PREMIUM
        
        cost_of_equity = risk_free_rate + beta * market_premium
        
        # For simplicity, assume all-equity financing
        # In practice, would calculate debt/equity ratios and cost of debt
        return cost_of_equity
    
    def _estimate_growth_rate(self, data: Dict[str, Any]) -> float:
        """Estimate revenue/earnings growth rate."""
        # Try to get analyst estimates or historical growth
        info = data.get('info', {})
        
        # Use analyst estimates if available
        earnings_growth = self._safe_float(info.get('earningsGrowth'))
        revenue_growth = self._safe_float(info.get('revenueGrowth'))
        
        if earnings_growth and earnings_growth > 0:
            return min(earnings_growth, VALUATION_DEFAULTS.MAX_GROWTH_RATE)
        elif revenue_growth and revenue_growth > 0:
            return min(revenue_growth, VALUATION_DEFAULTS.MAX_GROWTH_RATE)
        
        # Default to conservative growth
        return VALUATION_DEFAULTS.DEFAULT_GROWTH_RATE
    
    def _project_cash_flows(self, initial_fcf: float, growth_rate: float, years: int) -> List[float]:
        """Project future cash flows."""
        projected = []
        fcf = initial_fcf
        
        for year in range(years):
            fcf *= (1 + growth_rate)
            projected.append(fcf)
        
        return projected
    
    def _convert_to_equity_value(self, enterprise_value: float, data: Dict[str, Any]) -> float:
        """Convert enterprise value to equity value."""
        balance_sheet = data.get('balance_sheet')
        if balance_sheet is None or balance_sheet.empty:
            return enterprise_value  # Assume no net debt
        
        # Get cash and debt
        cash = self._get_most_recent_value(
            balance_sheet.loc['Cash And Cash Equivalents'] if 'Cash And Cash Equivalents' in balance_sheet.index else None,
            default=0
        )
        
        total_debt = self._get_most_recent_value(
            balance_sheet.loc['Total Debt'] if 'Total Debt' in balance_sheet.index else None,
            default=0
        )
        
        return enterprise_value - total_debt + cash
    
    def _get_shares_outstanding(self, data: Dict[str, Any]) -> float:
        """Get shares outstanding."""
        info = data.get('info', {})
        shares = self._safe_float(info.get('sharesOutstanding'))
        
        if not shares or shares <= 0:
            shares = self._safe_float(info.get('impliedSharesOutstanding'))
        
        if not shares or shares <= 0:
            raise InsufficientDataError('Cannot determine shares outstanding')
        
        return shares
    
    def _get_current_price(self, data: Dict[str, Any]) -> Optional[float]:
        """Get current stock price."""
        info = data.get('info', {})
        return self._safe_float(info.get('currentPrice'))


class EnhancedDCFModel(DCFModel):
    """Enhanced DCF with normalized cash flows and better assumptions."""
    
    def __init__(self):
        super().__init__()
        self.name = 'dcf_enhanced'
    
    def _get_free_cash_flow(self, data: Dict[str, Any]) -> Optional[float]:
        """Get normalized free cash flow using multi-year average."""
        cashflow = data.get('cashflow')
        if cashflow is None or cashflow.empty:
            return None
        
        # Get multi-year operating cash flow and capex data
        operating_cf_key = 'Total Cash From Operating Activities'
        capex_key = 'Capital Expenditures'
        
        if operating_cf_key not in cashflow.index or capex_key not in cashflow.index:
            return super()._get_free_cash_flow(data)
        
        operating_cf_series = cashflow.loc[operating_cf_key].dropna()
        capex_series = cashflow.loc[capex_key].dropna()
        
        if len(operating_cf_series) < 2 or len(capex_series) < 2:
            return super()._get_free_cash_flow(data)
        
        # Calculate multi-year average (normalize for one-time events)
        avg_operating_cf = operating_cf_series.head(3).mean()  # Last 3 years
        avg_capex = capex_series.head(3).mean()  # Last 3 years
        
        return avg_operating_cf + avg_capex  # Capex is typically negative


class MultiStageDCFModel(DCFModel):
    """Multi-stage DCF with different growth phases."""
    
    def __init__(self):
        super().__init__()
        self.name = 'multi_stage_dcf'
        self.high_growth_years = 5
        self.moderate_growth_years = 5
    
    def _calculate_valuation(self, ticker: str, data: Dict[str, Any]) -> ValuationResult:
        """Multi-stage DCF calculation."""
        # Extract inputs
        fcf = self._get_free_cash_flow(data)
        wacc = self._estimate_wacc(data)
        
        # Multi-stage growth rates
        high_growth = self._estimate_growth_rate(data)
        moderate_growth = high_growth * 0.5  # Half the initial growth
        terminal_growth = VALUATION_DEFAULTS.TERMINAL_GROWTH_RATE
        
        # Project cash flows in stages
        high_growth_fcfs = self._project_cash_flows(fcf, high_growth, self.high_growth_years)
        
        # Start moderate growth from last high growth FCF
        moderate_growth_fcfs = self._project_cash_flows(
            high_growth_fcfs[-1], moderate_growth, self.moderate_growth_years
        )
        
        # Calculate terminal value
        terminal_fcf = moderate_growth_fcfs[-1] * (1 + terminal_growth)
        terminal_value = terminal_fcf / (wacc - terminal_growth)
        
        # Discount all cash flows
        total_years = self.high_growth_years + self.moderate_growth_years
        all_fcfs = high_growth_fcfs + moderate_growth_fcfs
        
        pv_fcfs = [fcf / (1 + wacc)**i for i, fcf in enumerate(all_fcfs, 1)]
        pv_terminal = terminal_value / (1 + wacc)**total_years
        
        # Calculate enterprise value
        enterprise_value = sum(pv_fcfs) + pv_terminal
        
        # Convert to per-share value
        equity_value = self._convert_to_equity_value(enterprise_value, data)
        shares_outstanding = self._get_shares_outstanding(data)
        fair_value_per_share = equity_value / shares_outstanding
        
        # Calculate margin of safety
        current_price = self._get_current_price(data)
        margin_of_safety = None
        if current_price and current_price > 0:
            margin_of_safety = (fair_value_per_share - current_price) / current_price
        
        # Create result
        result = ValuationResult(
            ticker=ticker,
            model=self.name,
            fair_value=fair_value_per_share,
            current_price=current_price,
            margin_of_safety=margin_of_safety,
            enterprise_value=enterprise_value
        )
        
        result.inputs = {
            'free_cash_flow': fcf,
            'wacc': wacc,
            'high_growth_rate': high_growth,
            'moderate_growth_rate': moderate_growth,
            'terminal_growth': terminal_growth,
            'high_growth_years': self.high_growth_years,
            'moderate_growth_years': self.moderate_growth_years,
        }
        
        result.outputs = {
            'high_growth_fcfs': high_growth_fcfs,
            'moderate_growth_fcfs': moderate_growth_fcfs,
            'pv_fcfs': pv_fcfs,
            'terminal_value': terminal_value,
            'pv_terminal': pv_terminal,
            'equity_value': equity_value,
            'shares_outstanding': shares_outstanding,
        }
        
        return result