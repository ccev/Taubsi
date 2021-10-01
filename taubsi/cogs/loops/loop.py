from __future__ import annotations
from typing import TYPE_CHECKING

import arrow
from discord.ext import tasks, commands

from taubsi.core import log

if TYPE_CHECKING:
    from taubsi.core.bot import TaubsiBot


class Loop(commands.Cog):
    def __init__(self, bot):
        self.bot: TaubsiBot = bot
        self._last_pogodata_update = arrow.utcnow()

        self.pogodata_loop.start()
        self.gym_loop.start()

    @tasks.loop(hours=6)
    async def pogodata_loop(self):
        if arrow.utcnow() > self._last_pogodata_update.shift(hours=3):
            self.bot.reload_pogodata()
            log.info("Reloaded PogoData")

    @tasks.loop(seconds=10)
    async def gym_loop(self):
        for server in self.bot.servers:
            await server.update_gyms()


def setup(bot):
    bot.add_cog(Loop(bot))
