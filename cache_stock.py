import yfinance as yf
import json
import os

# Function to fetch stock price for a single ticker and update the JSON file
def cache_stock_price(ticker):
    # Define the file path where the stock data is saved
    file_path = os.path.join(os.getcwd(), 'stock_prices.json')

    # Try to load existing stock data from the JSON file, if it exists
    if os.path.exists(file_path):
        with open(file_path, 'r') as json_file:
            stock_data = json.load(json_file)
    else:
        stock_data = {}

    # Fetch stock data for the specified ticker
    stock = yf.Ticker(ticker)
    stock_info = stock.history(period="1d")

    if not stock_info.empty:
        # Get the closing price for the last available day
        stock_price = stock_info['Close'].iloc[-1]
        stock_data[ticker] = round(stock_price, 2)  # Round price to 2 decimal places
        
        # Save the updated stock data back to the JSON file
        with open(file_path, 'w') as json_file:
            json.dump(stock_data, json_file, indent=4)