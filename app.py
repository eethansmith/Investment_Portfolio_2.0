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

# --- Map Tickers to Company Names ---
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

# --- Calculate Portfolio Summary ---
portfolio_data = []
total_invested = 0.0
total_current_value = 0.0

for ticker, shares in holdings.items():
    avg_cost = latest_average_costs[ticker]
    invested_amount = shares * avg_cost
    ticker_obj = yf.Ticker(ticker)
    current_price = ticker_obj.history(period='1d')['Close'][0]
    current_value = shares * current_price
    gain_loss = current_value - invested_amount
    gain_loss_percent = (gain_loss / invested_amount) * 100 if invested_amount != 0 else 0
    company_name = ticker_to_name[ticker]
    
    total_invested += invested_amount
    total_current_value += current_value

    portfolio_data.append({
        'Ticker': ticker,
        'Company Name': company_name,
        'Shares': shares,
        'Average Cost': avg_cost,
        'Current Price': current_price,
        'Invested Amount': invested_amount,
        'Current Value': current_value,
        'Gain/Loss': gain_loss,
        'Gain/Loss %': gain_loss_percent
    })

portfolio_df = pd.DataFrame(portfolio_data)

# --- Display Portfolio Summary ---
st.header("Portfolio Overview")

col1, col2, col3 = st.columns(3)
col1.metric("Total Invested", f"${total_invested:,.2f}")
col2.metric("Current Value", f"${total_current_value:,.2f}")
total_gain_loss = total_current_value - total_invested
total_gain_loss_percent = (total_gain_loss / total_invested) * 100 if total_invested != 0 else 0
col3.metric("Total Gain/Loss", f"${total_gain_loss:,.2f}", f"{total_gain_loss_percent:+.2f}%")

# --- Display Portfolio Allocation Pie Chart ---
fig_pie = px.pie(
    portfolio_df, 
    names='Company Name', 
    values='Current Value', 
    title='Portfolio Allocation',
    hole=0.4
)
st.plotly_chart(fig_pie, use_container_width=True)

# --- Integrate into the Streamlit App ---
st.header("Individual Stock Performance")

# Add a dropdown to select a stock using company names
selected_name = st.selectbox('Select a Stock to View Holdings History', options=sorted(name_to_ticker.keys()))
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
        line=dict(color='#FF4B4B')
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

