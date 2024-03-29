from __future__ import annotations
from typing import List, TYPE_CHECKING, Optional
import discord
import arrow

from taubsi.cogs.dmap.nav_buttons import (EmptyButton, MultiplierButton, UpButton, LeftButton, DownButton,
                                          RightButton, ZoomInButton, ZoomOutButton, SettingsButton, BackToNavButton,
                                          StartRaidButton)
from taubsi.cogs.dmap.areaselect import AreaSelect
from taubsi.cogs.dmap.levelselect import LevelSelect
from taubsi.cogs.dmap.settings_items import StyleSelect, IconSelect, IncIconSizeButton, DecIconSizeButton, ResetButton
from taubsi.cogs.dmap.start_items import RaidSelect, TimeSelect, StartButton
from taubsi.core import Gym, bot

if TYPE_CHECKING:
    from taubsi.cogs.dmap.mapmenu import MapMenu


class MapPage:
    map_menu: MapMenu
    items: List[discord.ui.Item]

    def __init__(self, map_menu: MapMenu):
        self.map_menu = map_menu

    def add_to_embed(self):
        pass


class MapNavPage(MapPage):
    def __init__(self, map_menu: MapMenu):
        super().__init__(map_menu)
        self.items = [
            LevelSelect(map_menu),
            AreaSelect(map_menu),
            EmptyButton(0), UpButton(map_menu), EmptyButton(1), ZoomInButton(map_menu),
            LeftButton(map_menu), DownButton(map_menu), RightButton(map_menu), ZoomOutButton(map_menu),
            StartRaidButton(map_menu), SettingsButton(map_menu), MultiplierButton(map_menu)
        ]


class SettingsPage(MapPage):
    def __init__(self, map_menu: MapMenu):
        super().__init__(map_menu)
        inc_button = IncIconSizeButton(map_menu)
        dec_button = DecIconSizeButton(map_menu)
        inc_button.dec_button = dec_button
        dec_button.inc_button = inc_button
        self.items = [
            StyleSelect(map_menu),
            IconSelect(map_menu),
            dec_button, inc_button, ResetButton(map_menu), BackToNavButton(map_menu)
        ]

    def add_to_embed(self):
        style = bot.translate("dmap_style").format(self.map_menu.user_settings.style.name)
        icons = bot.translate("dmap_icons").format(self.map_menu.user_settings.iconset.value.name)
        icon_size = bot.translate("dmap_icon_size").format(round(self.map_menu.user_settings.marker_multiplier, 1))

        embed = discord.Embed(title=bot.translate("Settings"),
                              description=style + "\n" + icons + "\n" + icon_size)
        self.map_menu.extra_embed = embed


class StartRaidPage(MapPage):
    gym: Optional[Gym] = None
    start: Optional[arrow.Arrow] = None

    def __init__(self, dmap: MapMenu):
        super().__init__(map_menu=dmap)
        self.start_button = StartButton(self)
        self.time_select = TimeSelect(self)
        self.raid_select = RaidSelect(self)
        self.items = [
            self.raid_select,
            self.time_select,
            self.start_button, BackToNavButton(dmap, discord.ButtonStyle.grey)
        ]

    async def set_raid(self, gym: Gym, interaction: discord.Interaction):
        self.start_button.disabled = True
        self.start = None
        self.time_select.set_times(gym)
        self.gym = gym
        await self.map_menu.edit()

    async def set_time(self, time: arrow.Arrow, interaction: discord.Interaction):
        self.start_button.disabled = False
        self.start = time
        await self.map_menu.edit()

    def add_to_embed(self):
        text = ""
        if self.gym:
            text += bot.translate("dmap_gym_").format(self.gym.name) + "\n"
        if self.start:
            text += bot.translate("dmap_start_").format(self.start.strftime(bot.translate('timeformat_short')))
        self.map_menu.extra_embed = discord.Embed(
            title=bot.translate("dmap_start_raid"),
            description=text
        )
