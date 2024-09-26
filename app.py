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
from data_processing import process_transactions
from financial_calculations import calculate_current_values
from visualisation import display_overall_holdings, create_pie_chart, display_stock_details

st.set_page_config(page_title="Investment Portfolio", page_icon="logo.svg")

# Set the title of the app
st.title('Investment Portfolio')

def load_transactions(json_file_path):
    """Load transaction data from a JSON file."""
    with open(json_file_path, 'r') as file:
        transactions_data = json.load(file)
    return pd.DataFrame(transactions_data)

# Define the path to the JSON file
json_file_path = Path(__file__).parent / 'data' / 'investment_data.json'

# Load transactions
transactions_df = load_transactions(json_file_path)

# Process transactions to get holdings and cumulative investment
holdings, cumulative_investment, shares_held_over_time, investment_over_time, dates = process_transactions(transactions_df)

# Calculate current values and profit/loss
current_values, profit_loss_per_stock, total_current_value, total_invested_amount, total_profit_loss = calculate_current_values(holdings, transactions_df)

# Display overall holdings
display_overall_holdings(total_current_value, total_invested_amount, total_profit_loss)

# Prepare holdings_df for the pie chart
holdings_df = pd.DataFrame({
    'Ticker': list(holdings.keys()),
    'Shares': list(holdings.values()),
    'Current Value Numeric': [current_values[ticker] for ticker in holdings.keys()],
    'Profit/Loss': [profit_loss_per_stock[ticker] for ticker in holdings.keys()]
})

# Create and display the pie chart
create_pie_chart(holdings_df)

# Display your markdown text
st.markdown("Visual representation of my current stock holdings in my investment portfolio. This application is a remake of the original [Investment Portfolio Project](https://github.com/eethansmith/Investment-Portfolio-Project) I built using a React frontend and Django backend API in December 2023. Utilised yfinance to obtain live data along with investment transactions from my FreeTrade account. I wanted to recreate this project using Streamlit for ease of use and deployment whilst experimenting with more generative AI functionality that I never got round too previously.")  

# Display detailed stock information
display_stock_details(holdings, transactions_df)

