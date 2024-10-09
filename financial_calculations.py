import streamlit as st
import json
from pathlib import Path
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time

def generate_fallback_prices():
    default_prices = {
        "AMZN": 3200.0,
        "AAPL": 120.0,
        "GOOGL": 1500.0,
        "MSFT": 200.0,
        "NVDA": 500.0,
        "PLTR": 41.0
    }
    return default_prices

def calculate_current_values(holdings, transactions_df):
    """Calculate current values and profit/loss per stock."""
    current_values = {}
    profit_loss_per_stock = {}
    total_current_value = 0.0
    total_invested_amount = 0.0

    for ticker, shares in holdings.items():
        ticker_obj = yf.Ticker(ticker)
        try:
            default_prices = generate_fallback_prices()
            # Attempt to get the current price
            current_price = ticker_obj.history(period='1d')['Close'].iloc[0]

            # Update the fallback price to the latest value
            default_prices[ticker] = current_price

        except Exception as e:
            # Use fallback price if live price is unavailable
            st.error(f"Failed to retrieve price for {ticker}: {e}")
            current_price = default_prices.get(ticker, 0.0)  # Default to 0.0 if no fallback price is available

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

    # Calculate total profit or loss
    total_profit_loss = total_current_value - total_invested_amount

    return current_values, profit_loss_per_stock, total_current_value, total_invested_amount, total_profit_loss