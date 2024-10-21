import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import yfinance as yf
import pandas as pd
import re

from utils import get_ticker_to_name
from stock_data import get_stock_history

def display_overall_holdings(total_current_value, total_invested_amount, total_profit_loss):
    """Display overall holdings at the top."""
    col1, col2, col3 = st.columns(3)
    col1.metric("Current Holdings Value", f"${total_current_value:,.2f}")
    col2.metric("Total Amount Invested", f"${total_invested_amount:,.2f}")
    if total_profit_loss is not None and total_profit_loss is not None:
        if total_invested_amount != 0:
            total_profit_loss_percent = (total_profit_loss / total_invested_amount) * 100
            col3.metric("Profit/Loss", f"${total_profit_loss:,.2f}", f"{total_profit_loss_percent:.2f}%")
    else:
        col3.metric("Profit/Loss", "N/A")



def create_pie_chart(holdings_df):
    """Create and display a sunburst chart with stock categories and individual holdings."""
    
    # Add a new column for the stock categories (if not already added)
    holdings_df['Category'] = holdings_df['Ticker'].apply(lambda ticker: 
        'S&P 500' if ticker == 'VUAG.L' else
        'Tech' if ticker in ['PLTR', 'AAPL', 'MSFT', 'META', 'AMZN', 'GOOG', 'NVDA', 'ZS', 'CRWD', 'INTC', 'ORCL', 'DELL', 'IBM'] else
        'Finance' if ticker == 'BLK' else
        'Other'
    )

    # Define custom colors for the categories
    category_colors = {
        'Tech': '#0A6BC4',   
        'S&P 500': '#B4BEC9',  
        'Finance': '#FEBC4C',
        'Other': '#CCCCCC'     # default grey for other category
    }

    # Ensure that 'Profit/Loss' column contains numeric values and replace NaN with 0
    holdings_df['Profit/Loss'] = holdings_df['Profit/Loss'].fillna(0)

    # Create the sunburst chart
    fig = px.sunburst(
        data_frame=holdings_df,
        path=['Category', 'Ticker'],
        values='Current Value Numeric',
        color='Category',
        color_discrete_map=category_colors,
        hover_data={'Profit/Loss': ':.2f', 'Current Value Numeric': ':.2f'},
    )
    
    fig.update_traces(
        textinfo='label+percent entry',
        hovertemplate='<b>%{label}</b><br>Current Value: $%{value:,.2f}<br>Profit/Loss: $%{customdata[0]:,.2f}<extra></extra>'
    )

    # Display the sunburst chart
    st.plotly_chart(fig)


    
def display_stock_details(holdings, transactions_df):
    """Display detailed holdings and graphs for the selected stock."""
    # Map tickers to company names
    tickers = list(holdings.keys())
    ticker_to_name = get_ticker_to_name(tickers)
    name_to_ticker = {name: ticker for ticker, name in ticker_to_name.items()}

    # Add a dropdown to select a stock using company names
    selected_name = st.selectbox('Select a Stock to View Holdings', options=sorted(name_to_ticker.keys()))
    selected_stock = name_to_ticker[selected_name]
    
    transactions_data = transactions_df.to_dict('records')

    # Get the stock history
    historical_df, investment_score = get_stock_history(selected_stock, transactions_data)

    # Calculate additional stats
    # Get number of shares held
    shares_held = holdings.get(selected_stock, 0)

    # Get current price
    ticker_obj = yf.Ticker(selected_stock)
    try:
        current_price = ticker_obj.history(period='1d')['Close'][0]
    except Exception as e:
        current_price = None

    if current_price is not None:
        current_value = shares_held * current_price
    else:
        current_value = None

    # Get total amount invested
    if historical_df is not None and not historical_df.empty:
        total_invested = historical_df['Value Paid'].iloc[-1]
    else:
        total_invested = None

    # Compute profit and profit percentage
    if current_value is not None and total_invested is not None:
        profit = current_value - total_invested
        profit_percent = (profit / total_invested) * 100 if total_invested != 0 else None
    else:
        profit = None
        profit_percent = None

    # Compute average cost per share
    if shares_held > 0 and total_invested is not None:
        avg_cost_per_share = total_invested / shares_held
    else:
        avg_cost_per_share = None

    # Display the stats
    st.markdown(f"### {selected_name} ({selected_stock})")

    col1, col2, col3 = st.columns(3)
    col1.metric("Current Holdings Value", f"${current_value:,.2f}")
    col2.metric("Total Amount Invested", f"${total_invested:,.2f}")
    if profit is not None and profit_percent is not None:
        col3.metric("Profit/Loss", f"${profit:,.2f}", f"{profit_percent:.2f}%")
    else:
        col3.metric("Profit/Loss", "N/A")

    col4, col5, col6 = st.columns(3)

    # Define the desired smaller font size
    small_font_size = "16px"  # Adjust this value as needed

    # Column for Average Cost per Share
    col4.markdown(f"""
        <div style='font-size: {small_font_size}; text-align: center;'>
            <strong>Average Cost per Share</strong><br>
            {f"${avg_cost_per_share:,.2f}"}
        </div>
    """, unsafe_allow_html=True)

    # Column for Current Price per Share
    col5.markdown(f"""
        <div style='font-size: {small_font_size}; text-align: center;'>
            <strong>Price per Share</strong><br>
            {f"${current_price:,.2f}"}
        </div>
    """, unsafe_allow_html=True)

    # Column for Shares Held
    col6.markdown(f"""
        <div style='font-size: {small_font_size}; text-align: center;'>
            <strong>Shares Held</strong><br>
            {shares_held}
        </div>
    """, unsafe_allow_html=True)

    # Plot the graph
    if historical_df is not None and not historical_df.empty:
        # Plot Value of Holdings and Value Invested over time on the same y-axis
        fig = go.Figure()

        # Add "Value Invested" line
        fig.add_trace(go.Scatter(
            x=historical_df['Date'],
            y=historical_df['Value Paid'],
            name='Value Invested',
            line=dict(color='#FFFFFF')
        ))

        # Add "Value of Holdings" line
        fig.add_trace(go.Scatter(
            x=historical_df['Date'],
            y=historical_df['Value'],
            name='Value of Holdings',
            line=dict(color='#FDE311')
        ))

        # Update layout without dual y-axes
        fig.update_layout(
            xaxis_title='Date',
            yaxis_title='Value (USD)',
            legend=dict(x=0.01, y=0.99)
        )
        
        st.plotly_chart(fig)
    else:
        st.warning("No historical data available to display.")

    # Use regex to match either "Score: <number>" or just "<number>"
    match = re.search(r'(?:Score:\s*)?(100|[1-9]?\d)', investment_score, re.IGNORECASE)
    
    if match:
        score = int(match.group(1))  # Extract the score from the match
        # Extract explanation, everything after the matched score, if any
        explanation = investment_score[match.end():].strip()
    else:
        # Handle cases where no score is found
        score = None
        explanation = investment_score.strip()  # Return the full string as explanation
    explanation = re.sub(r'(?<!\$)\$(?!\$)', '\$', explanation)
    explanation = explanation.replace('\n', '')
    explanation = explanation.replace('*', '')
    
    return explanation, score