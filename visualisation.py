import streamlit as st
import plotly.graph_objects as go
import yfinance as yf
import pandas as pd

from utils import get_ticker_to_name
from stock_data import get_stock_history
from openai_call import score_investment

def display_overall_holdings(total_current_value, total_invested_amount, total_profit_loss):
    """Display overall holdings at the top."""
    col1, col2, col3 = st.columns(3)
    col1.metric("Current Holdings Value", f"${total_current_value:,.2f}" if total_current_value else "N/A")
    col2.metric("Total Amount Invested", f"${total_invested_amount:,.2f}" if total_invested_amount else "N/A")
    if total_profit_loss is not None and total_profit_loss is not None:
        if total_invested_amount != 0:
            total_profit_loss_percent = (total_profit_loss / total_invested_amount) * 100
            col3.metric("Profit/Loss", f"${total_profit_loss:,.2f}", f"{total_profit_loss_percent:.2f}%")
    else:
        col3.metric("Profit/Loss", "N/A")

    
def create_pie_chart(holdings_df):
    """Create and display the enhanced pie chart."""
    
    
    yellow = (253, 227, 17)
    dark_navy = (12, 35, 64)        
    grey = (93, 93, 93)             

    num_shades = len(holdings_df)
    shades_of_col = []

    def interpolate_color(color1, color2, factor):
        return tuple(
            int(color1[i] + (color2[i] - color1[i]) * factor)
            for i in range(3)
        )

    if num_shades == 1:
        shades_of_col = [f'rgb{yellow}']
    else:
        for i in range(num_shades):
            factor = i / (num_shades - 1)
            if factor <= 0.5:
                # Interpolate between yellow and grey
                interp_factor = factor / 0.5
                color_rgb = interpolate_color(yellow, grey, interp_factor)
            else:
                # Interpolate between grey and dark navy
                interp_factor = (factor - 0.5) / 0.5
                color_rgb = interpolate_color(grey, dark_navy, interp_factor)
            shades_of_col.append(f'rgb{color_rgb}')

    # Create the pie chart with hover information
    fig = go.Figure(data=[go.Pie(
        labels=holdings_df['Ticker'],
        values=holdings_df['Current Value Numeric'],
        marker=dict(colors=shades_of_col),
        textinfo='label+percent',
        hovertemplate='<b>%{label}</b><br>Current Value: %{value:$,.2f}<br>Profit/Loss: %{customdata:$,.2f}',
        customdata=holdings_df['Profit/Loss']
    )])

    fig.update_layout(
        showlegend=True
    )

    # Display the pie chart
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
    historical_df, investment_data = get_stock_history(selected_stock, transactions_data)

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

    # Get additional stats
    info = ticker_obj.info
    pe_ratio = info.get('trailingPE')
    market_cap = info.get('marketCap')
    dividend_yield = info.get('dividendYield')

    # Display the stats
    st.markdown(f"### {selected_name} ({selected_stock})")

    col1, col2, col3 = st.columns(3)
    col1.metric("Current Holdings Value", f"${current_value:,.2f}" if current_value else "N/A")
    col2.metric("Total Amount Invested", f"${total_invested:,.2f}" if total_invested else "N/A")
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
            {f"${avg_cost_per_share:,.2f}" if avg_cost_per_share else "N/A"}
        </div>
    """, unsafe_allow_html=True)

    # Column for Current Price per Share
    col5.markdown(f"""
        <div style='font-size: {small_font_size}; text-align: center;'>
            <strong>Price per Share</strong><br>
            {f"${current_price:,.2f}" if current_price else "N/A"}
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
        
    return (f" {investment_data} ")