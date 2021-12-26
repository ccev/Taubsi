from __future__ import annotations
from typing import TYPE_CHECKING

from discord.ext import tasks, commands

from taubsi.core import log
from taubsi.core.uicons import IconSet

if TYPE_CHECKING:
    from taubsi.core.bot import TaubsiBot


class LoopCog(commands.Cog):
    def __init__(self, bot):
        self.bot: TaubsiBot = bot
        self._first_uicon = True
        self._first_pogodata = True

    async def final_init(self):
        self.gym_loop.start()

        self.pogodata_loop.start()
        self.uicon_loop.start()

    @tasks.loop(hours=3)
    async def uicon_loop(self):
        if self._first_uicon:
            self._first_uicon = False
            return
        for iconset in IconSet:
            await iconset.value.reload()

    @tasks.loop(hours=6)
    async def pogodata_loop(self):
        if self._first_pogodata:
            self._first_pogodata = False
            return
        await self.bot.reload_pogodata()
        log.info("Reloaded PogoData")

    @tasks.loop(seconds=10)
    async def gym_loop(self):
        for server in self.bot.servers:
            await server.update_gyms()
