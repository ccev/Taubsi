async def is_guild(ctx):
    return ctx.guild.id in ctx.bot.server_ids


async def is_admin(ctx):
    return ctx.author.id in ctx.bot.config.ADMIN_IDS
