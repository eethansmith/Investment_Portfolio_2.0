import streamlit as st

import json
from pathlib import Path
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time

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
st.caption("Visual representation of my live stock holdings from my investment portfolio. This application is a remake of the original [Investment Portfolio Project](https://github.com/eethansmith/Investment-Portfolio-Project) I built using a React frontend and Django backend API in December 2023. Utilised yfinance to obtain live data along with investment transactions from my FreeTrade account. I wanted to recreate this project using Streamlit for ease of use and deployment whilst experimenting with more generative AI functionality.")  
st.caption("The investment data has been extracted from my FreeTrade account spanning back to my very first trade of Apple Stock in November 2020. Each trade is stored in a JSON file and processed to display the current value of my stock portfolio live.")
# Function to create color-coded bar based on the score
def score_to_color_bar(score):
    # Determine the color based on the score
    if score <= 20:
        color = 'red'
    elif score <= 40:
        color = 'orange'
    elif score <= 60:
        color = 'yellow'
    else:
        color = 'green'
    
    # Create a styled div with a width proportional to the score
    bar_html = f"""
    <div style="width: 100%; background-color: lightgray; border-radius: 5px; margin: 10px 0;">
        <div style="width: {score}%; background-color: {color}; height: 20px; border-radius: 5px;"></div>
    </div>
    """
    return bar_html

# Display WAYNE AI detailed stock assessment

explaination, score = display_stock_details(holdings, transactions_df)

# Define assessment based on score ranges
if score is not None:
    if 0 <= score <= 10:
        assessment = ":red[Very Poor Investment]"
    elif 10 < score <= 20:
        assessment = ":red[Poor Investment]"
    elif 20 < score <= 40:
        assessment = ":orange[Underperforming Investment]"
    elif 40 < score <= 60:
        assessment = ":orange[Average Investment]"
    elif 60 < score <= 70:
        assessment = ":green[Good Investment]"
    elif 70 < score <= 85:
        assessment = ":green[Great Investment]"
    elif 85 < score <= 100:
        assessment = ":green[Outstanding Investment]"
    else:
        assessment = "Invalid Score"
else:
    assessment = "No score available"

# Display the assessment in Streamlit
st.markdown(f"### {assessment}")

st.markdown(score_to_color_bar(score), unsafe_allow_html=True)

st.caption(f"{explaination}")