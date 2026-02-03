"""Stock data retrieval commands."""

#region Imports

import pandas as pd
import os
import re
import logging
import asyncio
from alpha_vantage.timeseries import TimeSeries
from dotenv import load_dotenv
from shared.retry_helpers import run_with_retries
from shared.config import BotConfig

#endregion


#region Setup

# Load environment variables
load_dotenv()

_api_key = os.getenv('ALPHA_VANTAGE_API_KEY')
_ts = TimeSeries(key=_api_key, output_format='pandas')

logger = logging.getLogger(__name__)

#endregion


#region Commands

async def generate_data(my_symbol: str) -> pd.DataFrame:
    """Generate stock data for a symbol and save to CSV.
    
    Args:
        my_symbol: Stock ticker symbol
        
    Returns:
        Pandas dataframe with stock data
    """
    if not my_symbol or not str(my_symbol).strip():
        raise ValueError("Please enter a ticker symbol.")

    symbol = str(my_symbol).strip().upper()
    if not re.match(r"^[A-Z0-9\.\-]{1,10}$", symbol):
        raise ValueError("Please enter a valid ticker symbol (e.g., AAPL).")

    logger.info("Fetching stock data for %s", symbol)
    try:
        data, _meta_data = await run_with_retries(
            lambda: asyncio.wait_for(
                asyncio.to_thread(_ts.get_daily_adjusted, symbol=symbol, outputsize='compact'),
                timeout=BotConfig.STOCK_API_TIMEOUT_SECONDS,
            ),
            retries=2,
            delay_seconds=0.5,
            backoff=2.0,
            retry_exceptions=(asyncio.TimeoutError,),
        )
    except asyncio.TimeoutError:
        raise ValueError("Stock data request timed out. Please try again.")
    if isinstance(data, dict):
        if "Note" in data or "Information" in data:
            raise ValueError("Stock API rate limit reached. Please try again later.")
        if "Error Message" in data:
            raise ValueError("Stock API returned an error for that ticker.")
    if data is None or data.empty:
        raise ValueError("No stock data found for that ticker.")
    data.to_csv('stocks.csv')
    while(not os.path.exists('stocks.csv')):
        pass
    return data

async def find_ticker(my_string: str) -> str:
    """Find stock ticker symbol from search string.
    
    Args:
        my_string: Search string
        
    Returns:
        Ticker symbol string
    """
    if not my_string or not str(my_string).strip():
        raise ValueError("Please enter a company name.")

    logger.info("Searching ticker for company: %s", my_string)
    try:
        ticker = await run_with_retries(
            lambda: asyncio.wait_for(
                asyncio.to_thread(_ts.get_symbol_search, my_string),
                timeout=BotConfig.STOCK_API_TIMEOUT_SECONDS,
            ),
            retries=2,
            delay_seconds=0.5,
            backoff=2.0,
            retry_exceptions=(asyncio.TimeoutError,),
        )
    except asyncio.TimeoutError:
        raise ValueError("Ticker lookup timed out. Please try again.")
    if isinstance(ticker, dict):
        if "Note" in ticker or "Information" in ticker:
            raise ValueError("Stock API rate limit reached. Please try again later.")
        if "Error Message" in ticker:
            raise ValueError("Stock API returned an error for that company name.")
    df = ticker[0]
    if df is None or df.empty:
        raise ValueError("No ticker found for that company name.")
    result = df.iloc[0]['1. symbol']
    return result

#endregion
