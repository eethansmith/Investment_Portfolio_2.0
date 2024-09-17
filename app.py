import json
from pathlib import Path
import yfinance as yf
import pandas as pd
import streamlit as st

import plotly.express as px

# Set the title of the app
st.title('Current Stock Holdings')

# Define the path to the JSON file
json_file_path = 'data/investment_data.json'

# Open the JSON file and load its content
with open(json_file_path, 'r') as file:
    transactions_data = json.load(file)

# Process transactions to determine current holdings
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

# Fetch live data for remaining stocks
live_data = []
for ticker, shares in holdings.items():
    try:
        stock = yf.Ticker(ticker)
        stock_info = stock.info

        # Determine the correct fields based on the ticker
        name_field = "longName" if ticker == "VUAG.L" else "shortName"
        price_field = "previousClose" if ticker == "VUAG.L" else "currentPrice"

        # Fetch the relevant data
        name = stock_info.get(name_field, 'N/A')
        current_price = stock_info.get(price_field) or stock_info.get("previousClose", 0)
        average_cost = latest_average_costs[ticker]
        total_investment = average_cost * shares
        current_value = shares * current_price if current_price else 0
        value_held = round(current_value, 2)

        profit_loss_percentage = round(((current_value - total_investment) / total_investment * 100), 2) if total_investment else 0

        live_data.append({
            "Ticker": ticker,
            "Name": name,
            "Shares Held": round(shares, 4),
            "Average Cost": round(average_cost, 2),
            "Current Price": round(current_price, 2),
            "Total Investment": round(total_investment, 2),
            "Current Value": value_held,
            "P/L %": profit_loss_percentage
        })
    except Exception as e:
        st.error(f"Error fetching data for {ticker}: {e}")

# Convert live data to DataFrame
df = pd.DataFrame(live_data)

# Sort DataFrame by 'Current Value'
df = df.sort_values(by='Current Value', ascending=False)

# Display DataFrame in Streamlit
st.dataframe(df.style.format({
    "Average Cost": "${:.2f}",
    "Current Price": "${:.2f}",
    "Total Investment": "${:.2f}",
    "Current Value": "${:.2f}",
    "P/L %": "{:.2f}%"
}))

# Get a list of unique tickers
tickers = df['Ticker'].unique()

# Add a multiselect widget in the sidebar
selected_tickers = st.sidebar.multiselect('Select Tickers', tickers, default=tickers)

# Filter the DataFrame based on selection
filtered_df = df[df['Ticker'].isin(selected_tickers)]

# Display the filtered DataFrame
st.dataframe(filtered_df)

# Create a bar chart for Profit/Loss Percentage
fig = px.bar(df, x='Ticker', y='P/L %', color='P/L %', title='Profit/Loss Percentage by Ticker')
st.plotly_chart(fig)

# Create a pie chart for portfolio distribution
fig = px.pie(df, names='Ticker', values='Current Value', title='Portfolio Distribution')
st.plotly_chart(fig)
