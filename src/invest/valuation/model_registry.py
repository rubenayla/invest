"""
Model Registry for the unified valuation system.

This module provides a centralized registry for all available valuation models,
making it easy to discover, instantiate, and manage different valuation approaches.
"""

from typing import Dict, List, Optional, Type, Any
import logging

from .base import ValuationModel, ValuationResult
from .dcf_model import DCFModel, EnhancedDCFModel, MultiStageDCFModel
from .rim_model import RIMModel
from .ratios_model import SimpleRatiosModel

logger = logging.getLogger(__name__)


class ModelRegistry:
    """
    Central registry for all valuation models.
    
    This class manages model instantiation, provides model metadata,
    and offers utilities for model selection and execution.
    """
    
    # Registry of available model classes
    _MODEL_CLASSES = {
        'dcf': DCFModel,
        'dcf_enhanced': EnhancedDCFModel,
        'multi_stage_dcf': MultiStageDCFModel,
        'rim': RIMModel,
        'simple_ratios': SimpleRatiosModel,
    }
    
    # Model metadata for user interfaces and documentation
    _MODEL_METADATA = {
        'dcf': {
            'name': 'Standard DCF',
            'description': 'Discounted Cash Flow model with projected free cash flows',
            'suitable_for': ['Growing companies', 'Companies with predictable cash flows'],
            'time_horizon': '10 years',
            'complexity': 'medium',
            'data_requirements': ['Cash flow statement', 'Balance sheet', 'Income statement'],
        },
        'dcf_enhanced': {
            'name': 'Enhanced DCF', 
            'description': 'DCF with normalized cash flows and improved assumptions',
            'suitable_for': ['Volatile companies', 'Companies with lumpy cash flows'],
            'time_horizon': '10 years',
            'complexity': 'medium',
            'data_requirements': ['Multi-year cash flow data', 'Balance sheet', 'Income statement'],
        },
        'multi_stage_dcf': {
            'name': 'Multi-Stage DCF',
            'description': 'DCF with multiple growth phases for realistic projections',
            'suitable_for': ['Growth companies', 'Companies in transition'],
            'time_horizon': '10+ years',
            'complexity': 'high',
            'data_requirements': ['Cash flow statement', 'Balance sheet', 'Growth forecasts'],
        },
        'rim': {
            'name': 'Residual Income Model',
            'description': 'Values companies based on returns above cost of equity',
            'suitable_for': ['Financial companies', 'Mature companies', 'Asset-heavy businesses'],
            'time_horizon': '10 years',
            'complexity': 'medium',
            'data_requirements': ['Balance sheet', 'Income statement', 'ROE history'],
        },
        'simple_ratios': {
            'name': 'Market Multiples',
            'description': 'Quick valuation using industry ratios and multiples',
            'suitable_for': ['All companies', 'Quick screening', 'Cross-validation'],
            'time_horizon': 'Current',
            'complexity': 'low',
            'data_requirements': ['Basic financial metrics', 'Market data'],
        },
    }
    
    def __init__(self):
        """Initialize the model registry."""
        self._model_instances = {}
        self._model_stats = {name: {'runs': 0, 'successes': 0, 'failures': 0} 
                           for name in self._MODEL_CLASSES.keys()}
    
    def get_available_models(self) -> List[str]:
        """Get list of all available model names."""
        return list(self._MODEL_CLASSES.keys())
    
    def get_model_metadata(self, model_name: str = None) -> Dict[str, Any]:
        """
        Get metadata for a specific model or all models.
        
        Parameters
        ----------
        model_name : str, optional
            Name of specific model. If None, returns all model metadata.
            
        Returns
        -------
        Dict[str, Any]
            Model metadata
        """
        if model_name:
            return self._MODEL_METADATA.get(model_name, {})
        return self._MODEL_METADATA.copy()
    
    def get_model(self, model_name: str) -> ValuationModel:
        """
        Get a model instance by name.
        
        Parameters
        ----------
        model_name : str
            Name of the model to instantiate
            
        Returns
        -------
        ValuationModel
            The model instance
            
        Raises
        ------
        ValueError
            If model name is not recognized
        """
        if model_name not in self._MODEL_CLASSES:
            available = ', '.join(self.get_available_models())
            raise ValueError(f'Unknown model: {model_name}. Available: {available}')
        
        # Use cached instance if available
        if model_name not in self._model_instances:
            model_class = self._MODEL_CLASSES[model_name]
            self._model_instances[model_name] = model_class()
        
        return self._model_instances[model_name]
    
    def run_valuation(self, model_name: str, ticker: str, verbose: bool = False) -> Optional[ValuationResult]:
        """
        Run a valuation using the specified model.
        
        Parameters
        ----------
        model_name : str
            Name of the model to use
        ticker : str
            Stock ticker symbol
        verbose : bool
            Whether to enable verbose logging
            
        Returns
        -------
        Optional[ValuationResult]
            Valuation result or None if failed
        """
        try:
            model = self.get_model(model_name)
            self._model_stats[model_name]['runs'] += 1
            
            result = model.value_company(ticker, verbose=verbose)
            
            if result and result.is_valid():
                self._model_stats[model_name]['successes'] += 1
                logger.info(f'{model_name} valuation successful for {ticker}: ${result.fair_value:.2f}')
                return result
            else:
                self._model_stats[model_name]['failures'] += 1
                logger.warning(f'{model_name} valuation returned invalid result for {ticker}')
                return None
                
        except Exception as e:
            self._model_stats[model_name]['failures'] += 1
            logger.error(f'{model_name} valuation failed for {ticker}: {str(e)}')
            return None
    
    def run_all_suitable_models(self, ticker: str, verbose: bool = False) -> Dict[str, ValuationResult]:
        """
        Run all models that are suitable for the given ticker.
        
        Parameters
        ----------
        ticker : str
            Stock ticker symbol
        verbose : bool
            Whether to enable verbose logging
            
        Returns
        -------
        Dict[str, ValuationResult]
            Dictionary mapping model names to their results
        """
        results = {}
        
        # First, fetch data once to check model suitability
        try:
            # Use any model to fetch data (they all use similar data sources)
            sample_model = self.get_model('simple_ratios')  # Least demanding model
            data = sample_model._fetch_data(ticker)
        except Exception as e:
            logger.error(f'Failed to fetch data for {ticker}: {str(e)}')
            return results
        
        # Test each model for suitability and run if appropriate
        for model_name in self.get_available_models():
            try:
                model = self.get_model(model_name)
                
                if model.is_suitable(ticker, data):
                    result = self.run_valuation(model_name, ticker, verbose)
                    if result:
                        results[model_name] = result
                else:
                    if verbose:
                        logger.info(f'{model_name} not suitable for {ticker}')
                        
            except Exception as e:
                logger.error(f'Error testing {model_name} for {ticker}: {str(e)}')
                continue
        
        return results
    
    def get_model_recommendations(self, ticker: str, data: Dict[str, Any] = None) -> List[str]:
        """
        Get recommended models for a specific ticker based on its characteristics.
        
        Parameters
        ----------
        ticker : str
            Stock ticker symbol
        data : Dict[str, Any], optional
            Pre-fetched company data
            
        Returns
        -------
        List[str]
            List of recommended model names in priority order
        """
        if data is None:
            try:
                sample_model = self.get_model('simple_ratios')
                data = sample_model._fetch_data(ticker)
            except:
                # Return general recommendations if data fetch fails
                return ['simple_ratios', 'dcf', 'rim']
        
        recommendations = []
        
        # Check company characteristics
        info = data.get('info', {})
        sector = info.get('sector', '')
        market_cap = info.get('marketCap', 0)
        
        # Simple ratios - always suitable for quick screening
        recommendations.append('simple_ratios')
        
        # DCF models - good for most companies
        if self._has_positive_cash_flow(data):
            if market_cap > 10_000_000_000:  # Large cap
                recommendations.extend(['dcf_enhanced', 'dcf'])
            elif market_cap > 1_000_000_000:  # Mid cap
                recommendations.extend(['dcf', 'multi_stage_dcf'])
            else:  # Small cap
                recommendations.append('multi_stage_dcf')
        
        # RIM - especially good for financial companies
        if 'Financial' in sector or 'Bank' in sector:
            recommendations.insert(1, 'rim')  # High priority for financials
        elif self._has_stable_roe(data):
            recommendations.append('rim')
        
        return recommendations
    
    def _has_positive_cash_flow(self, data: Dict[str, Any]) -> bool:
        """Check if company has positive free cash flow."""
        try:
            cashflow = data.get('cashflow')
            if cashflow is None or cashflow.empty:
                return False
            
            # Look for operating cash flow
            if 'Total Cash From Operating Activities' in cashflow.index:
                ocf = cashflow.loc['Total Cash From Operating Activities'].iloc[0] if len(cashflow.columns) > 0 else None
                return ocf is not None and ocf > 0
            
            return False
        except:
            return False
    
    def _has_stable_roe(self, data: Dict[str, Any]) -> bool:
        """Check if company has stable ROE suitable for RIM."""
        try:
            # This is a simplified check - in practice would analyze ROE history
            info = data.get('info', {})
            roe = info.get('returnOnEquity')
            return roe is not None and 0.05 < roe < 0.3  # 5% to 30% ROE range
        except:
            return False
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get statistics about model usage and performance."""
        stats = {}
        
        for model_name, model_stats in self._model_stats.items():
            runs = model_stats['runs']
            successes = model_stats['successes']
            success_rate = (successes / runs) if runs > 0 else 0
            
            stats[model_name] = {
                'runs': runs,
                'successes': successes,
                'failures': model_stats['failures'],
                'success_rate': success_rate,
                'metadata': self._MODEL_METADATA.get(model_name, {})
            }
        
        return stats
    
    def reset_stats(self):
        """Reset all model statistics."""
        self._model_stats = {name: {'runs': 0, 'successes': 0, 'failures': 0} 
                           for name in self._MODEL_CLASSES.keys()}
        logger.info('Model registry statistics reset')


# Global registry instance
_registry = ModelRegistry()

# Convenience functions that use the global registry
def get_model(model_name: str) -> ValuationModel:
    """Get a model instance from the global registry."""
    return _registry.get_model(model_name)

def run_valuation(model_name: str, ticker: str, verbose: bool = False) -> Optional[ValuationResult]:
    """Run a valuation using the global registry."""
    return _registry.run_valuation(model_name, ticker, verbose)

def get_available_models() -> List[str]:
    """Get available models from the global registry."""
    return _registry.get_available_models()

def run_all_suitable_models(ticker: str, verbose: bool = False) -> Dict[str, ValuationResult]:
    """Run all suitable models from the global registry."""
    return _registry.run_all_suitable_models(ticker, verbose)

# Backward compatibility functions that maintain the old interface
def calculate_dcf(ticker: str, verbose: bool = False) -> Optional[dict]:
    """Backward compatibility wrapper for DCF model."""
    result = run_valuation('dcf', ticker, verbose)
    return result.to_dict() if result else None

def calculate_enhanced_dcf(ticker: str, verbose: bool = False) -> Optional[dict]:
    """Backward compatibility wrapper for Enhanced DCF model.""" 
    result = run_valuation('dcf_enhanced', ticker, verbose)
    return result.to_dict() if result else None

def calculate_multi_stage_dcf(ticker: str, verbose: bool = False) -> Optional[dict]:
    """Backward compatibility wrapper for Multi-Stage DCF model."""
    result = run_valuation('multi_stage_dcf', ticker, verbose)
    return result.to_dict() if result else None

def calculate_rim(ticker: str, verbose: bool = False) -> Optional[dict]:
    """Backward compatibility wrapper for RIM model."""
    result = run_valuation('rim', ticker, verbose)
    return result.to_dict() if result else None

def calculate_simple_ratios_valuation(ticker: str, verbose: bool = False) -> Optional[dict]:
    """Backward compatibility wrapper for Simple Ratios model."""
    result = run_valuation('simple_ratios', ticker, verbose)
    return result.to_dict() if result else None