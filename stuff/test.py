import pandas as pd
import plotly.express as px

# Simulated Treasury yield data
data = {
    'Date': ['2025-06-10', '2025-06-11', '2025-06-12'],
    '1 Mo': [4.25, 4.23, 4.20],
    '3 Mo': [4.35, 4.33, 4.31],
    '6 Mo': [4.55, 4.52, 4.49],
    '1 Yr': [4.65, 4.60, 4.55],
    '2 Yr': [4.10, 4.08, 4.05],
    '3 Yr': [3.90, 3.88, 3.85],
    '5 Yr': [4.00, 3.98, 3.95],
    '7 Yr': [4.20, 4.18, 4.15],
    '10 Yr': [4.40, 4.38, 4.35],
    '20 Yr': [4.80, 4.78, 4.75],
    '30 Yr': [4.75, 4.72, 4.70],
}

df = pd.DataFrame(data)

# Convert to long format for 3D plot
df_long = df.melt(id_vars='Date', var_name='Maturity', value_name='Rate')

# Plot 3D yield surface
fig = px.line_3d(df_long, x='Date', y='Maturity', z='Rate', title='3D Yield Curve Over Time')
fig.update_traces(marker=dict(size=3))
fig.update_layout(scene=dict(zaxis_title='Rate (%)'))

fig.show()
