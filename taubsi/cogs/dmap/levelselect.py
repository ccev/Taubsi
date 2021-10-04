from __future__ import annotations
import discord
from typing import TYPE_CHECKING

from taubsi.core import bot

if TYPE_CHECKING:
    from taubsi.cogs.dmap.map import Map


class LevelSelect(discord.ui.Select):
    def __init__(self, dmap: Map):
        self.available_levels = [1, 3, 5, 6]
        super().__init__(placeholder="Select Raid levels to display", min_values=0,
                         max_values=len(self.available_levels), row=0)

        self.dmap = dmap
        for level in self.available_levels:
            self.options.append(discord.SelectOption(
                label=f"Level {level}", value=str(level), description=f"Zeige Level {level} Raid"
            ))

    async def callback(self, interaction: discord.Interaction):
        if not self.dmap.is_author(interaction.user.id):
            return
        self.dmap.start_load()
        for option in self.options:
            option.default = option.value in self.values
        levels = list(map(int, self.values))
        self.dmap.levels = levels
        await self.dmap.update(interaction)
