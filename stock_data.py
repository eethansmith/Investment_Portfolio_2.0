import streamlit as st  
import pandas as pd  
import yfinance as yf  
from datetime import datetime  

from prepare_data import prepare_investment_data_for_prompt

def get_stock_history(ticker, transactions_data):
    if not ticker:
        st.error("Ticker symbol is required.")
        return None

    # Filter transactions for the given ticker
    transactions = [
        t for t in transactions_data if t['Ticker Symbol'] == ticker
    ]

    if not transactions:
        st.error("No transactions found for the given ticker.")
        return None

    # Clean and convert transactions data
    for t in transactions:
        # Convert 'Date' to datetime object
        if isinstance(t['Date'], str):
            t['Date'] = datetime.strptime(t['Date'], '%d-%m-%Y')

        # Remove '$' and commas from 'Price per Share USD' and convert to float
        price_str = t['Price per Share USD'].replace('$', '').replace(',', '').strip()
        t['Price per Share USD'] = float(price_str)

        # Convert 'No. of Shares' to float
        t['No. of Shares'] = float(t['No. of Shares'])

        # Ensure 'Transaction Valuation USD' is a float
        if isinstance(t['Transaction Valuation USD'], str):
            valuation_str = t['Transaction Valuation USD'].replace('$', '').replace(',', '').strip()
            t['Transaction Valuation USD'] = float(valuation_str)

    # Now sort the transactions by date
    transactions.sort(key=lambda x: x["Date"])

    # Get the first purchase date and current date
    start_date = transactions[0]["Date"]
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
    total_trades = 0  # Initialize a counter for total trades
    last_holding_start = None
    total_holding_days = 0  # Initialize total holding days

    # Convert transactions to DataFrame
    transactions_df = pd.DataFrame(transactions)
    transactions_df = transactions_df.sort_values('Date')

    # Create an iterator over transactions
    transactions_iter = iter(transactions_df.iterrows())
    current_transaction_index, current_transaction = next(transactions_iter, (None, None))

    # Loop through historical prices
    for date, row in historical_prices.iterrows():
        date = date.to_pydatetime().replace(tzinfo=None)
        # Process all transactions up to the current date
        while current_transaction is not None and current_transaction['Date'] <= date:
            transaction_type = current_transaction['Transaction Type']
            shares = current_transaction['No. of Shares']
            transaction_amount = current_transaction['Transaction Valuation USD']

            if transaction_type == 'BUY':
                if cumulative_shares < 0.1:
                    last_holding_start = current_transaction['Date']
                cumulative_shares += shares
                cumulative_value_paid += transaction_amount
                total_trades += 1  # Increment the trade counter

            elif transaction_type == 'SELL':
                cumulative_shares -= shares
                cumulative_value_paid -= transaction_amount
                total_trades += 1  # Increment the trade counter

                # Ensure values don't go below zero
                cumulative_shares = max(cumulative_shares, 0.00)
                cumulative_value_paid = max(cumulative_value_paid, 0.00)

                if cumulative_shares == 0 and last_holding_start is not None:
                    last_holding_end = current_transaction['Date']
                    holding_period = (last_holding_end - last_holding_start).days
                    total_holding_days += holding_period
                    last_holding_start = None  # Reset holding start

            # Get the next transaction
            try:
                current_transaction_index, current_transaction = next(transactions_iter)
            except StopIteration:
                current_transaction = None

        # Get the closing price for the date
        price_per_share = row['Close']

        # Calculate current value of holdings
        value = cumulative_shares * price_per_share

        # Ensure value doesn't go below zero
        value = max(value, 0.00)

        # Calculate years held
        if last_holding_start is not None:
            current_holding_days = (date - last_holding_start).days
            total_days_held = total_holding_days + current_holding_days
        else:
            total_days_held = total_holding_days

        years_held = total_days_held / 365.25

        historical_values.append({
            "Date": date,
            "Value": value,
            "Value Paid": cumulative_value_paid,
            "Shares Held": cumulative_shares,
            "Price per Share": price_per_share,
            "Total Trades": total_trades,
            "Years Held": years_held
        })

    if not historical_values:
        st.error(f"No historical values computed for {ticker}.")
        return None

    # Convert historical_values to DataFrame
    historical_df = pd.DataFrame(historical_values)
    historical_df = historical_df.sort_values('Date')

    investment_data = prepare_investment_data_for_prompt(historical_df, ticker)

    return historical_df, investment_data