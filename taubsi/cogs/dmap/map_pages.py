from __future__ import annotations
from typing import List, TYPE_CHECKING
import discord

from taubsi.cogs.dmap.nav_buttons import (EmptyButton, MultiplierButton, UpButton, LeftButton, DownButton,
                                          RightButton, ZoomInButton, ZoomOutButton, SettingsButton, BackToNavButton,
                                          StartRaidButton)
from taubsi.cogs.dmap.areaselect import AreaSelect
from taubsi.cogs.dmap.levelselect import LevelSelect
from taubsi.cogs.dmap.settings_items import StyleSelect, IconSelect, IncIconSizeButton, DecIconSizeButton

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
            dec_button, inc_button,
            BackToNavButton(map_menu)
        ]

    def add_to_embed(self):
        self.map_menu.extra_embed = discord.Embed(
            title="Settings",
            description=(
                f"Map Style: **{self.map_menu.user_settings.style.name}**\n"
                f"Icons: **{self.map_menu.user_settings.iconset.value.name}**\n"
                f"Icon size: **{round(self.map_menu.user_settings.marker_multiplier, 1)}x**"
            )
        )


class StartRaidPage(MapPage):
    pass
