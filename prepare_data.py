import streamlit as st  
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

        # Get the last value from 'Years Held' column
        held_current_amount = historical_df['Years Held'].iloc[-1]
        
        # Format the data for clarity
        investment_data = {
            "Stock Name": ticker,
            "Current Stock Price": f"${current_stock_price:.2f}",
            "Average Price Paid per Share": f"${average_price_paid:.2f}",
            "Percentage Change Since Investment": f"{percentage_change:.2f}%",
            "Held current amount for": f"{held_current_amount:.2f} years",  # Fixed to use the single value
            "First Invested (years)": f"{holding_duration_years:.2f} years",
            "Shares Held": f"{total_shares_held:.2f} shares",
            "Total Value Invested": f"${total_value_paid:.2f}",
        }
        # Process data (e.g., scoring) and return result
        scoring_result = score_investment(investment_data)
        return scoring_result

    except Exception as e:
        st.error(f"An error occurred while preparing investment data: {e}")
        return None
