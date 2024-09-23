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

# Sort holdings by current value for better color gradient
holdings_df.sort_values('Current Value Numeric', ascending=False, inplace=True)

# Define the Batman-themed colors in RGB format
batman_yellow = (253, 227, 17)  # FDE311
dark_navy = (12, 35, 64)        # 0C2340
grey = (93, 93, 93)             # 5D5D5D

num_shades = len(holdings_df)
shades_of_batman = []

def interpolate_color(color1, color2, factor):
    """
    Interpolate between two colors.
    color1 and color2 are in RGB tuple format (R, G, B) where R, G, B are 0-255.
    factor is between 0 and 1, where 0 is color1, 1 is color2.
    """
    return tuple(
        int(color1[i] + (color2[i] - color1[i]) * factor)
        for i in range(3)
    )

if num_shades == 1:
    shades_of_batman = [f'rgb{batman_yellow}']
else:
    # We'll create a gradient that goes from Batman yellow to grey to dark navy
    for i in range(num_shades):
        factor = i / (num_shades - 1)
        if factor <= 0.5:
            # Interpolate between yellow and grey
            interp_factor = factor / 0.5
            color_rgb = interpolate_color(batman_yellow, grey, interp_factor)
        else:
            # Interpolate between grey and dark navy
            interp_factor = (factor - 0.5) / 0.5
            color_rgb = interpolate_color(grey, dark_navy, interp_factor)
        shades_of_batman.append(f'rgb{color_rgb}')

# Create the pie chart
fig = go.Figure(data=[go.Pie(
    labels=holdings_df['Ticker'],
    values=holdings_df['Current Value Numeric'],
    marker=dict(colors=shades_of_batman),
    textinfo='label+percent',
    hoverinfo='label+value'
)])

fig.update_layout(
    title_text='Portfolio Allocation - Batman Theme',
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
            time.sleep(0.1)  # To prevent hitting the API rate limit
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

# Calculate additional stats
# Get number of shares held
shares_held = holdings.get(selected_stock, 0)

# Get current price
ticker_obj = yf.Ticker(selected_stock)
try:
    current_price = ticker_obj.history(period='1d')['Close'][0]
except Exception as e:
    current_price = None

if current_price is not None:
    current_value = shares_held * current_price
else:
    current_value = None

# Get total amount invested
if historical_df is not None and not historical_df.empty:
    total_invested = historical_df['Value Paid'].iloc[-1]
else:
    total_invested = None

# Compute profit and profit percentage
if current_value is not None and total_invested is not None:
    profit = current_value - total_invested
    profit_percent = (profit / total_invested) * 100 if total_invested != 0 else None
else:
    profit = None
    profit_percent = None

# Compute average cost per share
if shares_held > 0 and total_invested is not None:
    avg_cost_per_share = total_invested / shares_held
else:
    avg_cost_per_share = None

# Get additional stats
info = ticker_obj.info
pe_ratio = info.get('trailingPE')
market_cap = info.get('marketCap')
dividend_yield = info.get('dividendYield')

# Display the stats
st.markdown(f"### {selected_name} ({selected_stock})")

col1, col2, col3 = st.columns(3)
col1.metric("Current Holdings Value", f"${current_value:,.2f}" if current_value else "N/A")
col2.metric("Total Amount Invested", f"${total_invested:,.2f}" if total_invested else "N/A")
if profit is not None and profit_percent is not None:
    col3.metric("Profit/Loss", f"${profit:,.2f}", f"{profit_percent:.2f}%")
else:
    col3.metric("Profit/Loss", "N/A")

col4, col5, col6 = st.columns(3)

# Define the desired smaller font size
small_font_size = "16px"  # Adjust this value as needed

# Column for Average Cost per Share
col4.markdown(f"""
    <div style='font-size: {small_font_size}; text-align: center;'>
        <strong>Average Cost per Share</strong><br>
        {f"${avg_cost_per_share:,.2f}" if avg_cost_per_share else "N/A"}
    </div>
""", unsafe_allow_html=True)

# Column for Current Price per Share
col5.markdown(f"""
    <div style='font-size: {small_font_size}; text-align: center;'>
        <strong>Current Price per Share</strong><br>
        {f"${current_price:,.2f}" if current_price else "N/A"}
    </div>
""", unsafe_allow_html=True)

# Column for Shares Held
col6.markdown(f"""
    <div style='font-size: {small_font_size}; text-align: center;'>
        <strong>Shares Held</strong><br>
        {shares_held}
    </div>
""", unsafe_allow_html=True)

# Plot the graph
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
