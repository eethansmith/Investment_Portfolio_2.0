from openai import OpenAI
from dotenv import load_dotenv
import yfinance as yf

import streamlit as st

openai_api_key = st.secrets["OPENAI_API_KEY"]

client = OpenAI(api_key=openai_api_key)

def get_answer(prompt, info):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"{prompt}"},
            {"role": "user", "content": f"{info}"}
        ]
    )
    return response.choices[0].message.content


def score_investment(investment_data):
    prompt = f"""
    Based on the grading criteria below, evaluate and provide a score for this stock investment on a scale of 0-100. Consider its performance relative to the broader market benchmarks, including the S&P 500's 5-Year Return of 93.01%, 1-Year Return of 25.31%, sector performance, and prevailing market conditions.

    When scoring, account for factors such as:
    - **Sector performance**: How the stock compares within its industry.
    - **Market volatility**: Impact of market-wide risk or stock-specific fluctuations.
    - **Return on Investment (ROI)**: Performance over the investment period compared to the market.

    ### Grading Scale:
    - **0-10**: Severe underperformance, high risk, or poor return relative to safer alternatives.
    - **10-20**: Poor performance, substantial volatility, or consistently low returns.
    - **20-30**: Below-average investment, marginal returns, or stagnant growth.
    - **30-40**: Slight underperformance, moderate growth but lags behind benchmarks.
    - **40-50**: Average performance, in line with S&P 500 or market norms.
    - **50-60**: Slightly above-average performance, moderately exceeding market benchmarks.
    - **60-70**: Strong performance, consistently exceeding market benchmarks by a good margin.
    - **70-80**: Great investment, showing excellent growth and competitive returns.
    - **80-90**: Exceptional performance with low risk and significant outperformance.
    - **90-100**: Outstanding investment, excellent timing, and substantial outperformance.

    ### Provide an exact integer score from 0-100 (not a multiple of 10) and a brief explanation considering:
    - Stock performance relative to its sector and market.
    - Level of risk/volatility experienced during the investment period.
    - Overall return compared to benchmarks and the investment’s timing.

    ### provide an exact integer score from 0-100 and a brief explanation of why the investment falls within that range. Score must not be a multiple of 10.
    """

    # Fetch the company info using yfinance
    ticker = yf.Ticker(investment_data['Stock Name'])
    company_name = ticker.info.get('longName', 'Company name not available')


    # Dynamically construct the 'info' string using investment_data
    info = f"""
    Stock Name: {company_name}({ticker}),
    Current Stock Price: {investment_data['Current Stock Price']},
    Average Price Paid per Share: {investment_data['Average Price Paid per Share']},
    Percentage Change Since Investment: {investment_data['Percentage Change Since Investment']},
    Held Current amount of shares for: {investment_data['Held current amount for']},
    Shares Held: {investment_data['Shares Held']},
    Total Value Invested: {investment_data['Total Value Invested']}
    
    Score:"""

    scoring = get_answer(prompt, info)
    return scoring