import pandas as pd
import os
from alpha_vantage.timeseries import TimeSeries
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
ts = TimeSeries(key=api_key, output_format='pandas')

async def generate_data(my_symbol):
    data, meta_data = ts.get_daily_adjusted(symbol=my_symbol, outputsize = 'compact')
    data.to_csv('stocks.csv')
    while(not os.path.exists('stocks.csv')):
        pass
    return data

async def find_ticker(my_string):
    ticker = ts.get_symbol_search(my_string)
    df = ticker[0]
    result = df.iloc[0]['1. symbol']
    return result
    