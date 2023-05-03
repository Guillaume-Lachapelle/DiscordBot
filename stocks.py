import pandas as pd
import os
from alpha_vantage.timeseries import TimeSeries

# Key taken from alpha vantage website. Keep this value safe.
api_key = '{your alpha vantage api key}'
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
    