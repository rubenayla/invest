from invest.dcf import calculate_dcf

print("==================================================")
print("Auto Mode DCF Valuation for SQM:")
print("==================================================")
auto_sqm = calculate_dcf("SQM", verbose=True)

print("\n==================================================")
print("Auto Mode DCF Valuation for TSLA:")
print("==================================================")
auto_tsla = calculate_dcf("TSLA", discount_rate=0.10, verbose=True)

print("\n==================================================")
print("Manual Mode DCF Valuation for FOOCORP (Dummy Company):")
print("==================================================")
manual_foocorp = calculate_dcf(
    "FOOCORP",            # Dummy ticker; market data won't be found.
    fcf=1.5e9,           # Manual override of normalized FCF
    shares=150_000_000,  # Manual shares outstanding
    cash=500e6,          # Manual cash
    debt=800e6,          # Manual debt
    current_price=50.0,  # Manual current price
    growth_rates=[0.05, 0.05, 0.04, 0.04, 0.03, 0.03, 0.02, 0.02, 0.02, 0.02],
    discount_rate=0.10,
    terminal_growth=0.02,
    verbose=True
)

print("\n==================================================")
print("Manual Mode DCF Valuation for MITSY:")
print("==================================================")
manual_mitsy = calculate_dcf(
    "MITSY",
    fcf=2.4e9,
    shares=220_000_000,
    cash=3e9,
    debt=1.5e9,
    current_price=95.0,
    growth_rates=[0.08, 0.07, 0.06, 0.05, 0.05, 0.04, 0.04, 0.03, 0.03, 0.03],
    discount_rate=0.11,
    terminal_growth=0.02,
    verbose=True
)
