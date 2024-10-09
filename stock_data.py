import streamlit as st  
import pandas as pd  
import yfinance as yf  
from datetime import datetime  

from wayne_ai import score_investment

def prepare_investment_data_for_prompt(historical_df, ticker):
    if historical_df.empty:
        st.error("No historical data available to process.")
        return None

    # Proceed with calculations
    try:
        # Current stock price (latest value in the dataframe)
        current_stock_price = historical_df.iloc[-1]["Price per Share"]

        # Calculate average price paid per share
        total_value_paid = historical_df.iloc[-1]["Value Paid"]
        total_shares_held = historical_df.iloc[-1]["Shares Held"]
        average_price_paid = total_value_paid / total_shares_held if total_shares_held != 0 else 0

        # Percentage change since first purchase
        initial_price = historical_df.iloc[0]["Price per Share"]
        
        profit = (current_stock_price * total_shares_held) - total_value_paid
        percentage_change = (profit / total_value_paid) * 100 if total_value_paid != 0 else 0

        # Holding duration in years
        start_date = historical_df.iloc[0]["Date"]
        end_date = historical_df.iloc[-1]["Date"]
        holding_duration_years = (end_date - start_date).days / 365

        # Format the data for clarity
        investment_data = {
            "Stock Name": ticker,
            "Current Stock Price": f"${current_stock_price:.2f}",
            "Average Price Paid per Share": f"${average_price_paid:.2f}",
            "Percentage Change Since Investment": f"{percentage_change:.2f}%",
            "Holding Duration (years)": f"{holding_duration_years:.2f} years",
            "Shares Held": f"{total_shares_held:.2f} shares",
            "Total Value Invested": f"${total_value_paid:.2f}",
        }

        # Print formatted output
        print(f"Investment Data Summary: {investment_data}")

        # Process data (e.g., scoring) and return result
        scoring_result = score_investment(investment_data)
        return scoring_result

    except Exception as e:
        st.error(f"An error occurred while preparing investment data: {e}")
        return None

# --- End of Function to Get Stock History ---

# --- Function to Get Stock History ---
def get_stock_history(ticker, transactions_data):
    if not ticker:
        st.error("Ticker symbol is required.")
        return None

    # Filter transactions for the given ticker
    transactions = [t for t in transactions_data if t['Ticker Symbol'] == ticker]

    if not transactions:
        st.error("No transactions found for the given ticker.")
        return None

    # Sort transactions by date
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

    if not historical_values:
        st.error(f"No historical values computed for {ticker}.")
        return None

    # Convert historical_values to DataFrame
    historical_df = pd.DataFrame(historical_values)
    historical_df = historical_df.sort_values('Date')

    investment_data = prepare_investment_data_for_prompt(historical_df, ticker)

    return historical_df, investment_data
