"""Poll command handlers."""

#region Imports

import discord
from typing import List

#endregion


#region Commands

async def create_poll(ctx: discord.Interaction, question: str, options: List[str]) -> None:
    """Create a poll with given question and options.
    
    Args:
        ctx: Discord context
        question: Poll question
        options: List of poll options
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
    reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
    embed = discord.Embed(description="\n".join([f"{reactions[idx]} {option}" for idx, option in enumerate(clean_options)]))
    poll = await ctx.followup.send(f":bar_chart: **{question}**", embed=embed)
    for reaction in reactions[:len(clean_options)]:
        await poll.add_reaction(reaction)

#endregion
