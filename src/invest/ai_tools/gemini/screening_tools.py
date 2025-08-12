"""
Gemini tools for systematic stock screening.

These tools allow Gemini to run the systematic analysis framework directly
and interpret results in natural language.
"""

from typing import Dict, List, Any, Optional
from ..core.screening import (
    run_systematic_screening,
    get_available_configs, 
    create_custom_screening
)


def systematic_screen(
    criteria: str = "default", 
    max_results: int = 20,
    save_results: bool = False
) -> Dict[str, Any]:
    """
    Run systematic stock screening based on specified criteria.
    
    Args:
        criteria: Either a config name (e.g., "conservative_value", "aggressive_growth")
                 or "default" for default analysis
        max_results: Maximum number of stocks to return
        save_results: Whether to save detailed results to file
    
    Returns:
        Dict containing screening results, top picks, and analysis summary
    
    Example usage by Gemini:
        results = systematic_screen("aggressive_growth", max_results=15)
        # Returns comprehensive analysis of growth stocks
    """
    return run_systematic_screening(criteria, max_results, save_results)


def get_screening_configs() -> Dict[str, Any]:
    """
    Get information about available screening configurations.
    
    Returns:
        Dict containing available configs and their descriptions
    
    Example usage by Gemini:
        configs = get_screening_configs()
        # Shows Gemini what screening options are available
    """
    return get_available_configs()


def create_custom_screen(
    name: str,
    quality_criteria: Optional[Dict] = None,
    value_criteria: Optional[Dict] = None, 
    growth_criteria: Optional[Dict] = None,
    risk_criteria: Optional[Dict] = None,
    universe_settings: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Create and run a custom screening configuration.
    
    Args:
        name: Name for this screening configuration
        quality_criteria: Dict with quality thresholds (min_roic, min_roe, etc.)
        value_criteria: Dict with value thresholds (max_pe, max_pb, etc.)
        growth_criteria: Dict with growth thresholds (min_revenue_growth, etc.)
        risk_criteria: Dict with risk thresholds (max_beta, etc.)
        universe_settings: Dict with universe settings (region, market_cap, etc.)
    
    Returns:
        Screening results using the custom criteria
    
    Example usage by Gemini:
        results = create_custom_screen(
            name="High Quality Value",
            quality_criteria={"min_roic": 0.15, "max_debt_equity": 0.4},
            value_criteria={"max_pe": 20, "max_pb": 2.5}
        )
    """
    return create_custom_screening(
        name, quality_criteria, value_criteria, 
        growth_criteria, risk_criteria, universe_settings
    )