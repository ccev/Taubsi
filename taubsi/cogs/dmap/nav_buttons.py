from __future__ import annotations
from typing import TYPE_CHECKING
import discord

from taubsi.core import bot

if TYPE_CHECKING:
    from taubsi.cogs.dmap.mapmenu import MapMenu

DEFAULT_ROW = 2


class BackToNavButton(discord.ui.Button):
    def __init__(self, dmap: MapMenu, style: discord.ButtonStyle = discord.ButtonStyle.blurple):
        super().__init__(style=style, label=bot.translate("dmap_back"), row=4)
        self.dmap = dmap

    async def callback(self, interaction: discord.Interaction):
        self.dmap.set_page(self.dmap.map_nav_page)
        await self.dmap.edit(interaction)


class BaseMapControlButton(discord.ui.Button):
    def __init__(self, dmap: MapMenu, label: str, row: int = DEFAULT_ROW):
        emoji = bot.config.DMAP_EMOJIS[label]
        super().__init__(style=discord.ButtonStyle.blurple, emoji=emoji, row=row)
        self.dmap = dmap


class EmptyButton(discord.ui.Button):
    def __init__(self, custom_id: int):
        super().__init__(style=discord.ButtonStyle.blurple, emoji=bot.config.DMAP_EMOJIS["blank"], disabled=True,
                         custom_id=str(custom_id), row=DEFAULT_ROW)


class MultiplierButton(discord.ui.Button):
    def __init__(self, dmap: MapMenu):
        self.multipliers = [1, 0.5, 3, 2]
        super().__init__(style=discord.ButtonStyle.grey,
                         label=bot.translate("dmap_speed").format(self.multipliers[0]),
                         custom_id="multiplier", row=DEFAULT_ROW + 2)
        self.dmap = dmap

    async def callback(self, interaction: discord.Interaction):
        multiplier = self.multipliers.pop()
        self.multipliers.insert(0, multiplier)
        self.dmap.multiplier = multiplier
        self.label = "Speed: " + str(multiplier) + "x"
        await self.dmap.edit(interaction)


class StartRaidButton(discord.ui.Button):
    def __init__(self, dmap: MapMenu):
        super().__init__(style=discord.ButtonStyle.green, label=bot.translate("dmap_start_raid"), row=DEFAULT_ROW + 2)
        self.dmap = dmap

    async def callback(self, interction: discord.Interaction):
        self.dmap.set_page(self.dmap.start_raid_page)
        await self.dmap.edit(interction)


class SettingsButton(discord.ui.Button):
    def __init__(self, dmap: MapMenu):
        super().__init__(style=discord.ButtonStyle.grey, emoji=bot.config.DMAP_EMOJIS["settings"], row=DEFAULT_ROW + 2)
        self.dmap = dmap

    async def callback(self, interaction: discord.Interaction):
        self.dmap.set_page(self.dmap.settings_page)
        await self.dmap.edit(interaction)


class UpButton(BaseMapControlButton):
    def __init__(self, dmap: MapMenu):
        super().__init__(dmap, "up")

    async def callback(self, interaction: discord.Interaction):
        self.dmap.user_settings.lat += self.dmap.get_lat_offset()
        await self.dmap.update(interaction)


class LeftButton(BaseMapControlButton):
    def __init__(self, dmap: MapMenu):
        super().__init__(dmap, "left", 3)

    async def callback(self, interaction: discord.Interaction):
        self.dmap.user_settings.lon -= self.dmap.get_lon_offset()
        await self.dmap.update(interaction)


class DownButton(BaseMapControlButton):
    def __init__(self, dmap: MapMenu):
        super().__init__(dmap, "down", 3)

    async def callback(self, interaction: discord.Interaction):
        self.dmap.user_settings.lat -= self.dmap.get_lat_offset()
        await self.dmap.update(interaction)


class RightButton(BaseMapControlButton):
    def __init__(self, dmap: MapMenu):
        super().__init__(dmap, "right", 3)

    async def callback(self, interaction: discord.Interaction):
        self.dmap.user_settings.lon += self.dmap.get_lon_offset()
        await self.dmap.update(interaction)


class ZoomInButton(BaseMapControlButton):
    def __init__(self, dmap: MapMenu):
        super().__init__(dmap, "in")

    async def callback(self, interaction: discord.Interaction):
        self.dmap.user_settings.zoom += 0.25 * self.dmap.user_settings.move_multiplier
        await self.dmap.update(interaction)


class ZoomOutButton(BaseMapControlButton):
    def __init__(self, dmap: MapMenu):
        super().__init__(dmap, "out", 3)

    async def callback(self, interaction: discord.Interaction):
        self.dmap.user_settings.zoom -= 0.25 * self.dmap.user_settings.move_multiplier
        await self.dmap.update(interaction)
