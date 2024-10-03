from openai import OpenAI
from dotenv import load_dotenv

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
        Using the following grading criteria provided, evaluate then provide a score for the investment on a scale from 0-100, The goal is to grade the stock investment's performance compared to broader benchmarks (S&P 500 5 Year Return is at 93.01%, S&P 500 1 Year Return at 25.31%), sector performance, and market conditions. Use the following grading scale to provide a score and a brief explanation of why the investment falls at that score.

        ### Grading Scale:
        - **0-10**: An Investment where the stock has underperformed severely compared to market benchmarks and safer alternatives.
        - **10-20**: A Poor Investment where this stock has underperformed and has shown significant volatility or low returns.
        - **20-30**: This investment is seen as Below Average and underperformed slightly or remained stagnant.
        - **30-40**: An investment is growing but at a slower pace than the market average thus landing Slightly Underperforming .
        - **40-50**: The stock has performed in line with market averages at 7-10% per anum or inline with S&P500.
        - **50-60**: An investment that is Slightly Above Average where the stock is performing better than market benchmarks 7-10% but marginnaly.
        - **60-70**: The stock has performed well, exceeding market expectations outporforming the 10% market benchmark.
        - **70-80**: The stock has shown excellent growth in the period invested and assesed retrospectively as a Great choice on investment.
        - **80-90**: The stock has delivered exceptional returns with minimal risk and performed exceedingly above the benchmark.
        - **90-100**: An Outstanding Investment that was well timed, shown exceeding performance and The stock has significantly outperformed expectations.
        
        ### provide an exact integer score from 0-100 and a brief explanation of why the investment falls within that range. Score must not be a multiple of 10.
        """

    # Dynamically construct the 'info' string using investment_data
    info = f"""
    Stock Name: {investment_data['Stock Name']},
    Current Stock Price: {investment_data['Current Stock Price']},
    Average Price Paid per Share: {investment_data['Average Price Paid per Share']},
    Percentage Change Since Investment: {investment_data['Percentage Change Since Investment']},
    Holding Duration (years): {investment_data['Holding Duration (years)']},
    Shares Held: {investment_data['Shares Held']},
    Total Value Invested: {investment_data['Total Value Invested']}
    
    Score:"""

    scoring = get_answer(prompt, info)
    return scoring