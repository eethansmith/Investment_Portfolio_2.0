import time
import yfinance as yf
import streamlit as st

@st.cache_data
def get_ticker_to_name(tickers):
    ticker_to_name = {}
    for ticker in tickers:
        ticker_obj = yf.Ticker(ticker)
        company_name = ticker  # Default to ticker symbol
        try:
            info = ticker_obj.info
            if info and 'longName' in info:
                company_name = info['longName']
            time.sleep(0.1)  # To prevent hitting the API rate limit
        except Exception as e:
            st.error(f"Failed to retrieve info for {ticker}: {e}")
        ticker_to_name[ticker] = company_name
    return ticker_to_name