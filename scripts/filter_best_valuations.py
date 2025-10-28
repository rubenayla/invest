#!/usr/bin/env python3
"""
Filter the previous analysis to show ONLY the value stocks we screened,
ranked by DCF upside.
"""

# Original 67 SAFE stocks (excluding Starlink/Tesla disruption)
SAFE_STOCKS = [
    'KB', 'MOH', 'SYF', 'VALE', 'EMN', 'TAP', 'ACGL', '9022.T', 'PHM', 'BG',
    'MOS', 'HPQ', 'SAN', 'RIO', 'CAG', 'TRV', 'RF', 'USB', 'UHS', 'HBAN',
    'MTB', 'MT', 'TFC', 'CB', 'PNC', '6752.T', 'VICI', 'MIN', 'STT', '8031.T',
    'FITB', 'MO', 'DVA', 'LEN', 'SMFG', 'DHI', 'PFE', '8316.T', 'CFR', 'MET',
    'CINF', '8411.T', 'C', 'MUFG', 'WFC', 'ELV', 'BAC', 'BIIB', 'APT', 'CFG',
    'NTRS', 'NVO', 'AIG', 'GPN', '8058.T', 'AIZ', 'BK', 'L', 'PFG', 'SNY',
    'MTCH', '4612.T', 'MHK', 'HRL', 'DIS', 'HST', 'TXT',
]

# Energy stocks (18 removed for disruption risk)
ENERGY_STOCKS = [
    'CMCSA', 'T', 'DVN', 'APA', 'TTE', 'WDS', 'FANG', 'CTRA', 'COP', 'SU',
    'SLB', 'EQT', 'XOM', '7203.T', '7267.T', '9432.T', 'FOX', 'LKQ',
]

# DCF Results from previous run (manually extracted)
DCF_RESULTS = [
    ('SMFG', 'Sumitomo Mitsui Financial Gro', 15.20, 204630, 'Financial Services'),
    ('MUFG', 'Mitsubishi UFJ Financial Grou', 14.62, 44255, 'Financial Services'),
    ('NVO', 'Novo Nordisk A/S', 56.93, 5204, 'Healthcare'),
    ('FOX', 'Fox Corporation', 52.78, 2388, 'Communication Services'),
    ('ACGL', 'Arch Capital Group Ltd.', 87.17, 2041, 'Financial Services'),
    ('TRV', 'The Travelers Companies, Inc.', 268.25, 1523, 'Financial Services'),
    ('SYF', 'Synchrony Financial', 73.21, 1331, 'Financial Services'),
    ('8316.T', 'SUMITOMO MITSUI FINANCIAL GRO', 3991.00, 1200, 'Financial Services'),
    ('CB', 'Chubb Limited', 280.63, 1156, 'Financial Services'),
    ('AIZ', 'Assurant, Inc.', 210.08, 979, 'Financial Services'),
    ('PFG', 'Principal Financial Group Inc', 79.25, 958, 'Financial Services'),
    ('CTRA', 'Coterra Energy Inc.', 23.46, 838, 'Energy'),
    ('CINF', 'Cincinnati Financial Corporat', 155.41, 776, 'Financial Services'),
    ('MTB', 'M&T Bank Corporation', 182.31, 696, 'Financial Services'),
    ('PFE', 'Pfizer, Inc.', 24.61, 679, 'Healthcare'),
    ('CAG', 'ConAgra Brands, Inc.', 18.48, 650, 'Consumer Defensive'),
    ('BIIB', 'Biogen Inc.', 148.30, 574, 'Healthcare'),
    ('CMCSA', 'Comcast Corporation', 29.29, 556, 'Communication Services'),
    ('PNC', 'PNC Financial Services Group', 181.65, 461, 'Financial Services'),
    ('USB', 'U.S. Bancorp', 47.28, 426, 'Financial Services'),
    ('MET', 'MetLife, Inc.', 78.35, 361, 'Financial Services'),
    ('HPQ', 'HP Inc.', 27.86, 352, 'Technology'),
    ('CFG', 'Citizens Financial Group, Inc', 50.97, 340, 'Financial Services'),
    ('ELV', 'Elevance Health, Inc.', 345.00, 333, 'Healthcare'),
    ('HBAN', 'Huntington Bancshares Incorpo', 15.87, 304, 'Financial Services'),
    ('UHS', 'Universal Health Services, In', 208.61, 289, 'Healthcare'),
    ('CFR', 'Cullen/Frost Bankers, Inc.', 122.83, 289, 'Financial Services'),
    ('L', 'Loews Corporation', 99.56, 223, 'Financial Services'),
    ('MOH', 'Molina Healthcare Inc', 155.92, 172, 'Healthcare'),
    ('FITB', 'Fifth Third Bancorp', 41.83, 143, 'Financial Services'),
]


def main():
    print('📊 DCF Valuations for Our Screened Value Stocks\n')

    # Filter to only safe stocks
    print('=' * 100)
    print('✅ SAFE STOCKS (No Starlink/Tesla disruption risk)\n')
    print(f'{"Ticker":<10} {"Name":<35} {"Price":<10} {"DCF↑%":<10} {"Sector":<25}')
    print('=' * 100)

    safe_with_dcf = [r for r in DCF_RESULTS if r[0] in SAFE_STOCKS]

    for ticker, name, price, upside, sector in safe_with_dcf:
        print(f'{ticker:<10} {name[:34]:<35} ${price:<9.2f} {upside:<10.0f} {sector:<25}')

    print(f'\n✅ Found {len(safe_with_dcf)} safe stocks with DCF valuations')

    # Show energy stocks separately
    print('\n' + '=' * 100)
    print('⚠️  ENERGY/DISRUPTION RISK STOCKS (Removed earlier for Starlink/Tesla)\n')
    print(f'{"Ticker":<10} {"Name":<35} {"Price":<10} {"DCF↑%":<10} {"Sector":<25}')
    print('=' * 100)

    energy_with_dcf = [r for r in DCF_RESULTS if r[0] in ENERGY_STOCKS]

    for ticker, name, price, upside, sector in energy_with_dcf:
        print(f'{ticker:<10} {name[:34]:<35} ${price:<9.2f} {upside:<10.0f} {sector:<25}')

    print(f'\n⚠️  Found {len(energy_with_dcf)} disruption-risk stocks with DCF valuations')

    # Top recommendations
    print('\n' + '=' * 100)
    print('🏆 TOP 10 RECOMMENDATIONS (Safe stocks with highest DCF upside)\n')

    top_10 = sorted(safe_with_dcf, key=lambda x: x[3], reverse=True)[:10]

    for i, (ticker, name, price, upside, sector) in enumerate(top_10, 1):
        print(f'{i:2}. {ticker:<8} ({sector:<20}) - {upside:>6.0f}% upside at ${price:.2f}')

    print('\n💡 Key Observations:')
    print('  • Financial Services dominate top picks (banks, insurance)')
    print('  • Healthcare has strong representation (NVO, PFE, BIIB, MOH)')
    print('  • Consumer Defensive: CAG with 650% upside')
    print('  • Extreme valuations (>1000%) may indicate data issues - focus on 100-700% range')


if __name__ == '__main__':
    main()
