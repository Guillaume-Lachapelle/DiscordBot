"""Poll command handlers."""

#region Imports

import discord
from typing import List
from datetime import timedelta

#endregion


#region Commands

async def create_poll(ctx: discord.Interaction, question: str, options: List[str], allow_multiselect: bool = False, duration_hours: int = 24) -> None:
    """Create a poll with given question and options.
    
    Args:
        ctx: Discord context
        question: Poll question
        options: List of poll options
        allow_multiselect: Whether to allow multiple selections
        duration_hours: Poll duration in hours (default: 24)
    """
    
    await ctx.response.defer()

    question = question.strip() if question else ""
    clean_options = [option.strip() for option in options if option and option.strip()]

    if not question:
        await ctx.followup.send("Please provide a poll question.")
        return

    if len(options) > 10:
        await ctx.followup.send("Please provide no more than 10 options.")
        return
    if len(clean_options) < 2:
        await ctx.followup.send("Please provide at least 2 options.")
        return
    if len(question) > 256:
        await ctx.followup.send("Please keep the question under 256 characters.")
        return
    
    # Create native Discord poll with configurable duration
    poll = discord.Poll(question=question, duration=timedelta(hours=duration_hours), multiple=allow_multiselect)
    for option in clean_options:
        poll.add_answer(text=option)
    
    await ctx.followup.send(poll=poll)

#endregion
