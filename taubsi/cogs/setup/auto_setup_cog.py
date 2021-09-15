import discord
from discord.ext import commands, tasks
from taubsi.utils.logging import logging
from taubsi.taubsi_objects import tb
from taubsi.cogs.setup.objects import TaubsiUser
from taubsi.utils.checks import is_guild
from taubsi.cogs.setup.errors import *
from taubsi.utils.enums import Team


log = logging.getLogger("AutoSetup")


class AutoSetup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.autoupdate_loop.start()

    async def reponse(self, ctx, text):
        embed = discord.Embed(description=text, color=3092790)
        await ctx.send(embed=embed)

    @tasks.loop(hours=1)
    async def autoupdate_loop(self):
        query = (
            "select user_id, u.name, t.level, t.team from users u "
            "left join mad.cev_trainer t on t.name = u.ingame_name "
            "where t.level > u.level or t.team != u.team_id"
        )
        result = await tb.intern_queries.execute(query)
        if len(result) == 0:
            return

        for user_id, name, level, team in result:
            if level is None or team is None:
                continue
            user = TaubsiUser()
            user.from_db(user_id, team_id=team, level=level, name=name)

            await user.update()
            log.info(f"Auto-updating {name} {user_id} (L{level}) (T{team})")


def setup(bot):
    bot.add_cog(AutoSetup(bot))
