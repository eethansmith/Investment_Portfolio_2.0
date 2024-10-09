import streamlit as st
import json
from pathlib import Path
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time

from cache_stock import cache_stock_price

# Load fallback stock prices from JSON
with open('stock_prices.json', 'r') as f:
    fallback_prices = json.load(f)

def calculate_current_values(holdings, transactions_df):
    """Calculate current values and profit/loss per stock."""
    # --- Calculate Current Values and Total Portfolio Value ---
    current_values = {}
    profit_loss_per_stock = {}
    total_current_value = 0.0
    total_invested_amount = 0.0

    for ticker, shares in holdings.items():
        try:
            stock = yf.Ticker(ticker)
            stock_info = stock.history(period="1d")['Close'].iloc[-1]  # Get the most recent closing price

            # Calculate current value based on fetched stock price
            current_value = stock_info * shares
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
            
            cache_stock_price(ticker)
            

        except Exception as e:
            # If there is an issue with fetching data, use the fallback price from the JSON file
            fallback_price = fallback_prices.get(ticker)
            if fallback_price is not None:
                current_value = fallback_price * shares
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
            else:
                st.error(f"Could not retrieve data for {ticker} from Yahoo Finance or fallback.")

    # Calculate total profit or loss
    total_profit_loss = total_current_value - total_invested_amount

    return current_values, profit_loss_per_stock, total_current_value, total_invested_amount, total_profit_loss
