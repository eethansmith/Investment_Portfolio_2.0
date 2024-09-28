from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# Initialize the OpenAI client
api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=api_key)

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
        Using the following information provided, evaluate and rank the investment on a scale from 0-100, where 0 represents the worst possible outcome and 100 represents the best possible outcome. The goal is to analyze the stock investment's performance compared to broader benchmarks (e.g., S&P 500), sector performance, and market conditions, while taking into account the investor’s objectives, time horizon, and risk tolerance.

        ### Grading Scale:
        - **0-10**: Very Bad Investment – The stock has underperformed severely compared to market benchmarks and safer alternatives.
        - **10-20**: Bad Investment – The stock has underperformed and has shown significant volatility or low returns.
        - **20-30**: Below Average Investment – The stock has underperformed slightly or remained stagnant.
        - **30-40**: Slightly Underperforming – The stock is growing but at a slower pace than the market average.
        - **40-50**: Average Investment – The stock has performed in line with market averages.
        - **50-60**: Slightly Above Average – The stock is performing better than market benchmarks.
        - **60-70**: Good Investment – The stock has performed well, exceeding market expectations.
        - **70-80**: Very Good Investment – The stock has shown excellent growth.
        - **80-90**: Great Investment – The stock has delivered exceptional returns with minimal risk.
        - **90-100**: Outstanding Investment – The stock has significantly outperformed expectations with minimal risk.
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

    Please provide a score from 0-100 and a brief explanation of why the investment falls within that range.
    """

    scoring = get_answer(prompt, info)
    return scoring