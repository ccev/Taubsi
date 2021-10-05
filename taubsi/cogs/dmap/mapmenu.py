from __future__ import annotations

import math
from typing import List, Optional

import aiohttp
import arrow
import discord

from taubsi.cogs.dmap.map_pages import MapNavPage, SettingsPage, StartRaidPage, MapPage
from taubsi.cogs.dmap.usersettings import UserSettings
from taubsi.core import bot, Gym, log


class MapMenu(discord.ui.View):
    user_settings: UserSettings
    current_page: MapPage

    url: str = bot.config.TILESERVER_URL + "staticmap"
    embed: discord.Embed
    extra_embed: Optional[discord.Embed]
    scale: int = 1
    hit_limit: bool = False
    interaction: discord.Interaction
    gyms: List[Gym]
    display_gyms: List[Gym]

    map_nav_page: MapNavPage
    settings_page: SettingsPage
    start_raid_page: StartRaidPage

    def __init__(self, interaction: discord.Interaction):
        super().__init__(timeout=None)
        self.user_settings = UserSettings.default()

        self.author_id = interaction.user.id
        self.display_gyms = []
        self.interaction = interaction

        server = [s for s in bot.servers if s.id == interaction.guild_id]
        if not server:
            raise
        server = server[0]
        self.gyms = server.gyms
        self.embed = discord.Embed()

        self.map_nav_page = MapNavPage(self)
        self.settings_page = SettingsPage(self)
        self.start_raid_page = StartRaidPage(self)
        self.set_page(self.map_nav_page)

    def set_page(self, page: MapPage):
        self.current_page = page
        self.extra_embed = None
        self.clear_items()
        for item in page.items:
            self.add_item(item)

    @staticmethod
    def _get_marker(gym: Gym, url: str, size: int, y_offset: int = 0, x_offset: int = 0) -> dict:
        return {
            "url": url,
            "latitude": gym.lat,
            "longitude": gym.lon,
            "width": size,
            "height": size,
            "x_offset": x_offset,
            "y_offset": y_offset
        }

    def get_data(self):
        data = {
            "style": self.user_settings.style.id,
            "latitude": self.user_settings.lat,
            "longitude": self.user_settings.lon,
            "zoom": self.user_settings.zoom,
            "width": self.user_settings.size.width,
            "height": self.user_settings.size.height,
            "format": "png",
            "scale": self.scale
        }
        if self.display_gyms:
            # i hate this logic
            markers = []
            for gym in self.display_gyms:
                if len(markers) >= bot.config.DMAP_MARKER_LIMIT:
                    self.hit_limit = True
                    break

                gym_size = self.get_marker_size(26)
                markers.append(self._get_marker(gym=gym,
                                                url=bot.uicons.gym(gym, iconset=self.user_settings.iconset),
                                                size=gym_size,
                                                y_offset=gym_size // -2))

                boss_size = self.get_marker_size(22)
                if gym.raid.boss:
                    boss_marker = self._get_marker(gym=gym,
                                                   url=bot.uicons.pokemon(gym.raid.boss,
                                                                          iconset=self.user_settings.iconset),
                                                   size=boss_size)
                else:
                    boss_marker = self._get_marker(gym=gym,
                                                   url=bot.uicons.egg(gym.raid, iconset=self.user_settings.iconset),
                                                   size=boss_size)
                boss_marker["y_offset"] = - self.get_marker_size(17)
                boss_marker["x_offset"] = - self.get_marker_size(2)
                markers.append(boss_marker)
            data.update({
                "markers": markers
            })
        return data

    def point_to_lat(self, wanted_points):
        # copied from https://help.openstreetmap.org/questions/75611/transform-xy-pixel-values-into-lat-and-long
        c = (256 / (2 * math.pi)) * 2 ** self.user_settings.zoom

        xcenter = c * (math.radians(self.user_settings.lon) + math.pi)
        ycenter = c * (math.pi - math.log(math.tan((math.pi / 4) + math.radians(self.user_settings.lat) / 2)))

        xpoint = xcenter - (self.user_settings.size.width / 2 - wanted_points[0])
        ypoint = ycenter - (self.user_settings.size.height / 2 - wanted_points[1])

        c = (256 / (2 * math.pi)) * 2 ** self.user_settings.zoom
        m = (xpoint / c) - math.pi
        n = -(ypoint / c) + math.pi

        fin_lon = math.degrees(m)
        fin_lat = math.degrees((math.atan(math.e ** n) - (math.pi / 4)) * 2)

        return fin_lat, fin_lon

    def get_bounds(self):
        lat1, lon1 = self.point_to_lat(wanted_points=(0, 0))
        lat2, lon2 = self.point_to_lat(wanted_points=(self.user_settings.size.width, self.user_settings.size.height))
        lats = [lat1, lat2]
        lons = [lon1, lon2]
        return min(lats), max(lats), min(lons), max(lons)

    def get_resolution(self) -> float:
        resolution = 156543.03 * math.cos(math.radians(self.user_settings.lat)) / (math.pow(2, self.user_settings.zoom))
        return resolution

    def get_marker_size(self, size: int = 20) -> int:
        result = size * (math.pow(2, self.user_settings.zoom))
        end_size = int(result // 50000)
        min_size = int((self.user_settings.size.width * size) // 500)
        return int(round(max(end_size, min_size) * self.user_settings.marker_multiplier))

    @staticmethod
    def _get_meters() -> float:
        earth = 6373.0
        meters = 40 * ((1 / ((2 * math.pi / 360) * earth)) / 1000)  # meter in degree * 40
        return meters

    def get_lat_offset(self) -> float:
        meters = self._get_meters()
        resolution = self.get_resolution()
        return meters * resolution * self.user_settings.move_multiplier

    def get_lon_offset(self) -> float:
        meters = self._get_meters()
        resolution = self.get_resolution()
        return (meters / math.cos((math.pi / 180))) * resolution * self.user_settings.move_multiplier

    async def set_map(self, attempt: int = 0):
        if attempt >= 3:
            self.embed.set_footer(text="Sorry, there was an error loading the map")
            return
        self.hit_limit = False
        async with aiohttp.ClientSession() as session:
            async with session.post(self.url + "?pregenerate=true", json=self.get_data()) as resp:
                pregen_id = await resp.text()
                if "error" in pregen_id:
                    log.warning("Tileserver threw an error. Retrying", pregen_id)
                    resp.close()
                    await session.close()
                    await self.set_map(attempt + 1)
                else:
                    self.embed.set_image(url=self.url + "/pregenerated/" + pregen_id)
                    footer = ""
                    if self.hit_limit:
                        footer = f"\nYou hit the marker limit of {bot.config.DMAP_MARKER_LIMIT}." \
                                 f" Try zooming in or decrease categories and filters"
                    self.embed.set_footer(text=footer)

    def set_gyms(self):
        bbox = self.get_bounds()
        self.display_gyms = []

        if self.user_settings.levels:
            for gym in self.gyms:
                if gym.raid.end > arrow.utcnow() and gym.raid.level in self.user_settings.levels and \
                        bbox[0] <= gym.lat <= bbox[1] and bbox[2] <= gym.lon <= bbox[3]:
                    self.display_gyms.append(gym)

    async def edit(self, interaction: discord.Interaction):
        self.current_page.add_to_embed()
        embeds = [self.embed]
        if self.extra_embed:
            embeds.append(self.extra_embed)
        await interaction.response.edit_message(embeds=embeds, view=self)

    async def send(self):
        self.set_gyms()
        await self.set_map()
        await self.interaction.response.send_message(embed=self.embed, view=self, ephemeral=True)

    async def update(self, interaction: discord.Interaction):
        self.set_gyms()
        await self.set_map()
        await self.edit(interaction)
