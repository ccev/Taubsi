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
        super().__init__(placeholder=bot.translate("dmap_select_style"),
                         min_values=1,
                         max_values=1,
                         row=0)

        self.dmap = dmap
        for i, style in enumerate(bot.config.DMAP_STYLES):
            label = bot.translate("dmap_style_option").format(style.name)
            self.options.append(discord.SelectOption(label=label, value=style.id,
                                                     default=style.id == self.dmap.user_settings.style.id))

    async def callback(self, interaction: discord.Interaction):
        value = self.values[0]
        for option in self.options:
            option.default = option.value == value
        self.dmap.user_settings.style = [s for s in bot.config.DMAP_STYLES if s.id == value][0]
        await self.dmap.update(interaction)
        await self.dmap.user_settings.update_db()


class SizeSelect(discord.ui.Select):
    def __init__(self, dmap: MapMenu):
        super().__init__(placeholder="Choose a map size",
                         min_values=1,
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
        await self.dmap.user_settings.update_db()


class IconSelect(discord.ui.Select):
    def __init__(self, dmap: MapMenu):
        super().__init__(placeholder=bot.translate("dmap_select_iconset"),
                         min_values=1,
                         max_values=1,
                         row=2)
        for i, iconset in enumerate(IconSet):
            label = bot.translate("dmap_iconset_option").format(iconset.value.name)
            self.options.append(discord.SelectOption(label=label, value=iconset.name,
                                                     default=iconset == dmap.user_settings.iconset))
        self.dmap = dmap

    async def callback(self, interaction: discord.Interaction):
        iconset_name = self.values[0]
        self.dmap.user_settings.iconset = IconSet[iconset_name]
        for option in self.options:
            option.default = option.value == iconset_name
        await self.dmap.update(interaction)
        await self.dmap.user_settings.update_db()


class IconSizeButton(discord.ui.Button):
    label: str
    style = discord.ButtonStyle.grey
    row = 4
    min_size = 0.5
    max_size = 2
    dmap: MapMenu

    def __init__(self, dmap: MapMenu):
        self.dmap = dmap
        super().__init__(label=self.label,
                         style=self.style,
                         row=self.row)
        self.set_disabled()

    def set_disabled(self):
        pass


class IncIconSizeButton(IconSizeButton):
    label = bot.translate("dmap_bigger_icons")
    dec_button: DecIconSizeButton

    def set_disabled(self):
        self.disabled = self.dmap.user_settings.marker_multiplier >= self.max_size

    async def callback(self, interaction: discord.Interaction):
        self.dmap.user_settings.marker_multiplier += 0.1
        self.dec_button.disabled = False
        self.set_disabled()
        await self.dmap.update(interaction)
        await self.dmap.user_settings.update_db()


class DecIconSizeButton(IconSizeButton):
    label = bot.translate("dmap_smaller_icons")
    inc_button: IncIconSizeButton

    def set_disabled(self):
        self.disabled = self.min_size > self.dmap.user_settings.marker_multiplier

    async def callback(self, interaction: discord.Interaction):
        self.dmap.user_settings.marker_multiplier -= 0.1
        self.inc_button.disabled = False
        self.set_disabled()
        await self.dmap.update(interaction)
        await self.dmap.user_settings.update_db()
