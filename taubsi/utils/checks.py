from taubsi.taubsi_objects import tb

async def is_guild(ctx):
    return ctx.guild in tb.guilds