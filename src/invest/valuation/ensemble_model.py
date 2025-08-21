"""
Ensemble Valuation Model

This model combines multiple valuation approaches to provide more robust and reliable
valuations. It uses sophisticated weighting schemes based on model confidence,
data quality, and company characteristics.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
from dataclasses import dataclass, field

from .base import ValuationModel, ValuationResult
# Import registry functions dynamically to avoid circular imports
from ..exceptions import InsufficientDataError

logger = logging.getLogger(__name__)


@dataclass
class ModelWeight:
    """Weight assignment for a specific model in the ensemble."""
    model_name: str
    weight: float
    confidence: str
    reason: str


@dataclass
class EnsembleResult(ValuationResult):
    """Extended result class for ensemble valuations."""
    constituent_models: List[str] = field(default_factory=list)
    model_weights: List[ModelWeight] = field(default_factory=list)
    individual_results: Dict[str, ValuationResult] = field(default_factory=dict)
    consensus_metrics: Dict[str, float] = field(default_factory=dict)
    
    def __post_init__(self):
        """Calculate additional ensemble metrics."""
        # Don't call super().__post_init__() as ValuationResult doesn't have it
        if self.individual_results:
            self._calculate_consensus_metrics()
    
    def _calculate_consensus_metrics(self):
        """Calculate consensus metrics across all models."""
        valid_results = [r for r in self.individual_results.values() 
                        if r and r.fair_value is not None]
        
        if not valid_results:
            return
        
        fair_values = [r.fair_value for r in valid_results]
        
        self.consensus_metrics = {
            'model_count': len(valid_results),
            'value_std': np.std(fair_values) if len(fair_values) > 1 else 0.0,
            'value_range': max(fair_values) - min(fair_values) if fair_values else 0.0,
            'value_cv': np.std(fair_values) / np.mean(fair_values) if fair_values and np.mean(fair_values) > 0 else 0.0,
            'min_value': min(fair_values) if fair_values else None,
            'max_value': max(fair_values) if fair_values else None,
            'median_value': np.median(fair_values) if fair_values else None,
        }


class EnsembleModel(ValuationModel):
    """
    Ensemble valuation model that combines multiple approaches.
    
    This model:
    - Automatically selects appropriate models for each company
    - Applies intelligent weighting based on model suitability and confidence
    - Provides uncertainty quantification and consensus metrics
    - Handles model failures gracefully
    """
    
    def __init__(self, model_selection: str = 'auto'):
        """
        Initialize ensemble model.
        
        Parameters
        ----------
        model_selection : str
            Strategy for selecting models ('auto', 'all', 'recommended')
        """
        super().__init__('ensemble_model')
        self.model_selection = model_selection
        
    def is_suitable(self, ticker: str, data: Dict[str, Any]) -> bool:
        """Ensemble is always suitable - it adapts to available models."""
        return True
    
    def _validate_inputs(self, ticker: str, data: Dict[str, Any]) -> None:
        """Validate that we can get at least one model result."""
        if not data.get('info'):
            raise InsufficientDataError(ticker, ['info'])
    
    def _calculate_valuation(self, ticker: str, data: Dict[str, Any]) -> EnsembleResult:
        """Calculate ensemble valuation using multiple models."""
        
        # Select which models to use
        selected_models = self._select_models(ticker, data)
        
        if not selected_models:
            raise InsufficientDataError(ticker, ['suitable_models'])
        
        # Run all selected models
        individual_results = {}
        for model_name in selected_models:
            try:
                # Import registry dynamically to avoid circular imports
                from . import model_registry
                result = model_registry.run_valuation(model_name, ticker, verbose=False)
                if result and result.is_valid():
                    individual_results[model_name] = result
                else:
                    logger.debug(f'Model {model_name} produced invalid result for {ticker}')
            except Exception as e:
                logger.debug(f'Model {model_name} failed for {ticker}: {str(e)}')
                continue
        
        if not individual_results:
            raise InsufficientDataError(ticker, ['valid_model_results'])
        
        # Calculate model weights
        model_weights = self._calculate_model_weights(individual_results, data)
        
        # Calculate weighted fair value
        weighted_sum = 0.0
        total_weight = 0.0
        
        for weight_info in model_weights:
            model_name = weight_info.model_name
            weight = weight_info.weight
            
            if model_name in individual_results:
                result = individual_results[model_name]
                if result.fair_value is not None:
                    weighted_sum += result.fair_value * weight
                    total_weight += weight
        
        if total_weight == 0:
            raise InsufficientDataError(ticker, ['weighted_fair_value'])
        
        fair_value = weighted_sum / total_weight
        
        # Calculate margin of safety using ensemble fair value
        current_price = data.get('info', {}).get('currentPrice')
        margin_of_safety = None
        if current_price and current_price > 0:
            margin_of_safety = (fair_value - current_price) / current_price
        
        # Determine ensemble confidence
        confidence = self._determine_ensemble_confidence(individual_results, model_weights)
        
        # Create ensemble result
        result = EnsembleResult(
            ticker=ticker,
            model=self.name,
            fair_value=fair_value,
            current_price=current_price,
            margin_of_safety=margin_of_safety,
            confidence=confidence,
            constituent_models=list(individual_results.keys()),
            model_weights=model_weights,
            individual_results=individual_results,
            consensus_metrics={}
        )
        
        # Add input/output details
        result.inputs = {
            'current_price': current_price,
            'models_attempted': len(selected_models),
            'models_successful': len(individual_results),
            'model_selection_strategy': self.model_selection,
        }
        
        result.outputs = {
            'weighted_fair_value': fair_value,
            'total_weight': total_weight,
            'model_count': len(individual_results),
            'constituent_models': list(individual_results.keys()),
            'individual_valuations': {name: result.fair_value for name, result in individual_results.items()},
        }
        
        return result
    
    def _select_models(self, ticker: str, data: Dict[str, Any]) -> List[str]:
        """Select which models to use for this company."""
        
        if self.model_selection == 'all':
            # Use all available models
            from . import model_registry
            return model_registry.get_available_models()
        
        elif self.model_selection == 'recommended':
            # Use registry's recommendations
            from . import model_registry
            return model_registry._registry.get_model_recommendations(ticker, data)
        
        else:  # 'auto' - intelligent selection
            return self._auto_select_models(ticker, data)
    
    def _auto_select_models(self, ticker: str, data: Dict[str, Any]) -> List[str]:
        """Intelligently select models based on company characteristics."""
        
        info = data.get('info', {})
        sector = info.get('sector', '').lower()
        industry = info.get('industry', '').lower()
        market_cap = info.get('marketCap', 0)
        
        selected_models = []
        
        # Always include simple ratios for baseline
        selected_models.append('simple_ratios')
        
        # Sector-specific models (high priority)
        if any(keyword in sector or keyword in industry 
               for keyword in ['reit', 'real estate']):
            selected_models.append('reit')
            
        elif any(keyword in sector or keyword in industry 
                 for keyword in ['bank', 'financial services', 'commercial banking']):
            selected_models.append('bank')
            
        elif any(keyword in sector or keyword in industry 
                 for keyword in ['technology', 'software', 'internet', 'computer']):
            selected_models.append('tech')
            
        elif any(keyword in sector or keyword in industry 
                 for keyword in ['utilities', 'utility', 'electric', 'gas', 'power']):
            selected_models.append('utility')
        
        # DCF models based on company size and cash flow
        if self._has_positive_cash_flow(data):
            # Check for growth/reinvestment characteristics first
            if self._is_reinvestment_heavy(data):
                selected_models.append('growth_dcf')
            
            if market_cap > 10_000_000_000:  # Large cap
                selected_models.extend(['dcf_enhanced', 'dcf'])
            elif market_cap > 1_000_000_000:  # Mid cap
                selected_models.extend(['dcf', 'multi_stage_dcf'])
            else:  # Small cap - more growth-focused
                selected_models.append('multi_stage_dcf')
        
        # RIM for companies with stable ROE
        if self._has_stable_roe(data):
            selected_models.append('rim')
        
        return list(set(selected_models))  # Remove duplicates
    
    def _calculate_model_weights(self, individual_results: Dict[str, ValuationResult], 
                                data: Dict[str, Any]) -> List[ModelWeight]:
        """Calculate weights for each model based on various factors."""
        
        model_weights = []
        
        for model_name, result in individual_results.items():
            # Base weight from model confidence
            confidence_weights = {'high': 1.0, 'medium': 0.7, 'low': 0.4}
            base_weight = confidence_weights.get(result.confidence, 0.5)
            
            # Adjust weight based on model type and company characteristics
            type_weight = self._get_model_type_weight(model_name, data)
            
            # Adjust for result reasonableness
            reasonableness_weight = self._assess_result_reasonableness(result, data)
            
            # Final weight is product of all factors
            final_weight = base_weight * type_weight * reasonableness_weight
            
            # Determine reason for weight
            reason = self._explain_weight_assignment(model_name, base_weight, 
                                                   type_weight, reasonableness_weight)
            
            model_weights.append(ModelWeight(
                model_name=model_name,
                weight=final_weight,
                confidence=result.confidence,
                reason=reason
            ))
        
        # Normalize weights to sum to 1.0
        total_weight = sum(w.weight for w in model_weights)
        if total_weight > 0:
            for weight_info in model_weights:
                weight_info.weight = weight_info.weight / total_weight
        
        return model_weights
    
    def _get_model_type_weight(self, model_name: str, data: Dict[str, Any]) -> float:
        """Get weight multiplier based on model type suitability."""
        
        info = data.get('info', {})
        sector = info.get('sector', '').lower()
        
        # Sector-specific models get higher weights for their sectors
        if model_name == 'reit' and 'real estate' in sector:
            return 1.3
        elif model_name == 'bank' and ('financial' in sector or 'bank' in sector):
            return 1.3
        elif model_name == 'tech' and 'technology' in sector:
            return 1.3
        elif model_name == 'utility' and 'utilit' in sector:
            return 1.3
        
        # Growth-Adjusted DCF gets highest weight for reinvestment-heavy companies
        elif model_name == 'growth_dcf' and self._is_reinvestment_heavy(data):
            return 1.4  # Highest weight - this is exactly what it's designed for
        
        # DCF models get higher weight for profitable companies
        elif model_name.startswith('dcf') and self._has_positive_cash_flow(data):
            return 1.2
        
        # RIM gets higher weight for stable companies
        elif model_name == 'rim' and self._has_stable_roe(data):
            return 1.1
        
        # Simple ratios - always moderate weight
        elif model_name == 'simple_ratios':
            return 0.8  # Lower weight as it's more of a baseline
        
        return 1.0  # Default weight
    
    def _assess_result_reasonableness(self, result: ValuationResult, 
                                    data: Dict[str, Any]) -> float:
        """Assess how reasonable a valuation result is."""
        
        if not result.fair_value or not result.current_price:
            return 0.5  # Neutral weight if missing data
        
        # Check for extreme valuations
        price_ratio = result.fair_value / result.current_price
        
        # Very extreme valuations get lower weight
        if price_ratio > 10 or price_ratio < 0.1:
            return 0.3  # Very low weight for extreme results
        elif price_ratio > 5 or price_ratio < 0.2:
            return 0.6  # Reduced weight for large deviations
        elif price_ratio > 3 or price_ratio < 0.33:
            return 0.8  # Slight reduction for moderate deviations
        else:
            return 1.0  # Full weight for reasonable results
    
    def _explain_weight_assignment(self, model_name: str, base_weight: float,
                                 type_weight: float, reasonableness_weight: float) -> str:
        """Generate human-readable explanation of weight assignment."""
        
        reasons = []
        
        if base_weight >= 0.9:
            reasons.append("high model confidence")
        elif base_weight >= 0.6:
            reasons.append("medium model confidence")
        else:
            reasons.append("low model confidence")
        
        if type_weight > 1.0:
            reasons.append("sector specialization bonus")
        elif type_weight < 1.0:
            reasons.append("generic model penalty")
        
        if reasonableness_weight < 0.8:
            reasons.append("extreme valuation penalty")
        
        return "; ".join(reasons)
    
    def _determine_ensemble_confidence(self, individual_results: Dict[str, ValuationResult],
                                     model_weights: List[ModelWeight]) -> str:
        """Determine overall confidence based on constituent models."""
        
        # Count models by confidence level
        high_confidence_count = sum(1 for r in individual_results.values() 
                                   if r.confidence == 'high')
        medium_confidence_count = sum(1 for r in individual_results.values() 
                                     if r.confidence == 'medium')
        total_models = len(individual_results)
        
        # Check agreement between models (coefficient of variation)
        fair_values = [r.fair_value for r in individual_results.values() 
                      if r.fair_value is not None]
        
        agreement_penalty = 0
        if len(fair_values) > 1:
            cv = np.std(fair_values) / np.mean(fair_values) if np.mean(fair_values) > 0 else 0
            if cv > 0.5:  # High disagreement
                agreement_penalty = 1
            elif cv > 0.3:  # Moderate disagreement
                agreement_penalty = 0.5
        
        # Determine base confidence
        if total_models >= 4 and high_confidence_count >= 2:
            base_confidence = 'high'
        elif total_models >= 3 and (high_confidence_count >= 1 or medium_confidence_count >= 2):
            base_confidence = 'medium'
        elif total_models >= 2:
            base_confidence = 'medium'
        else:
            base_confidence = 'low'
        
        # Apply agreement penalty
        if agreement_penalty >= 1:
            if base_confidence == 'high':
                return 'medium'
            elif base_confidence == 'medium':
                return 'low'
        elif agreement_penalty >= 0.5:
            if base_confidence == 'high':
                return 'medium'
        
        return base_confidence
    
    def _has_positive_cash_flow(self, data: Dict[str, Any]) -> bool:
        """Check if company has positive free cash flow."""
        try:
            cashflow = data.get('cashflow')
            if cashflow is None or cashflow.empty:
                return False
            
            if 'Total Cash From Operating Activities' in cashflow.index:
                ocf = cashflow.loc['Total Cash From Operating Activities'].iloc[0] if len(cashflow.columns) > 0 else None
                return ocf is not None and ocf > 0
            
            return False
        except:
            return False
    
    def _has_stable_roe(self, data: Dict[str, Any]) -> bool:
        """Check if company has stable ROE suitable for RIM."""
        try:
            info = data.get('info', {})
            roe = info.get('returnOnEquity')
            return roe is not None and 0.05 < roe < 0.3
        except:
            return False
    
    def _is_reinvestment_heavy(self, data: Dict[str, Any]) -> bool:
        """Check if company is reinvestment-heavy and suitable for Growth-Adjusted DCF."""
        try:
            info = data.get('info', {})
            cashflow = data.get('cashflow')
            financials = data.get('financials')
            
            # Check 1: High CapEx intensity (>3% of revenue)
            if cashflow is not None and not cashflow.empty and financials is not None and not financials.empty:
                try:
                    if 'Capital Expenditures' in cashflow.index and 'Total Revenue' in financials.index:
                        capex = abs(cashflow.loc['Capital Expenditures'].iloc[0])
                        revenue = financials.loc['Total Revenue'].iloc[0]
                        if revenue > 0:
                            capex_intensity = capex / revenue
                            if capex_intensity > 0.03:  # >3% CapEx/Revenue
                                return True
                except:
                    pass
            
            # Check 2: Industry characteristics (known reinvestment-heavy sectors)
            sector = info.get('sector', '').lower()
            industry = info.get('industry', '').lower()
            
            reinvestment_keywords = [
                'e-commerce', 'retail', 'fulfillment', 'logistics', 'transportation',
                'manufacturing', 'automotive', 'electric vehicles', 'energy',
                'data center', 'cloud', 'infrastructure', 'telecom',
                'materials', 'mining', 'oil', 'pipeline'
            ]
            
            if any(keyword in sector or keyword in industry for keyword in reinvestment_keywords):
                return True
            
            # Check 3: Specific company indicators (Amazon, Tesla, etc.)
            ticker = info.get('symbol', '').lower()
            
            if ticker in ['amzn', 'tsla', 'nflx', 'sbux', 'wmt', 'tgt', 'hd', 'low', 'cost', 
                         'meta', 'googl', 'goog', 'msft', 'aapl']:
                return True
            
            return False
            
        except:
            return False