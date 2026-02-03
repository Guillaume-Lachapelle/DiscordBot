"""AI commands cog - Question answering with Google Gemini."""

#region Imports

import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
import logging

import ai_commands
from shared.error_helpers import send_error_followup
from shared.config import BotConfig

#endregion


#region Setup

logger = logging.getLogger(__name__)

QUESTION_MODEL_CHOICES = [
    app_commands.Choice(name=model, value=model) for model in ai_commands.FALLBACK_MODELS
]

#endregion


class AICog(commands.Cog):
    """AI-powered question answering commands."""
    
    def __init__(self, bot: commands.Bot):
        """Initialize the AICog.
        
        Args:
            bot: The Discord bot instance.
        """
        self.bot = bot
    
    #region Commands
    
    @app_commands.command(name="question", description="Ask a question and the bot will try to answer it")
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
                await interaction.response.send_message("Please enter a question.")
                return
            await interaction.response.defer()
            response = await ai_commands.generate_response(question, model)
            if len(response) <= 2000:
                await interaction.followup.send(response)
            else:
                # Split the response into chunks of 2000 characters
                chunks = [response[i:i + 2000] for i in range(0, len(response), 2000)]
                # Edit the original message with the first chunk
                await interaction.edit_original_response(content=chunks[0])
                # Send the rest of the chunks as follow-up messages
                for chunk in chunks[1:]:
                    await interaction.followup.send(chunk)
        except Exception as e:
            logger.exception("Error generating AI response")
            await send_error_followup(interaction, "generate a response")
    
    #endregion


async def setup(bot: commands.Bot):
    """Load the AICog.
    
    Args:
        bot: The Discord bot instance.
    """
    await bot.add_cog(AICog(bot))
