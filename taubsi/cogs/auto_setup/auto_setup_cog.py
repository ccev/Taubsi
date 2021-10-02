from typing import TYPE_CHECKING
import discord
from discord.ext import commands, tasks

from taubsi.core import log
from taubsi.cogs.setup.objects import TaubsiUser

if TYPE_CHECKING:
    from taubsi.core import TaubsiBot


class AutoSetup(commands.Cog):
    def __init__(self, bot):
        self.bot: TaubsiBot = bot
        self.autoupdate_loop.start()

    @tasks.loop(hours=1)
    async def autoupdate_loop(self):
        query = (
            "select user_id, u.name, t.level, t.team from users u "
            "left join mad.cev_trainer t on t.name = u.ingame_name "
            "where t.level > u.level or t.team != u.team_id"
        )
        result = await self.bot.mad_db.execute(query, as_dict=False)
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