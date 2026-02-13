"""AI commands cog - Question answering with Google Gemini."""

#region Imports

import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
import logging

import ai_commands
from shared.error_helpers import send_user_message
from shared.config import BotConfig
from shared.pagination import paginate_text, send_paginated_message

#endregion


#region Setup

logger = logging.getLogger(__name__)

QUESTION_MODEL_CHOICES = [
    app_commands.Choice(name=model, value=model) for model in ai_commands.FALLBACK_MODELS
]

#endregion


class AICog(commands.GroupCog, name="ai", description="AI commands"):
    """AI-powered question answering commands."""
    
    def __init__(self, bot: commands.Bot):
        """Initialize the AICog.
        
        Args:
            bot: The Discord bot instance.
        """
        self.bot = bot
    
    #region Commands
    
    @app_commands.command(
        name="question",
        description="Ask a question and the bot will try to answer it",
    )
    @app_commands.checks.cooldown(BotConfig.QUESTION_COOLDOWN_RATE, BotConfig.QUESTION_COOLDOWN_PER_SECONDS)
    @app_commands.describe(question="Prompt for the model", model="Model to use (optional)")
    @app_commands.choices(model=QUESTION_MODEL_CHOICES)
    async def question(self, interaction: discord.Interaction, question: str, model: Optional[app_commands.Choice[str]] = None):
        """Generate an AI response for a user prompt.

        Args:
            interaction: Discord interaction context.
            question: Prompt to send to the model.
            model: Optional model choice.
        """
        try:
            if not question.strip():
                await interaction.response.send_message("Please enter a question.", ephemeral=True)
                return
            await interaction.response.defer()
            response = await ai_commands.generate_response(interaction, question, model)
            pages = paginate_text(response, max_length=1800)
            await send_paginated_message(interaction, pages, ephemeral=False)
        except Exception as e:
            logger.exception("Error generating AI response")
            await send_user_message("Sorry, I couldn't generate a response. Please try again.", ctx=interaction, ephemeral=True)

    #endregion


async def setup(bot: commands.Bot):
    """Load the AICog.
    
    Args:
        bot: The Discord bot instance.
    """
    await bot.add_cog(AICog(bot))
