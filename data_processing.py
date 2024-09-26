import pandas as pd
import yfinance as yf
from datetime import datetime

def process_transactions(transactions_df):
    """Process transactions to determine holdings and cumulative investment."""
    # Your existing processing logic here
    # --- Process Transactions to Determine Current Holdings and Cumulative Investment ---
    holdings = {}
    latest_average_costs = {}
    cumulative_investment = 0.0
    investment_over_time = []
    portfolio_value_over_time = []
    dates = []

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

    return holdings, cumulative_investment, shares_held_over_time, investment_over_time, dates