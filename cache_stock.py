import yfinance as yf
import json
import os

# Function to fetch stock prices and save them as a .json file
def save_stock_prices_to_json():
    # List of stock tickers
    tickers = ['GOOG', 'AMZN', 'AAPL', 'BLK', 'CRWD', 'DELL', 'INTC', 'META', 
               'MSFT', 'NVDA', 'ORCL', 'PLTR', 'VUAG.L', 'ZS', 'IBM']
    
    # Dictionary to store ticker and its current price
    stock_data = {}

    # Fetch stock data for each ticker
    for ticker in tickers:
        stock = yf.Ticker(ticker)
        stock_info = stock.history(period="1d")
        
        if not stock_info.empty:
            # Get the closing price for the last available day
            stock_price = stock_info['Close'].iloc[-1]
            stock_data[ticker] = round(stock_price, 2)  # Round price to 2 decimal places
        else:
            print(f"Warning: No data found for {ticker}, possibly delisted.")
    
    # Define the file path where you want to save the JSON
    file_path = os.path.join(os.getcwd(), 'stock_prices.json')

    # Save the stock data to a .json file
    with open(file_path, 'w') as json_file:
        json.dump(stock_data, json_file, indent=4)

    print(f"Stock prices saved to {file_path}")

# Example usage
save_stock_prices_to_json()
