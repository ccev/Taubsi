from __future__ import annotations
from typing import TYPE_CHECKING
import discord
from taubsi.core import bot
from taubsi.core.uicons import IconSet
from taubsi.cogs.dmap.usersettings import SizePreset

if TYPE_CHECKING:
    from taubsi.cogs.dmap.mapmenu import MapMenu


class StyleSelect(discord.ui.Select):
    def __init__(self, dmap: MapMenu):
        super().__init__(placeholder="Choose a map style",
                         min_values=0,
                         max_values=1,
                         row=0)
        for i, style in enumerate(bot.config.DMAP_STYLES):
            label = f"Map Style: {style.name}"
            self.options.append(discord.SelectOption(label=label, value=style.id, default=i == 0))
        self.dmap = dmap

    async def callback(self, interaction: discord.Interaction):
        value = self.values[0]
        for option in self.options:
            if option.value == value:
                option.default = True
                self.dmap.style_name = option.label
            else:
                option.default = False
        self.dmap.user_settings.style = [s for s in bot.config.DMAP_STYLES if s.id == value][0]
        await self.dmap.update(interaction)


class SizeSelect(discord.ui.Select):
    def __init__(self, dmap: MapMenu):
        super().__init__(placeholder="Choose a map size",
                         min_values=0,
                         max_values=1,
                         row=1)
        for size in SizePreset:
            label = f"Map size: {size.value.name}"
            self.options.append(discord.SelectOption(
                label=label, value=size.name, default=size.value.name == dmap.user_settings.size.name
            ))
        self.dmap = dmap

    async def callback(self, interaction: discord.Interaction):
        size_name = self.values[0]
        new_size = SizePreset[size_name]
        self.dmap.user_settings.size = new_size.value
        for option in self.options:
            option.default = option.value == new_size.name
        await self.dmap.update(interaction)


class IconSelect(discord.ui.Select):
    def __init__(self, dmap: MapMenu):
        super().__init__(placeholder="Choose an iconset",
                         min_values=0,
                         max_values=1,
                         row=2)
        self.custom_id += "s"
        for i, iconset in enumerate(IconSet):
            label = f"Icons: {iconset.value.name}"
            self.options.append(discord.SelectOption(label=label, value=iconset.name, default=i == 0))
        self.dmap = dmap

    async def callback(self, interaction: discord.Interaction):
        iconset_name = self.values[0]
        self.dmap.user_settings.iconset = IconSet[iconset_name]
        for option in self.options:
            option.default = option.value == iconset_name
        await self.dmap.update(interaction)


class IconSizeButton(discord.ui.Button):
    label: str
    style = discord.ButtonStyle.grey
    row = 3
    min_size = 0.5
    max_size = 2
    dmap: MapMenu

    def __init__(self, dmap: MapMenu):
        self.dmap = dmap
        super().__init__(label=self.label,
                         style=self.style,
                         row=self.row)


class IncIconSizeButton(IconSizeButton):
    label = "Größere Icons"
    dec_button: DecIconSizeButton

    async def callback(self, interaction: discord.Interaction):
        self.dmap.user_settings.marker_multiplier += 0.1
        self.dec_button.disabled = False
        if self.dmap.user_settings.marker_multiplier >= self.max_size:
            self.disabled = True
        await self.dmap.update(interaction)


class DecIconSizeButton(IconSizeButton):
    label = "Kleinere Icons"
    inc_button: IncIconSizeButton

    async def callback(self, interaction: discord.Interaction):
        self.dmap.user_settings.marker_multiplier -= 0.1
        self.inc_button.disabled = False
        if self.min_size <= self.dmap.user_settings.marker_multiplier:
            self.disabled = True
        await self.dmap.update(interaction)
