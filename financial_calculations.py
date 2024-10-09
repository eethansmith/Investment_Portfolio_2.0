import streamlit as st
import json
from pathlib import Path
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time

def calculate_current_values(holdings, transactions_df):
    """Calculate current values and profit/loss per stock."""
    current_values = {}
    profit_loss_per_stock = {}
    total_current_value = 0.0
    total_invested_amount = 0.0
    hardcoded_prices = {'AMZN': 130.0, 'AAPL': 150.0, 'GOOGL': 2700.0}  # Update with actual values

    for ticker, shares in holdings.items():
        ticker_obj = yf.Ticker(ticker)
        try:
            history = ticker_obj.history(period='1d')
            if not history.empty:
                current_price = history['Close'].iloc[0]
            else:
                # Try a longer period
                history = ticker_obj.history(period='7d')
                if not history.empty:
                    current_price = history['Close'].iloc[-1]
                else:
                    # Use hardcoded value
                    current_price = hardcoded_prices.get(ticker, 0.0)
                    st.warning(f"Using hardcoded price for {ticker}")

            current_value = current_price * shares
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

        except Exception as e:
            current_values[ticker] = 0.0
            profit_loss_per_stock[ticker] = 0.0  # Set a default value for profit/loss
            st.error(f"Failed to retrieve price for {ticker}: {e}")

    # Calculate total profit or loss
    total_profit_loss = total_current_value - total_invested_amount

    return current_values, profit_loss_per_stock, total_current_value, total_invested_amount, total_profit_loss