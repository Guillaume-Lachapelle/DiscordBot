import discord

async def create_poll(ctx, question, options):
    if len(options) > 10:
        await ctx.followup.send("You can only have a maximum of 10 options.")
        return
    if len(options) < 2:
        await ctx.followup.send("You need at least 2 options.")
        return
    if len(question) > 256:
        await ctx.followup.send("Your question must be less than 256 characters.")
        return
    reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
    embed = discord.Embed(description="\n".join([f"{reactions[idx]} {option}" for idx, option in enumerate(options)]))
    await ctx.response.defer()
    poll = await ctx.followup.send(f":bar_chart: **{question}**", embed=embed)
    for reaction in reactions[:len(options)]:
        await poll.add_reaction(reaction)