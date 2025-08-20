#!/usr/bin/env python
"""
Comprehensive analysis of Centene Corporation (CNC)
Focus on efficiency, valuation, and competitive position
"""

import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add src to path
sys.path.append('src')

from invest.dcf import calculate_dcf
from invest.dcf_enhanced import calculate_enhanced_dcf
from invest.simple_ratios import calculate_simple_ratios_valuation


def get_managed_care_peers():
    """Get managed care industry peers for comparison"""
    return {
        'CNC': 'Centene Corporation',
        'UNH': 'UnitedHealth Group',
        'ANTM': 'Anthem Inc',  # Now Elevance Health
        'CVS': 'CVS Health',
        'HUM': 'Humana Inc',
        'MOH': 'Molina Healthcare',
        'WCG': 'WellCare (acquired)',
        'CYH': 'Community Health Systems'  # Hospital operator for context
    }


def analyze_efficiency_metrics(ticker):
    """Analyze operational efficiency metrics specific to managed care"""
    stock = yf.Ticker(ticker)
    info = stock.info
    
    # Key managed care efficiency metrics
    metrics = {
        'medical_loss_ratio': None,  # Not directly available, need to calculate
        'operating_margin': info.get('operatingMargins', 0) * 100,
        'profit_margin': info.get('profitMargins', 0) * 100,
        'roe': info.get('returnOnEquity', 0) * 100,
        'roa': info.get('returnOnAssets', 0) * 100,
        'asset_turnover': info.get('totalRevenue', 0) / info.get('totalAssets', 1) if info.get('totalAssets') else None,
        'membership_growth': None,  # Would need historical data
        'revenue_per_member': None,  # Would need member count data
        'admin_cost_ratio': None  # Would need detailed income statement
    }
    
    # Get recent financial data for trend analysis
    try:
        financials = stock.quarterly_financials
        if not financials.empty:
            # Calculate some efficiency ratios
            revenues = financials.loc['Total Revenue'] if 'Total Revenue' in financials.index else None
            if revenues is not None and len(revenues) >= 4:
                # Revenue growth (quarterly)
                latest_q = revenues.iloc[0]
                year_ago_q = revenues.iloc[-1] if len(revenues) >= 4 else revenues.iloc[-1]
                revenue_growth = ((latest_q - year_ago_q) / year_ago_q * 100) if year_ago_q != 0 else None
                metrics['revenue_growth_yoy'] = revenue_growth
    except:
        pass
    
    return metrics


def get_industry_context():
    """Get managed care industry context and challenges"""
    context = {
        'aca_risk_adjustment': {
            'description': 'ACA Risk Adjustment Program redistributes funds based on member risk scores',
            'impact': 'Companies with healthier populations pay into program, those with sicker pay out',
            'cnc_issue': 'CNC received $1.8B due to underestimating member risk - suggests operational inefficiency'
        },
        'key_metrics': {
            'medical_loss_ratio': 'Medical costs / Premium revenue (target ~85%)',
            'admin_cost_ratio': 'Admin costs / Premium revenue (target ~15%)',
            'membership_growth': 'Growth in covered lives',
            'premium_per_member': 'Revenue efficiency per member'
        },
        'regulatory_environment': {
            'medicaid_expansion': 'Opportunities in new states',
            'medicare_advantage': 'Growing market for seniors',
            'aca_exchanges': 'Individual market participation'
        }
    }
    return context


def comparative_analysis():
    """Compare CNC to managed care peers"""
    peers = get_managed_care_peers()
    comparison_data = {}
    
    print("\n" + "="*80)
    print("MANAGED CARE PEER COMPARISON")
    print("="*80)
    
    for ticker, name in peers.items():
        if ticker == 'WCG' or ticker == 'ANTM':  # Skip acquired/renamed companies
            continue
            
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            comparison_data[ticker] = {
                'name': name,
                'market_cap': info.get('marketCap', 0) / 1e9,
                'pe_ratio': info.get('trailingPE', 0),
                'forward_pe': info.get('forwardPE', 0),
                'profit_margin': info.get('profitMargins', 0) * 100,
                'operating_margin': info.get('operatingMargins', 0) * 100,
                'roe': info.get('returnOnEquity', 0) * 100,
                'price_to_book': info.get('priceToBook', 0),
                'debt_to_equity': info.get('debtToEquity', 0),
                'current_price': info.get('currentPrice', 0)
            }
            
        except Exception as e:
            print(f"Error analyzing {ticker}: {e}")
            continue
    
    # Display comparison table
    if comparison_data:
        df = pd.DataFrame(comparison_data).T
        df = df.round(2)
        print(df.to_string())
    
    return comparison_data


def analyze_cnc_detailed():
    """Detailed analysis of Centene Corporation"""
    print("\n" + "="*80)
    print("CENTENE CORPORATION (CNC) - DETAILED ANALYSIS")
    print("="*80)
    
    stock = yf.Ticker('CNC')
    info = stock.info
    
    # Basic information
    print(f"\n📊 CURRENT METRICS:")
    print(f"Current Price: ${info.get('currentPrice', 0):.2f}")
    print(f"Market Cap: ${info.get('marketCap', 0)/1e9:.1f}B")
    print(f"Enterprise Value: ${info.get('enterpriseValue', 0)/1e9:.1f}B")
    print(f"Employees: {info.get('fullTimeEmployees', 'N/A'):,}")
    
    print(f"\n💰 VALUATION METRICS:")
    print(f"P/E Ratio (TTM): {info.get('trailingPE', 'N/A')}")
    print(f"Forward P/E: {info.get('forwardPE', 'N/A')}")
    print(f"Price/Book: {info.get('priceToBook', 'N/A')}")
    print(f"Price/Sales: {info.get('priceToSalesTrailing12Months', 'N/A')}")
    print(f"EV/Revenue: {(info.get('enterpriseValue', 0) / info.get('totalRevenue', 1)):.2f}")
    print(f"EV/EBITDA: {info.get('enterpriseToEbitda', 'N/A')}")
    
    print(f"\n⚡ EFFICIENCY METRICS:")
    print(f"Profit Margin: {info.get('profitMargins', 0)*100:.2f}%")
    print(f"Operating Margin: {info.get('operatingMargins', 0)*100:.2f}%")
    print(f"ROE: {info.get('returnOnEquity', 0)*100:.2f}%")
    print(f"ROA: {info.get('returnOnAssets', 0)*100:.2f}%")
    print(f"Asset Turnover: {info.get('totalRevenue', 0) / info.get('totalAssets', 1):.2f}x")
    
    print(f"\n🏗️ FINANCIAL STRENGTH:")
    print(f"Total Cash: ${info.get('totalCash', 0)/1e9:.1f}B")
    print(f"Total Debt: ${info.get('totalDebt', 0)/1e9:.1f}B")
    print(f"Debt/Equity: {info.get('debtToEquity', 0):.2f}")
    print(f"Current Ratio: {info.get('currentRatio', 'N/A')}")
    print(f"Quick Ratio: {info.get('quickRatio', 'N/A')}")
    
    print(f"\n📈 GROWTH & RETURNS:")
    print(f"Revenue Growth (YoY): {info.get('revenueGrowth', 0)*100:.2f}%")
    print(f"Earnings Growth (YoY): {info.get('earningsGrowth', 0)*100:.2f}%")
    print(f"Dividend Yield: {info.get('dividendYield', 0)*100:.2f}%")
    print(f"Beta: {info.get('beta', 'N/A')}")
    
    # Get historical performance
    try:
        hist = stock.history(period='2y', interval='1mo')
        if not hist.empty:
            current_price = hist['Close'].iloc[-1]
            price_1y_ago = hist['Close'].iloc[-13] if len(hist) >= 13 else hist['Close'].iloc[0]
            returns_1y = ((current_price - price_1y_ago) / price_1y_ago * 100)
            print(f"1-Year Return: {returns_1y:.1f}%")
            
            # Volatility
            daily_returns = hist['Close'].pct_change().dropna()
            volatility = daily_returns.std() * np.sqrt(252) * 100
            print(f"Annual Volatility: {volatility:.1f}%")
    except:
        pass
    
    return info


def run_valuation_models(ticker='CNC'):
    """Run multiple valuation models on CNC"""
    print("\n" + "="*80)
    print("VALUATION MODELS ANALYSIS")
    print("="*80)
    
    # DCF Valuation
    print("\n🔍 DISCOUNTED CASH FLOW (DCF) VALUATION:")
    print("-" * 50)
    try:
        dcf_result = calculate_dcf(ticker, verbose=True)
    except Exception as e:
        print(f"DCF Error: {e}")
        dcf_result = None
    
    # Enhanced DCF
    print("\n🔍 ENHANCED DCF VALUATION:")
    print("-" * 50)
    try:
        enhanced_dcf_result = calculate_enhanced_dcf(ticker, verbose=True)
    except Exception as e:
        print(f"Enhanced DCF Error: {e}")
        enhanced_dcf_result = None
    
    # Simple Ratios Valuation
    print("\n🔍 SIMPLE RATIOS VALUATION:")
    print("-" * 50)
    try:
        ratios_result = calculate_simple_ratios_valuation(ticker, verbose=True)
    except Exception as e:
        print(f"Simple Ratios Error: {e}")
        ratios_result = None
    
    return {
        'dcf': dcf_result,
        'enhanced_dcf': enhanced_dcf_result,
        'simple_ratios': ratios_result
    }


def main():
    """Run comprehensive CNC analysis"""
    print("="*80)
    print("CENTENE CORPORATION (CNC) - COMPREHENSIVE ANALYSIS")
    print("POST-ACA RISK ADJUSTMENT PAYMENT IMPACT")
    print("="*80)
    
    # Industry context
    print("\n🏥 INDUSTRY CONTEXT:")
    context = get_industry_context()
    print(f"ACA Risk Adjustment Issue: {context['aca_risk_adjustment']['cnc_issue']}")
    
    # Detailed company analysis
    cnc_info = analyze_cnc_detailed()
    
    # Efficiency analysis
    print("\n⚙️ EFFICIENCY ANALYSIS:")
    efficiency = analyze_efficiency_metrics('CNC')
    for metric, value in efficiency.items():
        if value is not None:
            if isinstance(value, float):
                print(f"{metric.replace('_', ' ').title()}: {value:.2f}{'%' if 'ratio' in metric or 'margin' in metric or 'roe' in metric or 'roa' in metric else ''}")
            else:
                print(f"{metric.replace('_', ' ').title()}: {value}")
    
    # Peer comparison
    peer_data = comparative_analysis()
    
    # Valuation models
    valuation_results = run_valuation_models('CNC')
    
    # Summary and recommendation
    print("\n" + "="*80)
    print("INVESTMENT THESIS SUMMARY")
    print("="*80)
    
    current_price = cnc_info.get('currentPrice', 0)
    
    print(f"\n📊 CURRENT SITUATION:")
    print(f"• Current Price: ${current_price:.2f}")
    print(f"• Market Cap: ${cnc_info.get('marketCap', 0)/1e9:.1f}B")
    print(f"• P/E Ratio: {cnc_info.get('trailingPE', 'N/A')}")
    
    print(f"\n⚠️ KEY CONCERNS:")
    print("• $1.8B ACA risk adjustment payment indicates operational inefficiency")
    print("• Company underestimated member risk profiles")
    print("• Suggests challenges in risk assessment and pricing")
    
    print(f"\n✅ POSITIVES:")
    print(f"• Operating Margin: {cnc_info.get('operatingMargins', 0)*100:.2f}%")
    print(f"• ROE: {cnc_info.get('returnOnEquity', 0)*100:.2f}%")
    print("• Medicaid expansion opportunities")
    print("• Large scale and market presence")
    
    # Investment recommendation based on analysis
    pe_ratio = cnc_info.get('trailingPE', 999)
    roe = cnc_info.get('returnOnEquity', 0) * 100
    profit_margin = cnc_info.get('profitMargins', 0) * 100
    
    print(f"\n🎯 INVESTMENT RECOMMENDATION:")
    if pe_ratio < 15 and roe > 15 and profit_margin > 3:
        print("ATTRACTIVE - Low valuation with reasonable efficiency metrics")
    elif pe_ratio < 20 and roe > 10:
        print("FAIR VALUE - Reasonably valued but monitor efficiency improvements")
    else:
        print("CAUTIOUS - Efficiency concerns and valuation questions remain")
    
    print(f"\n📈 KEY METRICS TO MONITOR:")
    print("• Medical Loss Ratio improvements")
    print("• Administrative cost control")
    print("• Risk adjustment accuracy")
    print("• Membership growth quality")
    print("• Regulatory compliance costs")


if __name__ == "__main__":
    main()