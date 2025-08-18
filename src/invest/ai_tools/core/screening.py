"""
Shared core screening logic for multi-provider AI tools.

This module contains the business logic for systematic stock screening
that can be used by any AI provider (Claude, Gemini, etc.).
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from invest.analysis.pipeline import AnalysisPipeline  # noqa: E402
from invest.config.loader import list_available_configs, load_analysis_config  # noqa: E402
from invest.config.schema import (  # noqa: E402
    AnalysisConfig,
)


def run_systematic_screening(
    criteria: str = "default", max_results: int = 20, save_results: bool = False
) -> Dict[str, Any]:
    """
    Core systematic screening logic shared across AI providers.

    Args:
        criteria: Configuration name or path
        max_results: Maximum number of stocks to return
        save_results: Whether to save detailed results to file

    Returns:
        Dict containing screening results and analysis summary
    """
    try:
        # Load configuration
        config = _load_screening_config(criteria)
        config.max_results = max_results

        # Run analysis pipeline
        pipeline = AnalysisPipeline(config)
        results = pipeline.run_analysis()

        # Format results
        formatted_results = _format_screening_results(results, config)

        # Save results if requested
        if save_results:
            output_path = Path(f"screening_results_{criteria}.json")
            with open(output_path, "w") as f:
                json.dump(results, f, indent=2, default=str)
            formatted_results["saved_to"] = str(output_path)

        return formatted_results

    except Exception as e:
        return {"error": str(e), "message": f"Failed to run screening with criteria '{criteria}'"}


def get_available_configs() -> Dict[str, Any]:
    """
    Get information about available screening configurations.

    Returns:
        Dict containing available configs and their descriptions
    """
    try:
        configs_info = {
            "available_configs": [],
            "config_directory": str(Path(__file__).parent.parent.parent.parent.parent / "configs"),
        }

        config_paths = list_available_configs()

        for config_path in config_paths:
            try:
                config = load_analysis_config(config_path)
                config_info = _extract_config_info(config_path, config)
                configs_info["available_configs"].append(config_info)

            except Exception as e:
                configs_info["available_configs"].append(
                    {"name": config_path.stem, "error": f"Failed to load: {str(e)}"}
                )

        return configs_info

    except Exception as e:
        return {"error": str(e), "message": "Failed to load configuration information"}


def create_custom_screening(
    name: str,
    quality_criteria: Optional[Dict] = None,
    value_criteria: Optional[Dict] = None,
    growth_criteria: Optional[Dict] = None,
    risk_criteria: Optional[Dict] = None,
    universe_settings: Optional[Dict] = None,
    max_results: int = 20,
) -> Dict[str, Any]:
    """
    Create and run a custom screening configuration.

    Args:
        name: Name for this screening configuration
        quality_criteria: Quality thresholds (min_roic, min_roe, etc.)
        value_criteria: Value thresholds (max_pe, max_pb, etc.)
        growth_criteria: Growth thresholds (min_revenue_growth, etc.)
        risk_criteria: Risk thresholds (max_beta, etc.)
        universe_settings: Universe settings (region, market_cap, etc.)
        max_results: Maximum results to return

    Returns:
        Screening results using the custom criteria
    """
    try:
        # Build configuration dictionary
        config_dict = {
            "name": name,
            "description": f"Custom screening: {name}",
            "max_results": max_results,
        }

        if universe_settings:
            config_dict["universe"] = universe_settings
        if quality_criteria:
            config_dict["quality"] = quality_criteria
        if value_criteria:
            config_dict["value"] = value_criteria
        if growth_criteria:
            config_dict["growth"] = growth_criteria
        if risk_criteria:
            config_dict["risk"] = risk_criteria

        # Create and validate configuration
        config = AnalysisConfig(**config_dict)

        # Run analysis pipeline
        pipeline = AnalysisPipeline(config)
        results = pipeline.run_analysis()

        return _format_screening_results(results, config)

    except Exception as e:
        return {"error": str(e), "message": f"Failed to create custom screen '{name}'"}


def _load_screening_config(criteria: str) -> AnalysisConfig:
    """Load screening configuration from criteria string."""
    if criteria == "default":
        config_path = (
            Path(__file__).parent.parent.parent.parent.parent / "configs" / "default_analysis.yaml"
        )
    else:
        config_path = (
            Path(__file__).parent.parent.parent.parent.parent / "configs" / f"{criteria}.yaml"
        )
        if not config_path.exists():
            config_path = Path(__file__).parent.parent.parent.parent.parent / "configs" / criteria

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration '{criteria}' not found")

    return load_analysis_config(config_path)


def _format_screening_results(results: Dict[str, Any], config: AnalysisConfig) -> Dict[str, Any]:
    """Format screening results for AI consumption."""
    formatted_results = {
        "analysis_name": config.name,
        "description": config.description,
        "screening_summary": {
            "total_universe": results.get("total_universe", 0),
            "passed_screening": results.get("passed_screening", 0),
            "final_results": results.get("final_results", 0),
            "success_rate": f"{(results.get('final_results', 0) / results.get('total_universe', 1) * 100):.1f}%",
        },
        "top_picks": [],
        "sector_breakdown": results.get("summary", {}).get("sector_breakdown", {}),
        "average_scores": results.get("summary", {}).get("average_scores", {}),
        "criteria_used": {
            "quality_filters": dict(config.quality) if config.quality else {},
            "value_filters": dict(config.value) if config.value else {},
            "growth_filters": dict(config.growth) if config.growth else {},
            "risk_filters": dict(config.risk) if config.risk else {},
        },
    }

    # Extract top picks with key information
    stocks = results.get("stocks", [])[: config.max_results or 20]
    for stock in stocks:
        basic_data = stock.get("basic_data", {})
        scores = stock.get("scores", {})

        pick = {
            "ticker": stock.get("ticker", "N/A"),
            "company_name": basic_data.get("longName", "N/A"),
            "sector": basic_data.get("sector", "N/A"),
            "market_cap_b": f"{basic_data.get('market_cap', 0) / 1e9:.2f}",
            "current_price": f"${basic_data.get('current_price', 0):.2f}",
            "scores": {
                "composite": f"{scores.get('composite', 0):.1f}",
                "quality": f"{scores.get('quality', 0):.1f}",
                "value": f"{scores.get('value', 0):.1f}",
                "growth": f"{scores.get('growth', 0):.1f}",
                "risk": f"{scores.get('risk', 0):.1f}",
            },
            "key_metrics": {
                "pe_ratio": f"{basic_data.get('trailing_pe', 0):.1f}"
                if basic_data.get("trailing_pe")
                else "N/A",
                "pb_ratio": f"{basic_data.get('price_to_book', 0):.2f}"
                if basic_data.get("price_to_book")
                else "N/A",
                "roe": f"{basic_data.get('return_on_equity', 0):.1%}"
                if basic_data.get("return_on_equity")
                else "N/A",
                "debt_equity": f"{basic_data.get('debt_to_equity', 0):.1f}"
                if basic_data.get("debt_to_equity")
                else "N/A",
            },
            "flags": {
                "quality_flags": stock.get("quality", {}).get("quality_flags", []),
                "value_flags": stock.get("value", {}).get("value_flags", []),
                "growth_flags": stock.get("growth", {}).get("growth_flags", []),
                "risk_flags": stock.get("risk", {}).get("risk_flags", []),
            },
        }
        formatted_results["top_picks"].append(pick)

    return formatted_results


def _extract_config_info(config_path: Path, config: AnalysisConfig) -> Dict[str, Any]:
    """Extract configuration information for display."""
    config_info = {
        "name": config_path.stem,
        "file_name": config_path.name,
        "display_name": config.name,
        "description": config.description or "No description provided",
        "focus_areas": [],
    }

    # Identify focus areas based on thresholds
    if config.quality and any([config.quality.min_roic, config.quality.min_roe]):
        config_info["focus_areas"].append("Quality")
    if config.value and any([config.value.max_pe, config.value.max_pb]):
        config_info["focus_areas"].append("Value")
    if config.growth and any([config.growth.min_revenue_growth, config.growth.min_earnings_growth]):
        config_info["focus_areas"].append("Growth")
    if config.risk and any([config.risk.max_beta, config.risk.cyclical_adjustment]):
        config_info["focus_areas"].append("Risk Management")

    # Add key criteria summary
    criteria_summary = []
    if config.quality:
        if config.quality.min_roic:
            criteria_summary.append(f"Min ROIC: {config.quality.min_roic:.1%}")
        if config.quality.min_roe:
            criteria_summary.append(f"Min ROE: {config.quality.min_roe:.1%}")

    if config.value:
        if config.value.max_pe:
            criteria_summary.append(f"Max P/E: {config.value.max_pe}")
        if config.value.max_pb:
            criteria_summary.append(f"Max P/B: {config.value.max_pb}")

    if config.growth:
        if config.growth.min_revenue_growth:
            criteria_summary.append(f"Min Revenue Growth: {config.growth.min_revenue_growth:.1%}")

    config_info["key_criteria"] = criteria_summary
    return config_info
