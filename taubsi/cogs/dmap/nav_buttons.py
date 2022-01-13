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
        await self.dmap.edit()


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
        self.multipliers = [0.5, 1, 2, 3]
        for multiplier in self.multipliers.copy():
            new_multi = self.multipliers.pop(0)
            self.multipliers.append(new_multi)
            if multiplier == dmap.user_settings.move_multiplier:
                break
        self.dmap = dmap
        super().__init__(style=discord.ButtonStyle.grey,
                         label=self.get_label(),
                         row=DEFAULT_ROW + 2)

    def get_label(self):
        multi = self.dmap.user_settings.move_multiplier
        if multi != 0.5:
            multi = int(multi)
        return bot.translate("dmap_speed").format(multi)

    async def callback(self, interaction: discord.Interaction):
        multiplier = self.multipliers.pop(0)
        self.multipliers.append(multiplier)
        self.dmap.user_settings.move_multiplier = multiplier
        self.label = self.get_label()
        await self.dmap.edit()
        await self.dmap.user_settings.update_db()


class StartRaidButton(discord.ui.Button):
    def __init__(self, dmap: MapMenu):
        super().__init__(style=discord.ButtonStyle.green, label=bot.translate("dmap_start_raid"), row=DEFAULT_ROW + 2)
        self.dmap = dmap

    async def callback(self, interction: discord.Interaction):
        self.dmap.set_page(self.dmap.start_raid_page)
        await self.dmap.edit()


class SettingsButton(discord.ui.Button):
    def __init__(self, dmap: MapMenu):
        super().__init__(style=discord.ButtonStyle.grey, emoji=bot.config.DMAP_EMOJIS["settings"], row=DEFAULT_ROW + 2)
        self.dmap = dmap

    async def callback(self, interaction: discord.Interaction):
        self.dmap.set_page(self.dmap.settings_page)
        await self.dmap.edit()


class UpButton(BaseMapControlButton):
    def __init__(self, dmap: MapMenu):
        super().__init__(dmap, "up")

    async def callback(self, interaction: discord.Interaction):
        self.dmap.user_settings.lat += self.dmap.get_lat_offset()
        await self.dmap.update(interaction)
        await self.dmap.user_settings.update_db()


class LeftButton(BaseMapControlButton):
    def __init__(self, dmap: MapMenu):
        super().__init__(dmap, "left", 3)

    async def callback(self, interaction: discord.Interaction):
        self.dmap.user_settings.lon -= self.dmap.get_lon_offset()
        await self.dmap.update(interaction)
        await self.dmap.user_settings.update_db()


class DownButton(BaseMapControlButton):
    def __init__(self, dmap: MapMenu):
        super().__init__(dmap, "down", 3)

    async def callback(self, interaction: discord.Interaction):
        self.dmap.user_settings.lat -= self.dmap.get_lat_offset()
        await self.dmap.update(interaction)
        await self.dmap.user_settings.update_db()


class RightButton(BaseMapControlButton):
    def __init__(self, dmap: MapMenu):
        super().__init__(dmap, "right", 3)

    async def callback(self, interaction: discord.Interaction):
        self.dmap.user_settings.lon += self.dmap.get_lon_offset()
        await self.dmap.update(interaction)
        await self.dmap.user_settings.update_db()


class ZoomInButton(BaseMapControlButton):
    def __init__(self, dmap: MapMenu):
        super().__init__(dmap, "in")

    async def callback(self, interaction: discord.Interaction):
        self.dmap.user_settings.zoom += 0.25 * self.dmap.user_settings.move_multiplier
        await self.dmap.update(interaction)
        await self.dmap.user_settings.update_db()


class ZoomOutButton(BaseMapControlButton):
    def __init__(self, dmap: MapMenu):
        super().__init__(dmap, "out", 3)

    async def callback(self, interaction: discord.Interaction):
        self.dmap.user_settings.zoom -= 0.25 * self.dmap.user_settings.move_multiplier
        await self.dmap.update(interaction)
        await self.dmap.user_settings.update_db()
