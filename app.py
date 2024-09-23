import json
from pathlib import Path
import yfinance as yf
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from stock_data import get_stock_history

# Set the title of the app
st.title('Investment Portfolio')

# Define the path to the JSON file
json_file_path = Path(__file__).parent / 'data' / 'investment_data.json'

# Open the JSON file and load its content
with open(json_file_path, 'r') as file:
    transactions_data = json.load(file)

# --- Process Transactions to Determine Current Holdings ---
holdings = {}
latest_average_costs = {}
for transaction in transactions_data:
    ticker = transaction["Ticker Symbol"]
    shares = float(transaction["No. of Shares"])
    transaction_type = transaction["Transaction Type"]
    avg_cost = float(transaction["Average Cost per Share USD"])

    if ticker not in holdings:
        holdings[ticker] = 0.0

    # Adjust shares based on transaction type
    holdings[ticker] += shares if transaction_type == "BUY" else -shares
    latest_average_costs[ticker] = avg_cost  # Update with the latest average cost

# Filter out stocks where holdings are zero or negative
holdings = {k: v for k, v in holdings.items() if v > 0.001}

# --- Calculate Current Values and Total Portfolio Value ---
current_values = {}
for ticker, shares in holdings.items():
    ticker_obj = yf.Ticker(ticker)
    try:
        # Attempt to get the current price
        current_price = None
        if hasattr(ticker_obj, 'fast_info') and ticker_obj.fast_info.get('lastPrice'):
            current_price = ticker_obj.fast_info['lastPrice']
        elif ticker_obj.info.get('regularMarketPrice'):
            current_price = ticker_obj.info['regularMarketPrice']
        else:
            # Fallback to using history data
            hist = ticker_obj.history(period='5d')  # Use '5d' to ensure data is available
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]

        if current_price is None:
            raise ValueError(f"Current price for {ticker} is unavailable.")

        current_value = current_price * shares
        current_values[ticker] = current_value
    except Exception as e:
        current_values[ticker] = 0.0
        st.error(f"Failed to retrieve price for {ticker}: {e}")

# Calculate total portfolio value
total_portfolio_value = sum(current_values.values())

# --- Display Overall Holdings at the Top ---
st.header('Overall Holdings')
st.subheader(f'Total Portfolio Value: ${total_portfolio_value:,.2f}')

# Create a DataFrame for detailed holdings
holdings_df = pd.DataFrame({
    'Ticker': list(holdings.keys()),
    'Shares': list(holdings.values()),
    'Current Value Numeric': [current_values[ticker] for ticker in holdings.keys()]
})

# Format the DataFrame
holdings_df['Current Value (USD)'] = holdings_df['Current Value Numeric'].map('${:,.2f}'.format)

# --- Create a Batman-Themed Pie Chart ---
import matplotlib.colors as mcolors

# Sort holdings by current value for better color gradient
holdings_df.sort_values('Current Value Numeric', ascending=False, inplace=True)

# Define Batman-themed colors
batman_yellow = '#FDE311'
dark_navy = '#0C2340'  # Batman's dark navy
grey_palette = ['#2C2C2C', '#4F4F4F', '#6E6E6E', '#9E9E9E']  # Different shades of grey

# Generate shades of Batman theme
num_shades = len(holdings_df)
batman_colors = []

if num_shades == 1:
    batman_colors = [batman_yellow]
else:
    # Alternate between yellow, navy, and greys
    for i in range(num_shades):
        if i == 0:
            # Start with Batman yellow
            batman_colors.append(batman_yellow)
        elif i % 2 == 0:
            # Alternate with dark navy
            batman_colors.append(dark_navy)
        else:
            # Fill in with grey shades (cycled through)
            batman_colors.append(grey_palette[i % len(grey_palette)])

# Create the pie chart with Batman theme colors
fig = go.Figure(data=[go.Pie(
    labels=holdings_df['Ticker'],
    values=holdings_df['Current Value Numeric'],
    marker=dict(colors=batman_colors),
    textinfo='label+percent',
    hoverinfo='label+value'
)])

fig.update_layout(
    title_text='Portfolio Allocation (Batman Theme)',
    showlegend=True
)

# Display the pie chart
st.plotly_chart(fig)
# --- Integrate into the Streamlit App ---
# Map tickers to company names
@st.cache_data
def get_ticker_to_name(tickers):
    ticker_to_name = {}
    for ticker in tickers:
        ticker_obj = yf.Ticker(ticker)
        try:
            info = ticker_obj.info
            company_name = info.get('longName', ticker)
        except Exception as e:
            company_name = ticker
        ticker_to_name[ticker] = company_name
    return ticker_to_name

tickers = list(holdings.keys())
ticker_to_name = get_ticker_to_name(tickers)
name_to_ticker = {name: ticker for ticker, name in ticker_to_name.items()}

# Add a dropdown to select a stock using company names
selected_name = st.selectbox('Select a Stock to View Holdings', options=sorted(name_to_ticker.keys()))
selected_stock = name_to_ticker[selected_name]

# Get the stock history
historical_df = get_stock_history(selected_stock, transactions_data)
if historical_df is not None and not historical_df.empty:
    # Plot Value of Holdings and Value Invested over time on the same y-axis
    fig = go.Figure()

    # Add "Value Invested" line
    fig.add_trace(go.Scatter(
        x=historical_df['Date'],
        y=historical_df['Value Paid'],
        name='Value Invested',
        line=dict(color='#FFFFFF')
    ))

    # Add "Value of Holdings" line
    fig.add_trace(go.Scatter(
        x=historical_df['Date'],
        y=historical_df['Value'],
        name='Value of Holdings',
        line=dict(color='#FDE311')
    ))

    # Update layout without dual y-axes
    fig.update_layout(
        title=f'{selected_name} Holdings',
        xaxis_title='Date',
        yaxis_title='Value (USD)',
        legend=dict(x=0.01, y=0.99)
    )

    st.plotly_chart(fig)
else:
    st.warning("No historical data available to display.")
