import pandas as pd
import numpy as np
from typing import Dict, Optional
from ..config.schema import QualityThresholds


def calculate_roic(data: Dict) -> float:
    """Calculate Return on Invested Capital."""
    # ROIC approximation using available data
    # ROIC = NOPAT / Invested Capital
    # Approximation: ROE adjusted for leverage
    
    roe = data.get('return_on_equity', 0)
    if not roe or roe <= 0:
        return 0.0
    
    debt_ratio = data.get('debt_to_equity', 0)
    if debt_ratio and debt_ratio > 0:
        # Rough ROIC approximation: ROE / (1 + D/E)
        roic = roe / (1 + debt_ratio / 100)
    else:
        roic = roe  # If no debt, ROIC ≈ ROE
    
    return max(0.0, roic)


def calculate_interest_coverage(data: Dict) -> Optional[float]:
    """Calculate interest coverage ratio (EBIT / Interest Expense)."""
    # This would require income statement data
    # For now, use a proxy based on debt levels and profitability
    debt_ratio = data.get('debt_to_equity', 0)
    roe = data.get('return_on_equity', 0)
    
    if not debt_ratio or debt_ratio <= 0 or not roe:
        return None
    
    # Rough approximation: lower debt ratio = higher coverage
    # This is very approximate - real calculation needs EBIT and interest expense
    if debt_ratio < 20:
        return 10.0  # Assume good coverage for low debt companies
    elif debt_ratio < 50:
        return 5.0   # Moderate coverage
    else:
        return 2.0   # Lower coverage for high debt


def assess_quality(data: Dict, thresholds: QualityThresholds) -> Dict:
    """Assess quality metrics for a single stock."""
    results = {
        'ticker': data.get('ticker', 'N/A'),
        'quality_score': 0,
        'quality_flags': [],
        'quality_metrics': {}
    }
    
    # Calculate derived metrics
    roic = calculate_roic(data)
    roe = data.get('return_on_equity', 0) or 0
    current_ratio = data.get('current_ratio', 0) or 0
    debt_equity = data.get('debt_to_equity', 0) or 0
    interest_coverage = calculate_interest_coverage(data)
    
    results['quality_metrics'] = {
        'roic': roic,
        'roe': roe,
        'current_ratio': current_ratio,
        'debt_to_equity': debt_equity,
        'interest_coverage': interest_coverage
    }
    
    # Score each quality metric (0-1 scale)
    score = 0
    max_score = 0
    
    # ROIC scoring
    if thresholds.min_roic is not None:
        max_score += 1
        if roic >= thresholds.min_roic:
            score += 1
        else:
            results['quality_flags'].append(f"ROIC {roic:.1%} below threshold {thresholds.min_roic:.1%}")
    
    # ROE scoring
    if thresholds.min_roe is not None:
        max_score += 1
        if roe >= thresholds.min_roe:
            score += 1
        else:
            results['quality_flags'].append(f"ROE {roe:.1%} below threshold {thresholds.min_roe:.1%}")
    
    # Current ratio scoring
    if thresholds.min_current_ratio is not None:
        max_score += 1
        if current_ratio >= thresholds.min_current_ratio:
            score += 1
        else:
            results['quality_flags'].append(f"Current ratio {current_ratio:.2f} below threshold {thresholds.min_current_ratio:.2f}")
    
    # Debt/equity scoring (inverse - lower is better)
    if thresholds.max_debt_equity is not None:
        max_score += 1
        debt_equity_ratio = debt_equity / 100 if debt_equity > 5 else debt_equity  # Handle percentage vs ratio
        if debt_equity_ratio <= thresholds.max_debt_equity:
            score += 1
        else:
            results['quality_flags'].append(f"Debt/Equity {debt_equity_ratio:.2f} above threshold {thresholds.max_debt_equity:.2f}")
    
    # Interest coverage scoring
    if thresholds.min_interest_coverage is not None and interest_coverage is not None:
        max_score += 1
        if interest_coverage >= thresholds.min_interest_coverage:
            score += 1
        else:
            results['quality_flags'].append(f"Interest coverage {interest_coverage:.1f} below threshold {thresholds.min_interest_coverage:.1f}")
    
    # Calculate final quality score (0-100 scale)
    if max_score > 0:
        results['quality_score'] = (score / max_score) * 100
    else:
        results['quality_score'] = 0
    
    return results


def screen_quality(stocks_data: list[Dict], thresholds: QualityThresholds) -> list[Dict]:
    """Screen multiple stocks for quality criteria."""
    results = []
    
    for stock_data in stocks_data:
        quality_result = assess_quality(stock_data, thresholds)
        results.append(quality_result)
    
    return results


def apply_quality_filters(stocks_data: list[Dict], thresholds: QualityThresholds, 
                         min_quality_score: float = 60.0) -> list[Dict]:
    """Filter stocks that meet minimum quality requirements."""
    quality_results = screen_quality(stocks_data, thresholds)
    
    # Filter by minimum quality score
    filtered = [
        result for result in quality_results 
        if result['quality_score'] >= min_quality_score
    ]
    
    return filtered


def rank_by_quality(stocks_data: list[Dict], thresholds: QualityThresholds) -> list[Dict]:
    """Rank stocks by quality score (highest first)."""
    quality_results = screen_quality(stocks_data, thresholds)
    
    return sorted(quality_results, key=lambda x: x['quality_score'], reverse=True)