#!/usr/bin/env python3
"""
Enhanced MCP Server for Investment Analysis
============================================

Modern MCP server that exposes the complete investment analysis system to AI assistants.
"""

import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from mcp.server.fastmcp import FastMCP

# Import the modern valuation system
from src.invest.valuation.model_registry import ModelRegistry
from src.invest.valuation.multi_timeframe_models import MultiTimeframeNeuralNetworks

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize components
mcp = FastMCP('investment-analysis')
model_registry = ModelRegistry()
neural_networks = MultiTimeframeNeuralNetworks()
cache_dir = Path('data/cache')
cache_dir.mkdir(parents=True, exist_ok=True)

# Utility functions
async def get_stock_data(ticker: str, use_cache: bool = True) -> Optional[Dict]:
    """Get stock data from cache or fetch fresh data."""
    try:
        cache_file = cache_dir / f'{ticker}.json'

        if use_cache and cache_file.exists():
            cache_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
            if cache_age < timedelta(hours=4):
                with open(cache_file, 'r') as f:
                    return json.load(f)

        import yfinance as yf
        stock = yf.Ticker(ticker)
        data = stock.info

        if data and data.get('currentPrice'):
            with open(cache_file, 'w') as f:
                json.dump(data, f)
            return data

        return None

    except Exception as e:
        logger.warning(f'Error getting data for {ticker}: {e}')
        return None

def get_model_display_name(model_name: str) -> str:
    """Get display name for a model."""
    display_names = {
        'dcf': 'Standard DCF',
        'dcf_enhanced': 'Enhanced DCF',
        'multi_stage_dcf': 'Multi-Stage DCF',
        'growth_dcf': 'Growth DCF',
        'simple_ratios': 'Market Ratios',
        'rim': 'RIM Model',
        'neural_network_best': 'AI Best (2Y)',
        'neural_network_consensus': 'AI Consensus',
        'ensemble': 'Ensemble'
    }
    return display_names.get(model_name, model_name)

def format_stock_analysis(ticker: str, stock_data: Dict, results: Dict) -> str:
    """Format comprehensive stock analysis response."""
    company_name = stock_data.get('longName', ticker)
    current_price = stock_data.get('currentPrice', 0)
    market_cap = stock_data.get('marketCap', 0)
    sector = stock_data.get('sector', 'Unknown')

    response = f'📈 **Investment Analysis: {company_name} ({ticker})**\\n\\n'

    # Company basics
    response += '**Company Overview:**\\n'
    response += f'• Current Price: ${current_price:.2f}\\n'
    response += f'• Market Cap: ${market_cap/1e9:.1f}B\\n'
    response += f'• Sector: {sector}\\n'
    response += f'• P/E Ratio: {stock_data.get("trailingPE", "N/A")}\\n\\n'

    if not results:
        response += '❌ No valuation models produced results'
        return response

    # Valuation results
    response += f'**Valuation Results:** ({len(results)} models)\\n'
    response += f'{"Model":<20} {"Fair Value":<12} {"Upside":<10}\\n'
    response += '-' * 50 + '\\n'

    # Sort by margin of safety
    sorted_results = sorted(results.items(),
                          key=lambda x: x[1].margin_of_safety or 0,
                          reverse=True)

    for model_name, result in sorted_results:
        model_display = get_model_display_name(model_name)
        fair_value = f'${result.fair_value:.2f}' if result.fair_value else 'N/A'
        margin = result.margin_of_safety

        if margin is not None:
            margin_str = f'{margin:+.1f}%'
        else:
            margin_str = 'N/A'

        response += f'{model_display:<20} {fair_value:<12} {margin_str:<10}\\n'

    # Consensus
    fair_values = [r.fair_value for r in results.values() if r.fair_value]
    if len(fair_values) > 1:
        avg_fair_value = sum(fair_values) / len(fair_values)
        consensus_margin = (avg_fair_value - current_price) / current_price * 100

        response += '\\n**Consensus Analysis:**\\n'
        response += f'• Average Fair Value: ${avg_fair_value:.2f}\\n'
        response += f'• Consensus Margin: {consensus_margin:+.1f}%\\n'

    return response

# MCP Tools
@mcp.tool()
async def analyze_stock(
    ticker: str,
    models: Optional[List[str]] = None,
    use_cache: bool = True
) -> str:
    """
    Comprehensive stock analysis with multiple valuation models.
    
    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        models: List of models to use. Available: dcf, dcf_enhanced, multi_stage_dcf, 
               growth_dcf, rim, simple_ratios, neural_network_best, neural_network_consensus, ensemble
        use_cache: Whether to use cached data (default: True)
    
    Returns:
        Detailed analysis with valuations from multiple models
    """
    try:
        ticker = ticker.upper()

        # Get available models if not specified
        if models is None:
            models = ['dcf', 'dcf_enhanced', 'simple_ratios', 'neural_network_best']

        # Validate models
        available_models = model_registry.get_available_models()
        valid_models = [m for m in models if m in available_models]

        if not valid_models:
            return f'❌ No valid models specified. Available: {", ".join(available_models[:8])}'

        # Get stock data
        stock_data = await get_stock_data(ticker, use_cache)
        if not stock_data:
            return f'❌ Could not fetch data for {ticker}'

        # Run valuations
        results = {}

        for model_name in valid_models:
            try:
                model = model_registry.get_model(model_name)
                if model and model.is_suitable(ticker, stock_data):
                    result = model.value_company(ticker, verbose=False)
                    if result:
                        results[model_name] = result
            except Exception as e:
                logger.warning(f'Model {model_name} failed for {ticker}: {e}')
                continue

        # Format comprehensive response
        response = format_stock_analysis(ticker, stock_data, results)
        return response

    except Exception as e:
        logger.error(f'Error analyzing {ticker}: {e}')
        return f'❌ Analysis failed for {ticker}: {str(e)}'

@mcp.tool()
async def neural_predict(
    ticker: str,
    timeframe: str = '2year',
    include_all_timeframes: bool = False
) -> str:
    """
    Get neural network predictions for a stock.
    
    Args:
        ticker: Stock ticker symbol
        timeframe: Prediction horizon ('1month', '3month', '6month', '1year', '18month', '2year', '3year')
        include_all_timeframes: If True, show predictions from all neural network models
    
    Returns:
        Neural network predictions with confidence metrics and model performance data
    """
    try:
        ticker = ticker.upper()

        if include_all_timeframes:
            # Get predictions from all timeframes
            results = neural_networks.value_company_all_timeframes(ticker)
            consensus = neural_networks.get_consensus_valuation(ticker)

            response = f'🧠 **Neural Network Analysis for {ticker}**\\n\\n'

            # Show performance summary
            performance = neural_networks.get_performance_summary()
            response += '**Model Performance:**\\n'
            for tf, info in performance.items():
                if results.get(tf):
                    correlation = info.get('correlation', 0)
                    hit_rate = info.get('hit_rate', 0)
                    recommended = '⭐' if info.get('recommended', False) else '•'
                    response += f'{recommended} {tf:8} ({info["months"]:2}m): Corr={correlation:.3f}, Hit Rate={hit_rate:.0%}\\n'

            response += '\\n**Predictions by Timeframe:**\\n'
            for tf in ['1month', '3month', '6month', '1year', '18month', '2year', '3year']:
                result = results.get(tf)
                if result:
                    margin = result.margin_of_safety
                    response += f'• {tf:8}: ${result.fair_value:.2f} ({margin:+.1f}%)\\n'
                else:
                    response += f'• {tf:8}: Not available\\n'

            if consensus:
                response += f'\\n**🎯 Consensus Prediction: ${consensus.fair_value:.2f} ({consensus.margin_of_safety:+.1f}%)**\\n'

            return response

        else:
            # Single timeframe prediction
            model = neural_networks.get_model(timeframe)
            if not model:
                available = list(neural_networks.AVAILABLE_TIMEFRAMES.keys())
                return f'❌ Timeframe "{timeframe}" not available. Options: {", ".join(available)}'

            result = model.value_company(ticker, verbose=False)
            if not result:
                return f'❌ Neural network prediction failed for {ticker}'

            # Get model info
            timeframe_info = neural_networks.AVAILABLE_TIMEFRAMES[timeframe]
            performance = neural_networks.get_performance_summary().get(timeframe, {})

            response = f'🧠 **Neural Network Prediction for {ticker}**\\n\\n'
            response += f'**Model:** {timeframe} ({timeframe_info["months"]} months)\\n'
            response += f'**Description:** {timeframe_info["description"]}\\n\\n'

            response += '**Performance Metrics:**\\n'
            response += f'• Correlation: {performance.get("correlation", 0):.3f}\\n'
            response += f'• Hit Rate: {performance.get("hit_rate", 0):.0%}\\n\\n'

            response += '**Prediction:**\\n'
            response += f'• Current Price: ${result.current_price:.2f}\\n'
            response += f'• Fair Value: ${result.fair_value:.2f}\\n'
            response += f'• Margin of Safety: {result.margin_of_safety:+.1f}%\\n\\n'

            if result.margin_of_safety > 20:
                response += '🔥 **Strong Buy** - High upside potential'
            elif result.margin_of_safety > 5:
                response += '📈 **Buy** - Moderate upside'
            elif result.margin_of_safety > -5:
                response += '➡️ **Hold** - Fair value'
            elif result.margin_of_safety > -20:
                response += '📉 **Sell** - Overvalued'
            else:
                response += '🧊 **Strong Sell** - Significantly overvalued'

            return response

    except Exception as e:
        logger.error(f'Neural prediction error for {ticker}: {e}')
        return f'❌ Neural network prediction failed: {str(e)}'

@mcp.tool()
async def get_model_info(model_name: Optional[str] = None) -> str:
    """
    Get information about valuation models.
    
    Args:
        model_name: Specific model to get info about (None = list all models)
    
    Returns:
        Model information including description, suitable use cases, and requirements
    """
    try:
        available_models = model_registry.get_available_models()
        metadata = model_registry._MODEL_METADATA

        if model_name:
            if model_name not in available_models:
                return f'❌ Model "{model_name}" not found. Available: {", ".join(available_models[:10])}'

            info = metadata.get(model_name, {})
            response = f'📋 **{info.get("name", model_name)}**\\n\\n'
            response += f'**Description:** {info.get("description", "No description available")}\\n'
            response += f'**Suitable for:** {", ".join(info.get("suitable_for", ["General use"]))}\\n'
            response += f'**Time horizon:** {info.get("time_horizon", "Not specified")}\\n'
            response += f'**Complexity:** {info.get("complexity", "Medium")}\\n'
            response += f'**Data requirements:** {", ".join(info.get("data_requirements", ["Basic financial data"]))}\\n'

            return response

        else:
            # List all models with brief descriptions
            response = f'📚 **Available Valuation Models** ({len(available_models)} total)\\n\\n'

            # Group models by category
            dcf_models = [m for m in available_models if 'dcf' in m.lower()]
            neural_models = [m for m in available_models if 'neural' in m.lower()]
            other_models = [m for m in available_models if m not in dcf_models and m not in neural_models]

            if dcf_models:
                response += '**DCF Models:**\\n'
                for model in dcf_models:
                    name = metadata.get(model, {}).get('name', model)
                    response += f'• **{model}**: {name}\\n'
                response += '\\n'

            if neural_models:
                response += '**Neural Network Models:**\\n'
                for model in neural_models:
                    if 'best' in model:
                        response += f'• **{model}**: 2-year AI model (51.8% correlation, best performance)\\n'
                    elif 'consensus' in model:
                        response += f'• **{model}**: Weighted average of all neural network timeframes\\n'
                    else:
                        response += f'• **{model}**: AI-powered valuation model\\n'
                response += '\\n'

            if other_models:
                response += '**Other Models:**\\n'
                for model in other_models:
                    name = metadata.get(model, {}).get('name', model)
                    response += f'• **{model}**: {name}\\n'

            response += '\\n💡 Use `get_model_info("model_name")` for detailed information about any model.'

            return response

    except Exception as e:
        logger.error(f'Error getting model info: {e}')
        return f'❌ Could not retrieve model information: {str(e)}'

@mcp.tool()
async def quick_compare(ticker: str) -> str:
    """
    Quick comparison of key valuation models for a stock.
    
    Args:
        ticker: Stock ticker symbol
    
    Returns:
        Side-by-side comparison of DCF, neural network, and market ratio valuations
    """
    try:
        ticker = ticker.upper()

        # Get stock data
        stock_data = await get_stock_data(ticker)
        if not stock_data:
            return f'❌ Could not fetch data for {ticker}'

        current_price = stock_data.get('currentPrice', 0)

        # Test key models
        models = ['dcf', 'simple_ratios', 'neural_network_best']
        results = {}

        for model_name in models:
            try:
                model = model_registry.get_model(model_name)
                if model and model.is_suitable(ticker, stock_data):
                    result = model.value_company(ticker, verbose=False)
                    if result:
                        results[model_name] = result
            except Exception as e:
                logger.warning(f'Model {model_name} failed: {e}')
                continue

        # Format comparison
        response = f'⚡ **Quick Comparison for {ticker}**\\n'
        response += f'Current Price: ${current_price:.2f}\\n\\n'

        if not results:
            return f'❌ No models produced valid results for {ticker}'

        for model_name, result in results.items():
            model_display = get_model_display_name(model_name)
            margin = result.margin_of_safety or 0

            if margin > 15:
                signal = '🔥 Strong Buy'
            elif margin > 5:
                signal = '📈 Buy'
            elif margin > -5:
                signal = '➡️ Hold'
            else:
                signal = '📉 Sell'

            response += f'**{model_display}**: ${result.fair_value:.2f} ({margin:+.1f}%) {signal}\\n'

        return response

    except Exception as e:
        logger.error(f'Quick comparison error for {ticker}: {e}')
        return f'❌ Quick comparison failed: {str(e)}'

if __name__ == '__main__':
    # Run the server
    logger.info('🚀 Investment Analysis MCP Server starting...')
    logger.info('Available tools: analyze_stock, neural_predict, get_model_info, quick_compare')
    mcp.run()
