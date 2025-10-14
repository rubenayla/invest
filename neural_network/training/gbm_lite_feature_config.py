"""
GBM Lite Feature Configuration - Reduced requirements for stocks with limited history.

This is a lightweight version of GBM that requires only 4-6 quarters of data:
- Reduced lag periods: [1, 2] instead of [1, 2, 4, 8]
- Reduced rolling windows: [4] instead of [4, 8, 12]
- Same base features for consistency

Use this for stocks that don't have 8-12 quarters of historical data.
"""

# Same fundamental features as full GBM
FUNDAMENTAL_FEATURES = [
    # Profitability
    'profit_margins',
    'operating_margins',
    'gross_margins',

    # Returns
    'return_on_equity',
    'return_on_assets',

    # Growth
    'revenue_growth',
    'earnings_growth',

    # Balance Sheet Strength
    'current_ratio',
    'quick_ratio',
    'debt_to_equity',

    # Valuation Multiples
    'pe_ratio',
    'pb_ratio',
    'ps_ratio',
    'enterprise_to_ebitda',
    'enterprise_to_revenue',

    # Dividends
    'dividend_yield',
    'payout_ratio',

    # Company Characteristics
    'market_cap',  # Will be log-transformed
    'beta',
]

# Market regime features
MARKET_FEATURES = [
    'vix',
    'treasury_10y',
]

# Price-based momentum features (computed from price_history)
PRICE_FEATURES = [
    'returns_1m',
    'returns_3m',
    'returns_6m',
    'returns_1y',
    'volatility',
    'volume_trend',
]

# Absolute fundamental metrics (for computing yields)
CASHFLOW_FEATURES = [
    'free_cashflow',
    'operating_cashflow',
    'trailing_eps',
    'book_value',
]

# All base features to engineer
BASE_FEATURES = FUNDAMENTAL_FEATURES + MARKET_FEATURES + PRICE_FEATURES

# LITE CONFIGURATION: Reduced requirements
LAG_PERIODS = [1, 2]  # Only 2 quarters back (reduced from [1, 2, 4, 8])
ROLLING_WINDOWS = [4]  # Only 4-quarter windows (reduced from [4, 8, 12])
ROLLING_STATS = ['mean', 'std', 'slope']

# Minimum quarters needed for this configuration
MIN_QUARTERS_REQUIRED = 4  # Need at least 4 quarters for 4Q rolling windows

# Categorical features
CATEGORICAL_FEATURES = ['sector']


def get_all_feature_names():
    """
    Get complete list of all feature names after engineering.

    Returns
    -------
    list
        List of all feature column names in order
    """
    features = []

    # Base features
    features.extend(BASE_FEATURES)

    # Computed yields (created from cashflow features)
    features.extend(['fcf_yield', 'ocf_yield', 'earnings_yield'])

    # Log-transformed market cap
    features.append('log_market_cap')

    # Engineered features for each base feature
    for feat in BASE_FEATURES:
        # Lags (only 1Q, 2Q)
        for lag in LAG_PERIODS:
            features.append(f'{feat}_lag{lag}q')

        # Changes (QoQ, YoY)
        features.append(f'{feat}_qoq')
        features.append(f'{feat}_yoy')

        # Rolling statistics (only 4Q windows)
        for window in ROLLING_WINDOWS:
            for stat in ROLLING_STATS:
                features.append(f'{feat}_{stat}{window}q')

        # Missingness flag
        features.append(f'{feat}_missing')

    # Categorical
    features.extend(CATEGORICAL_FEATURES)

    return features


def get_snapshot_query_columns():
    """
    Get SQL columns needed from snapshots table.

    Returns
    -------
    list
        List of column names to query
    """
    return (
        ['ticker', 'snapshot_date', 'snapshot_id', 'sector'] +
        FUNDAMENTAL_FEATURES +
        MARKET_FEATURES +
        CASHFLOW_FEATURES
    )


def get_min_quarters_required():
    """
    Get minimum quarters needed for GBM Lite.

    Returns
    -------
    int
        Minimum number of quarters required
    """
    # Need enough for:
    # - Current quarter (1)
    # - Lag 2Q (2)
    # - 4Q rolling window with min_periods=2 (practically 4)
    return MIN_QUARTERS_REQUIRED
