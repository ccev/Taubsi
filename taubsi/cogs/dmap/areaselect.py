from __future__ import annotations
import discord
from typing import TYPE_CHECKING

from taubsi.core import bot

if TYPE_CHECKING:
    from taubsi.cogs.dmap.mapmenu import MapMenu


class AreaSelect(discord.ui.Select):
    def __init__(self, dmap: MapMenu):
        super().__init__(placeholder=bot.translate("dmap_jump_to_an_area"),
                         min_values=0, max_values=1, row=1)

        self.dmap = dmap
        for i, area in enumerate(bot.config.DMAP_AREAS):
            self.options.append(discord.SelectOption(
                label=area.name, value=str(i)
            ))

    async def callback(self, interaction: discord.Interaction):
        value = int(self.values[0])
        self.dmap.user_settings.jump_to_area(bot.config.DMAP_AREAS[value])
        await self.dmap.update(interaction)
