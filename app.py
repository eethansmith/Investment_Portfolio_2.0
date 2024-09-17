import json
from pathlib import Path
import yfinance as yf
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

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
holdings = {k: v for k, v in holdings.items() if v > 0}

# --- Function to Get Stock History ---
def get_stock_history(ticker):
    if not ticker:
        st.error("Ticker symbol is required.")
        return None

    # Filter transactions for the given ticker
    transactions = [t for t in transactions_data if t['Ticker Symbol'] == ticker]

    if not transactions:
        st.error("No transactions found for the given ticker.")
        return None

    # Sort transactions by date
    transactions.sort(key=lambda x: datetime.strptime(x["Date"], '%d-%m-%Y'))

    # Get the first purchase date and current date
    start_date = datetime.strptime(transactions[0]["Date"], '%d-%m-%Y')
    end_date = datetime.now()

    stock = yf.Ticker(ticker)
    try:
        historical_prices = stock.history(start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'))
    except Exception as e:
        st.error(f"Error fetching historical prices for {ticker}: {e}")
        return None

    if historical_prices.empty:
        st.error(f"No historical price data found for {ticker}.")
        return None

    historical_values = []

    # Initialize cumulative values
    cumulative_shares = 0
    cumulative_value_paid = 0

    # Convert transactions to DataFrame and set Date as datetime
    transactions_df = pd.DataFrame(transactions)
    transactions_df['Date'] = pd.to_datetime(transactions_df['Date'], format='%d-%m-%Y')
    transactions_df = transactions_df.sort_values('Date')

    # Create an iterator over transactions
    transactions_iter = iter(transactions_df.iterrows())
    current_transaction_index, current_transaction = next(transactions_iter, (None, None))

    for date, row in historical_prices.iterrows():
        date = date.to_pydatetime().replace(tzinfo=None)
        # Process all transactions up to the current date
        while current_transaction is not None and current_transaction['Date'] <= date:
            transaction_type = current_transaction['Transaction Type']
            shares = float(current_transaction['No. of Shares'])
            transaction_amount = float(current_transaction['Transaction Valuation USD'])
            if transaction_type == 'BUY':
                cumulative_shares += shares
                cumulative_value_paid += transaction_amount
            elif transaction_type == 'SELL':
                cumulative_shares -= shares
                cumulative_value_paid -= transaction_amount
                if cumulative_value_paid < 0:
                    cumulative_value_paid = 0
            # Get the next transaction
            current_transaction_index, current_transaction = next(transactions_iter, (None, None))

        # Get the closing price for the date
        price_per_share = row['Close']

        # Calculate current value of holdings
        value = cumulative_shares * price_per_share

        historical_values.append({
            "Date": date,
            "Value": value,
            "Value Paid": cumulative_value_paid,
            "Shares Held": cumulative_shares,
            "Price per Share": price_per_share
        })

    # Convert historical_values to DataFrame
    historical_df = pd.DataFrame(historical_values)
    historical_df = historical_df.sort_values('Date')

    return historical_df
# --- Integrate into the Streamlit App ---
# Get a list of unique tickers
tickers = list(set([t['Ticker Symbol'] for t in transactions_data]))

# Add a dropdown to select a stock
selected_stock = st.selectbox('Select a Stock to View Holdings History', options=tickers)

# Get the stock history
historical_df = get_stock_history(selected_stock)
if historical_df is not None and not historical_df.empty:
    # Plot Value of Holdings and Value Invested over time on the same y-axis
    fig = go.Figure()

    # Add "Value of Holdings" line
    fig.add_trace(go.Scatter(
        x=historical_df['Date'],
        y=historical_df['Value'],
        name='Value of Holdings',
        line=dict(color='#FF4B4B')
    ))

    # Add "Value Invested" line
    fig.add_trace(go.Scatter(
        x=historical_df['Date'],
        y=historical_df['Value Paid'],
        name='Value Invested',
        line=dict(color='#FAFAFA')
    ))

    # Update layout without dual y-axes
    fig.update_layout(
        title=f'Value of Holdings and Value Invested Over Time for {selected_stock}',
        xaxis_title='Date',
        yaxis_title='Value (USD)',
        legend=dict(x=0.01, y=0.99)
    )

    st.plotly_chart(fig)
else:
    st.warning("No historical data available to display.")

