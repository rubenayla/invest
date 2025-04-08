from invest.dcf import calculate_dcf

# Full auto mode
calculate_dcf("SQM")

# Override some values
calculate_dcf("TSLA", discount_rate=0.10)

# Override all for full control
calculate_dcf(
    "MITSY",
    fcf=2.4e9,
    shares=220_000_000,
    cash=3e9,
    debt=1.5e9,
    current_price=95.0,
    growth_rates=[0.12] * 10,
    discount_rate=0.11,
    terminal_growth=0.02,
)
