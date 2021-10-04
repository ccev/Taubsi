from __future__ import annotations
from typing import TYPE_CHECKING
import discord

from taubsi.core import bot
from taubsi.cogs.dmap.settings import Settings

if TYPE_CHECKING:
    from taubsi.cogs.dmap.map import Map

DEFAULT_ROW = 2


class BaseMapControlButton(discord.ui.Button):
    def __init__(self, dmap: Map, label: str, row: int = DEFAULT_ROW):
        emoji = bot.config.DMAP_EMOJIS[label]
        super().__init__(style=discord.ButtonStyle.blurple, emoji=emoji, row=row)
        self.dmap = dmap

    async def _callback(self, interaction: discord.Interaction):
        if not self.dmap.is_author(interaction.user.id):
            return
        self.dmap.start_load()
        await self.dmap.update(interaction)


class EmptyButton(discord.ui.Button):
    def __init__(self, custom_id: int):
        super().__init__(style=discord.ButtonStyle.blurple, emoji=bot.config.DMAP_EMOJIS["blank"], disabled=True,
                         custom_id=str(custom_id), row=DEFAULT_ROW)


class MultiplierButton(discord.ui.Button):
    def __init__(self, dmap: Map):
        self.multipliers = [1, 0.5, 3, 2]
        super().__init__(style=discord.ButtonStyle.grey, label="Speed: " + str(self.multipliers[0]) + "x",
                         custom_id="multiplier", row=DEFAULT_ROW + 2)
        self.dmap = dmap

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if not self.dmap.is_author(interaction.user.id):
            return
        multiplier = self.multipliers.pop()
        self.multipliers.insert(0, multiplier)
        self.dmap.multiplier = multiplier
        self.label = "Speed: " + str(multiplier) + "x"
        await self.dmap.edit(interaction)


class SettingsButton(discord.ui.Button):
    def __init__(self, dmap: Map):
        super().__init__(style=discord.ButtonStyle.grey, label="Settings", row=DEFAULT_ROW + 2)
        self.dmap = dmap

    async def callback(self, interaction: discord.Interaction):
        settings = Settings(self.dmap)
        await settings.send(interaction.response)


class UpButton(BaseMapControlButton):
    def __init__(self, dmap: Map):
        super().__init__(dmap, "up")

    async def callback(self, interaction: discord.Interaction):
        self.dmap.lat += self.dmap.get_lat_offset()
        await self._callback(interaction)


class LeftButton(BaseMapControlButton):
    def __init__(self, dmap: Map):
        super().__init__(dmap, "left", 3)

    async def callback(self, interaction: discord.Interaction):
        self.dmap.lon -= self.dmap.get_lon_offset()
        await self._callback(interaction)


class DownButton(BaseMapControlButton):
    def __init__(self, dmap: Map):
        super().__init__(dmap, "down", 3)

    async def callback(self, interaction: discord.Interaction):
        self.dmap.lat -= self.dmap.get_lat_offset()
        await self._callback(interaction)


class RightButton(BaseMapControlButton):
    def __init__(self, dmap: Map):
        super().__init__(dmap, "right", 3)

    async def callback(self, interaction: discord.Interaction):
        self.dmap.lon += self.dmap.get_lon_offset()
        await self._callback(interaction)


class ZoomInButton(BaseMapControlButton):
    def __init__(self, dmap: Map):
        super().__init__(dmap, "in")

    async def callback(self, interaction: discord.Interaction):
        self.dmap.zoom += 0.25 * self.dmap.multiplier
        await self._callback(interaction)


class ZoomOutButton(BaseMapControlButton):
    def __init__(self, dmap: Map):
        super().__init__(dmap, "out", 3)

    async def callback(self, interaction: discord.Interaction):
        self.dmap.zoom -= 0.25 * self.dmap.multiplier
        await self._callback(interaction)
