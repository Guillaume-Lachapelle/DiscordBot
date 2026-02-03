"""Poll commands cog - Create polls with reactions."""

#region Imports

import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional, Literal

import poll_commands

#endregion


class PollCog(commands.Cog):
    """Poll creation commands."""
    
    def __init__(self, bot: commands.Bot):
        """Initialize the PollCog.
        
        Args:
            bot: The Discord bot instance.
        """
        self.bot = bot
    
    #region Commands
    
    @app_commands.command(name="poll", description="Create a poll")
    @app_commands.describe(
        question="Poll question",
        option1="First option",
        option2="Second option",
        option3="Third option (optional)",
        option4="Fourth option (optional)",
        option5="Fifth option (optional)",
        option6="Sixth option (optional)",
        option7="Seventh option (optional)",
        option8="Eighth option (optional)",
        option9="Ninth option (optional)",
        option10="Tenth option (optional)",
        allow_multiselect="Allow multiple selections (optional)",
        duration="Poll duration (default: 24 hours)"
    )
    async def poll(
        self, 
        interaction: discord.Interaction, 
        question: str, 
        option1: str, 
        option2: str, 
        option3: Optional[str] = None, 
        option4: Optional[str] = None, 
        option5: Optional[str] = None, 
        option6: Optional[str] = None, 
        option7: Optional[str] = None, 
        option8: Optional[str] = None, 
        option9: Optional[str] = None, 
        option10: Optional[str] = None,
        allow_multiselect: bool = False,
        duration: Literal["24 hours", "3 days", "7 days"] = "24 hours"
    ):
        """Create a poll with up to 10 options.

        Args:
            interaction: Discord interaction context.
            question: Poll question text.
            option1: First option.
            option2: Second option.
            option3: Third option (optional).
            option4: Fourth option (optional).
            option5: Fifth option (optional).
            option6: Sixth option (optional).
            option7: Seventh option (optional).
            option8: Eighth option (optional).
            option9: Ninth option (optional).
            option10: Tenth option (optional).
            allow_multiselect: Whether to allow multiple selections.
            duration: Poll duration (default: 24 hours).
        """
        # Convert duration string to hours
        duration_map = {
            "24 hours": 24,
            "3 days": 72,
            "7 days": 168
        }
        duration_hours = duration_map[duration]
        
        options = [
            option for option in (
                option1, option2, option3, option4, option5, 
                option6, option7, option8, option9, option10
            ) if option is not None
        ]
        await poll_commands.create_poll(interaction, question, options, allow_multiselect=allow_multiselect, duration_hours=duration_hours)
    
    #endregion


async def setup(bot: commands.Bot):
    """Load the PollCog.
    
    Args:
        bot: The Discord bot instance.
    """
    await bot.add_cog(PollCog(bot))
