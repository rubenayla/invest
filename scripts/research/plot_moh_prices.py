import yfinance as yf
import matplotlib.pyplot as plt

# Fetch MOH data from 2005 to 2015
ticker = yf.Ticker('MOH')
hist = ticker.history(start='2005-01-01', end='2015-12-31')

# Create the plot
plt.figure(figsize=(12, 6))
plt.plot(hist.index, hist['Close'], linewidth=2)
plt.title('MOH (Molina Healthcare) Stock Price: 2005-2015', fontsize=14, fontweight='bold')
plt.xlabel('Year', fontsize=12)
plt.ylabel('Price ($)', fontsize=12)
plt.grid(True, alpha=0.3)
plt.tight_layout()

# Show the plot
plt.show()

# Print some summary statistics
print(f'\nMOH Price Summary (2005-2015):')
print(f'Starting Price (2005): ${hist["Close"].iloc[0]:.2f}')
print(f'Ending Price (2015): ${hist["Close"].iloc[-1]:.2f}')
print(f'Highest Price: ${hist["Close"].max():.2f}')
print(f'Lowest Price: ${hist["Close"].min():.2f}')
print(f'Total Return: {((hist["Close"].iloc[-1] / hist["Close"].iloc[0]) - 1) * 100:.1f}%')
