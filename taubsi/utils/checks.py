from taubsi.taubsi_objects import tb


async def is_guild(ctx):
    return ctx.guild.id in tb.guild_ids
