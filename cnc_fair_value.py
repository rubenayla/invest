#!/usr/bin/env python
"""
Calculate fair value for CNC using multiple methods
Focus on post-ACA adjustment reality
"""

import yfinance as yf
import numpy as np
import pandas as pd


def calculate_cnc_fair_value():
    """Calculate CNC fair value using multiple approaches"""
    
    cnc = yf.Ticker('CNC')
    info = cnc.info
    
    print("="*80)
    print("CNC FAIR VALUE ANALYSIS - POST ACA ADJUSTMENT")
    print("="*80)
    
    current_price = info.get('currentPrice', 28.99)
    shares_outstanding = info.get('sharesOutstanding', 490e6)
    
    # Key metrics
    ttm_revenue = info.get('totalRevenue', 159.6e9)
    ttm_fcf = info.get('freeCashflow', 1.54e9)
    book_value = info.get('bookValue', 55.77)
    tangible_book = book_value  # Assume minimal intangibles for insurer
    
    print(f"Current Price: ${current_price:.2f}")
    print(f"TTM Revenue: ${ttm_revenue/1e9:.1f}B")
    print(f"TTM FCF: ${ttm_fcf/1e9:.1f}B")
    print(f"Book Value: ${book_value:.2f}")
    
    # Method 1: Adjusted P/B based on normalized ROE
    print(f"\n1. PRICE-TO-BOOK VALUATION")
    print("-" * 40)
    
    # Managed care companies typically trade at 1.0-2.0x book value
    # CNC's efficiency issues suggest lower multiple
    normalized_pb_multiple = 0.8  # Conservative due to efficiency concerns
    pb_fair_value = tangible_book * normalized_pb_multiple
    
    print(f"Book Value per Share: ${book_value:.2f}")
    print(f"Normalized P/B Multiple: {normalized_pb_multiple:.1f}x")
    print(f"P/B Fair Value: ${pb_fair_value:.2f}")
    print(f"Upside/Downside: {((pb_fair_value - current_price) / current_price * 100):+.1f}%")
    
    # Method 2: Revenue Multiple (Post-adjustment)
    print(f"\n2. REVENUE MULTIPLE VALUATION")
    print("-" * 40)
    
    # Adjust for $1.8B revenue hit
    adjusted_revenue = ttm_revenue - 1.8e9  # Remove the ACA adjustment hit
    revenue_per_share = adjusted_revenue / shares_outstanding
    
    # Managed care typically trades at 0.3-0.8x revenue
    # CNC's issues suggest lower multiple
    normalized_ps_multiple = 0.4  # Conservative
    ps_fair_value = revenue_per_share * normalized_ps_multiple
    
    print(f"Adjusted Revenue: ${adjusted_revenue/1e9:.1f}B")
    print(f"Revenue per Share: ${revenue_per_share:.2f}")
    print(f"Normalized P/S Multiple: {normalized_ps_multiple:.1f}x")
    print(f"P/S Fair Value: ${ps_fair_value:.2f}")
    print(f"Upside/Downside: {((ps_fair_value - current_price) / current_price * 100):+.1f}%")
    
    # Method 3: Earnings Multiple (Forward-looking)
    print(f"\n3. NORMALIZED EARNINGS VALUATION")
    print("-" * 40)
    
    # Estimate normalized earnings post-adjustment
    # Assume company can achieve 3% net margin (industry average)
    normalized_net_margin = 0.03
    normalized_earnings = adjusted_revenue * normalized_net_margin
    normalized_eps = normalized_earnings / shares_outstanding
    
    # Managed care P/E typically 10-15x
    normalized_pe_multiple = 12  # Mid-range
    pe_fair_value = normalized_eps * normalized_pe_multiple
    
    print(f"Normalized Net Margin: {normalized_net_margin*100:.1f}%")
    print(f"Normalized Earnings: ${normalized_earnings/1e9:.1f}B")
    print(f"Normalized EPS: ${normalized_eps:.2f}")
    print(f"Normalized P/E Multiple: {normalized_pe_multiple:.1f}x")
    print(f"P/E Fair Value: ${pe_fair_value:.2f}")
    print(f"Upside/Downside: {((pe_fair_value - current_price) / current_price * 100):+.1f}%")
    
    # Method 4: Peer Comparison
    print(f"\n4. PEER COMPARISON VALUATION")
    print("-" * 40)
    
    # Get peer multiples
    peers = ['UNH', 'CVS', 'HUM', 'MOH']
    peer_multiples = []
    
    for peer in peers:
        try:
            peer_stock = yf.Ticker(peer)
            peer_info = peer_stock.info
            peer_pb = peer_info.get('priceToBook', 0)
            peer_ps = peer_info.get('priceToSalesTrailing12Months', 0)
            
            if peer_pb > 0 and peer_ps > 0:
                peer_multiples.append({
                    'ticker': peer,
                    'pb': peer_pb,
                    'ps': peer_ps
                })
                print(f"{peer}: P/B={peer_pb:.2f}, P/S={peer_ps:.2f}")
        except:
            continue
    
    if peer_multiples:
        avg_pb = np.mean([p['pb'] for p in peer_multiples])
        avg_ps = np.mean([p['ps'] for p in peer_multiples])
        
        # Apply discount for CNC's efficiency issues
        discount = 0.7  # 30% discount
        discounted_pb = avg_pb * discount
        discounted_ps = avg_ps * discount
        
        peer_pb_value = book_value * discounted_pb
        peer_ps_value = revenue_per_share * discounted_ps
        
        print(f"\nPeer Average P/B: {avg_pb:.2f}")
        print(f"Discounted P/B (30% off): {discounted_pb:.2f}")
        print(f"Peer P/B Fair Value: ${peer_pb_value:.2f}")
        
        print(f"\nPeer Average P/S: {avg_ps:.2f}")
        print(f"Discounted P/S (30% off): {discounted_ps:.2f}")
        print(f"Peer P/S Fair Value: ${peer_ps_value:.2f}")
    
    # Method 5: Liquidation/Asset Value
    print(f"\n5. ASSET VALUE ANALYSIS")
    print("-" * 40)
    
    total_assets = info.get('totalAssets', 0)
    total_liabilities = info.get('totalLiab', 0)
    
    if total_assets and total_liabilities:
        net_assets = total_assets - total_liabilities
        asset_value_per_share = net_assets / shares_outstanding
        
        # Insurance companies often trade near book value in distress
        print(f"Total Assets: ${total_assets/1e9:.1f}B")
        print(f"Total Liabilities: ${total_liabilities/1e9:.1f}B")
        print(f"Net Assets: ${net_assets/1e9:.1f}B")
        print(f"Asset Value per Share: ${asset_value_per_share:.2f}")
    
    # Summary and recommendation
    print(f"\n" + "="*80)
    print("FAIR VALUE SUMMARY")
    print("="*80)
    
    fair_values = []
    if 'pb_fair_value' in locals(): fair_values.append(pb_fair_value)
    if 'ps_fair_value' in locals(): fair_values.append(ps_fair_value)
    if 'pe_fair_value' in locals(): fair_values.append(pe_fair_value)
    if 'peer_pb_value' in locals() and peer_pb_value > 0: fair_values.append(peer_pb_value)
    if 'peer_ps_value' in locals() and peer_ps_value > 0: fair_values.append(peer_ps_value)
    
    if fair_values:
        average_fair_value = np.mean(fair_values)
        median_fair_value = np.median(fair_values)
        
        print(f"Current Price: ${current_price:.2f}")
        print(f"Average Fair Value: ${average_fair_value:.2f}")
        print(f"Median Fair Value: ${median_fair_value:.2f}")
        print(f"Fair Value Range: ${min(fair_values):.2f} - ${max(fair_values):.2f}")
        
        avg_upside = ((average_fair_value - current_price) / current_price * 100)
        median_upside = ((median_fair_value - current_price) / current_price * 100)
        
        print(f"\nAverage Fair Value Upside: {avg_upside:+.1f}%")
        print(f"Median Fair Value Upside: {median_upside:+.1f}%")
        
        # Risk assessment
        print(f"\n" + "="*80)
        print("RISK ASSESSMENT")
        print("="*80)
        
        print("🔴 HIGH RISKS:")
        print("• Operational inefficiency demonstrated by ACA adjustment")
        print("• Medical loss ratio management challenges")
        print("• Regulatory and compliance risks")
        print("• Continued membership quality issues")
        
        print("\n🟡 MODERATE RISKS:")
        print("• High debt levels (D/E = 64)")
        print("• Competitive pressure from UNH, others")
        print("• Healthcare policy changes")
        
        print("\n🟢 POSITIVE FACTORS:")
        print("• Trading near 5-year lows")
        print("• Medicaid expansion opportunities")
        print("• Scale advantages")
        print("• Potential for operational improvements")
        
        # Investment recommendation
        if avg_upside > 50:
            recommendation = "SPECULATIVE BUY - High risk, high reward"
        elif avg_upside > 20:
            recommendation = "CAUTIOUS BUY - Wait for efficiency improvements"
        elif avg_upside > 0:
            recommendation = "HOLD - Monitor operational metrics"
        else:
            recommendation = "AVOID - Efficiency concerns outweigh value"
            
        print(f"\n🎯 RECOMMENDATION: {recommendation}")
        
        return {
            'current_price': current_price,
            'fair_values': fair_values,
            'average_fair_value': average_fair_value,
            'median_fair_value': median_fair_value,
            'upside': avg_upside
        }


if __name__ == "__main__":
    result = calculate_cnc_fair_value()