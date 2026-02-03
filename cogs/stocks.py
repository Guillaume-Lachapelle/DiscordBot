"""Stock commands cog - Stock ticker lookup and data retrieval."""

#region Imports

import os
import discord
from discord import app_commands
from discord.ext import commands
import logging

import stock_commands
from shared.error_helpers import send_error_followup
from shared.config import BotConfig

#endregion


#region Setup

logger = logging.getLogger(__name__)

#endregion


class StockCog(commands.Cog):
    """Stock market data commands."""
    
    def __init__(self, bot: commands.Bot):
        """Initialize the StockCog.
        
        Args:
            bot: The Discord bot instance.
        """
        self.bot = bot
    
    #region Commands
    
    @app_commands.command(name="stock-ticker", description="Get the stock ticker of a company")
    @app_commands.checks.cooldown(BotConfig.STOCK_TICKER_COOLDOWN_RATE, BotConfig.STOCK_TICKER_COOLDOWN_PER_SECONDS)
    @app_commands.describe(company="Company name to look up")
    async def stock_ticker(self, interaction: discord.Interaction, company: str):
        """Find a stock ticker for a company name.

        Args:
            interaction: Discord interaction context.
            company: Company name to search.
        """
        try:
            await interaction.response.defer()
            ticker = await stock_commands.find_ticker(company)
            await interaction.followup.send(ticker)
        except ValueError as e:
            await interaction.followup.send(str(e))
        except Exception as e:
            logger.exception("Error getting stock ticker")
            await send_error_followup(interaction, "get the stock ticker")
    
    @app_commands.command(name="stock-info", description="Get historical information about a stock")
    @app_commands.checks.cooldown(BotConfig.STOCK_INFO_COOLDOWN_RATE, BotConfig.STOCK_INFO_COOLDOWN_PER_SECONDS)
    @app_commands.describe(ticker="Stock ticker symbol (e.g., AAPL)")
    async def stock_info(self, interaction: discord.Interaction, ticker: str):
        """Retrieve stock data for a ticker and send a CSV file.

        Args:
            interaction: Discord interaction context.
            ticker: Stock ticker symbol.
        """
        try:
            await interaction.response.defer()
            await stock_commands.generate_data(ticker)
        except ValueError as e:
            await interaction.followup.send(str(e))
            return
        except Exception as e:
            logger.exception("Error getting stock information")
            await send_error_followup(interaction, "get stock information")
            return
        
        if os.path.exists('stocks.csv'):
            with open('stocks.csv', 'rb') as f:
                file = discord.File(f)
                await interaction.followup.send(file=file)
        
        if os.path.exists('stocks.csv'):
            os.remove('stocks.csv')
    
    #endregion


async def setup(bot: commands.Bot):
    """Load the StockCog.
    
    Args:
        bot: The Discord bot instance.
    """
    await bot.add_cog(StockCog(bot))
