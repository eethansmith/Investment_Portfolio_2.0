import streamlit as st

import json
from pathlib import Path
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time

from stock_data import get_stock_history

st.set_page_config(page_title="Investment Portfolio", page_icon="logo.svg")

# Set the title of the app
st.title('Investment Portfolio')

# Define the path to the JSON file
json_file_path = Path(__file__).parent / 'data' / 'investment_data.json'

# Open the JSON file and load its content
with open(json_file_path, 'r') as file:
    transactions_data = json.load(file)

# --- Process Transactions to Determine Current Holdings and Cumulative Investment ---
holdings = {}
latest_average_costs = {}
cumulative_investment = 0.0
investment_over_time = []
portfolio_value_over_time = []
dates = []

# Create a DataFrame from transactions_data for easier processing
transactions_df = pd.DataFrame(transactions_data)
transactions_df['Date'] = pd.to_datetime(transactions_df['Date'])

# Sort transactions by date
transactions_df.sort_values('Date', inplace=True)

# Initialize a dictionary to keep track of shares held over time
shares_held_over_time = {}

# Process each transaction
for idx, transaction in transactions_df.iterrows():
    date = transaction["Date"]
    ticker = transaction["Ticker Symbol"]
    shares = float(transaction["No. of Shares"])
    transaction_type = transaction["Transaction Type"]
    avg_cost = float(transaction["Average Cost per Share USD"])
    total_cost = shares * avg_cost

    if ticker not in holdings:
        holdings[ticker] = 0.0

    # Adjust shares based on transaction type
    if transaction_type == "BUY":
        holdings[ticker] += shares
        cumulative_investment += total_cost
    elif transaction_type == "SELL":
        holdings[ticker] -= shares
        cumulative_investment -= total_cost

    latest_average_costs[ticker] = avg_cost  # Update with the latest average cost

    # Record the cumulative investment over time
    investment_over_time.append(cumulative_investment)
    dates.append(date)

    # Record shares held over time
    shares_held_over_time.setdefault(ticker, []).append((date, holdings[ticker]))

# Filter out stocks where holdings are zero or negative
holdings = {k: v for k, v in holdings.items() if v > 0.001}

# --- Calculate Current Values and Total Portfolio Value ---
current_values = {}
profit_loss_per_stock = {}
total_current_value = 0.0
total_invested_amount = 0.0

for ticker, shares in holdings.items():
    ticker_obj = yf.Ticker(ticker)
    try:
        # Attempt to get the current price
        current_price = ticker_obj.history(period='1d')['Close'][0]

        current_value = current_price * shares
        current_values[ticker] = current_value
        total_current_value += current_value

        # Calculate total invested amount for this stock
        total_invested = 0.0
        for idx, transaction in transactions_df[transactions_df['Ticker Symbol'] == ticker].iterrows():
            shares_transacted = float(transaction["No. of Shares"])
            avg_cost = float(transaction["Average Cost per Share USD"])
            total_cost = shares_transacted * avg_cost
            if transaction["Transaction Type"] == "BUY":
                total_invested += total_cost
            elif transaction["Transaction Type"] == "SELL":
                total_invested -= total_cost

        total_invested_amount += total_invested

        # Calculate profit or loss for this stock
        profit_loss = current_value - total_invested
        profit_loss_per_stock[ticker] = profit_loss

    except Exception as e:
        current_values[ticker] = 0.0
        st.error(f"Failed to retrieve price for {ticker}: {e}")

# Calculate total profit or loss
total_profit_loss = total_current_value - total_invested_amount

# --- Display Overall Holdings at the Top ---

col1, col2, col3 = st.columns(3)
col1.metric("Current Holdings Value", f"${total_current_value:,.2f}" if total_current_value else "N/A")
col2.metric("Total Amount Invested", f"${total_invested_amount:,.2f}" if total_invested_amount else "N/A")
if total_profit_loss is not None and total_profit_loss is not None:
    if total_invested_amount != 0:
        total_profit_loss_percent = (total_profit_loss / total_invested_amount) * 100
        col3.metric("Profit/Loss", f"${total_profit_loss:,.2f}", f"{total_profit_loss_percent:.2f}%")
else:
    col3.metric("Profit/Loss", "N/A")
    
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
batman_yellow = (253, 227, 17)
dark_navy = (12, 35, 64)        
grey = (93, 93, 93)             

num_shades = len(holdings_df)
shades_of_batman = []

def interpolate_color(color1, color2, factor):
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

# --- Enhanced Pie Chart ---
holdings_df = pd.DataFrame({
    'Ticker': list(holdings.keys()),
    'Shares': list(holdings.values()),
    'Current Value Numeric': [current_values[ticker] for ticker in holdings.keys()],
    'Profit/Loss': [profit_loss_per_stock[ticker] for ticker in holdings.keys()]
})

# Format the DataFrame
holdings_df['Current Value (USD)'] = holdings_df['Current Value Numeric'].map('${:,.2f}'.format)

# Sort holdings by current value for better color gradient
holdings_df.sort_values('Current Value Numeric', ascending=False, inplace=True)

# Create the pie chart with hover information
fig = go.Figure(data=[go.Pie(
    labels=holdings_df['Ticker'],
    values=holdings_df['Current Value Numeric'],
    marker=dict(colors=shades_of_batman),
    textinfo='label+percent',
    hovertemplate='<b>%{label}</b><br>Current Value: %{value:$,.2f}<br>Profit/Loss: %{customdata:$,.2f}',
    customdata=holdings_df['Profit/Loss']
)])

fig.update_layout(
    showlegend=True
)

# Display the pie chart
st.plotly_chart(fig)

st.markdown("Visual representation of my current stock holdings in my investment portfolio. This application is a remake of the original [Investment Portfolio Project](https://github.com/eethansmith/Investment-Portfolio-Project) I built using a React frontend and Django backend API in December 2023. Utilised yfinance to obtain live data along with investment transactions from FreeTrade. I wanted to recreate this project using Streamlit for ease of use and deployment whilst experimenting with more AI functionality.")  

# --- Display Detailed Holdings ---
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
        <strong>Price per Share</strong><br>
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
        xaxis_title='Date',
        yaxis_title='Value (USD)',
        legend=dict(x=0.01, y=0.99)
    )

    st.plotly_chart(fig)
else:
    st.warning("No historical data available to display.")
