from __future__ import annotations
from typing import Optional, List
import aiohttp
import arrow
import discord
import math
from time import time

from taubsi.cogs.dmap.buttons import (EmptyButton, MultiplierButton, UpButton, LeftButton, DownButton,
                                      RightButton, ZoomInButton, ZoomOutButton, SettingsButton)
from taubsi.cogs.dmap.areaselect import AreaSelect
from taubsi.cogs.dmap.levelselect import LevelSelect
from taubsi.core import bot, Gym
from taubsi.core.config_classes import Area, Style
from taubsi.core.uicons import IconSet


class Map(discord.ui.View):
    zoom: float
    lat: float
    lon: float
    style: Style = bot.config.DMAP_STYLES[0]
    multiplier: float = 1
    marker_multiplier: float = 1
    levels: List[int]

    author_id: int
    url: str = bot.config.TILESERVER_URL + "staticmap"
    embed: discord.Embed
    start: float

    width: int = 700
    height: int = 400
    scale: int = 1
    hit_limit: bool = False

    iconset: IconSet = IconSet.POGO_OUTLINE
    interaction: discord.Interaction
    gyms: List[Gym]
    display_gyms: List[Gym]

    def __init__(self, interaction: discord.Interaction):
        super().__init__(timeout=None)
        self.start = time()
        init_area = bot.config.DMAP_AREAS[0]
        self.zoom = init_area.zoom
        self.lat = init_area.lat
        self.lon = init_area.lon
        self.author_id = interaction.user.id
        self.display_gyms = []
        self.interaction = interaction
        self.levels = [5]

        server = [s for s in bot.servers if s.id == interaction.guild_id]
        if not server:
            raise
        server = server[0]
        self.gyms = server.gyms

        self.embed = discord.Embed()

        for item in [
            LevelSelect(self),
            AreaSelect(self),
            EmptyButton(0), UpButton(self), EmptyButton(1), ZoomInButton(self),
            LeftButton(self), DownButton(self), RightButton(self), ZoomOutButton(self),
            SettingsButton(self), MultiplierButton(self)
        ]:
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
            "style": self.style.id,
            "latitude": self.lat,
            "longitude": self.lon,
            "zoom": self.zoom,
            "width": self.width,
            "height": self.height,
            "format": "png",
            "scale": self.scale
        }
        if self.display_gyms:
            markers = []
            for gym in self.display_gyms:
                if len(markers) >= bot.config.DMAP_MARKER_LIMIT:
                    self.hit_limit = True
                    break

                gym_size = self.get_marker_size(26)
                markers.append(self._get_marker(gym=gym,
                                                url=bot.uicons.gym(gym, iconset=self.iconset),
                                                size=gym_size,
                                                y_offset=gym_size // -2))

                boss_size = self.get_marker_size(20)
                if gym.raid.boss:
                    boss_marker = self._get_marker(gym=gym,
                                                   url=bot.uicons.pokemon(gym.raid.boss, iconset=self.iconset),
                                                   size=boss_size)
                else:
                    boss_marker = self._get_marker(gym=gym,
                                                   url=bot.uicons.egg(gym.raid, iconset=self.iconset),
                                                   size=boss_size)
                boss_marker["y_offset"] = - self.get_marker_size(19)
                boss_marker["x_offset"] = - self.get_marker_size(5)
                markers.append(boss_marker)
            data.update({
                "markers": markers
            })
        return data

    def start_load(self):
        self.start = time()

    def is_author(self, check_id: int):
        return check_id == self.author_id

    def point_to_lat(self, wanted_points):
        # copied from https://help.openstreetmap.org/questions/75611/transform-xy-pixel-values-into-lat-and-long
        c = (256 / (2 * math.pi)) * 2 ** self.zoom

        xcenter = c * (math.radians(self.lon) + math.pi)
        ycenter = c * (math.pi - math.log(math.tan((math.pi / 4) + math.radians(self.lat) / 2)))

        xpoint = xcenter - (self.width / 2 - wanted_points[0])
        ypoint = ycenter - (self.height / 2 - wanted_points[1])

        c = (256 / (2 * math.pi)) * 2 ** self.zoom
        m = (xpoint / c) - math.pi
        n = -(ypoint / c) + math.pi

        fin_lon = math.degrees(m)
        fin_lat = math.degrees((math.atan(math.e ** n) - (math.pi / 4)) * 2)

        return fin_lat, fin_lon

    def get_bounds(self):
        lat1, lon1 = self.point_to_lat(wanted_points=(0, 0))
        lat2, lon2 = self.point_to_lat(wanted_points=(self.width, self.height))
        lats = [lat1, lat2]
        lons = [lon1, lon2]
        return min(lats), max(lats), min(lons), max(lons)

    def get_resolution(self) -> float:
        resolution = 156543.03 * math.cos(math.radians(self.lat)) / (math.pow(2, self.zoom))
        return resolution

    def get_marker_size(self, size: int = 20) -> int:
        result = size * (math.pow(2, self.zoom))
        end_size = int(result // 50000)
        min_size = int((self.width * size) // 500)
        return int(round(max(end_size, min_size) * self.marker_multiplier))

    @staticmethod
    def _get_meters() -> float:
        earth = 6373.0
        meters = 40 * ((1 / ((2 * math.pi / 360) * earth)) / 1000)  # meter in degree * 40
        return meters

    def get_lat_offset(self) -> float:
        meters = self._get_meters()
        resolution = self.get_resolution()
        return meters * resolution * self.multiplier

    def get_lon_offset(self) -> float:
        meters = self._get_meters()
        resolution = self.get_resolution()
        return (meters / math.cos((math.pi / 180))) * resolution * self.multiplier

    def jump_to_area(self, area: Area):
        self.lat = area.lat
        self.lon = area.lon
        self.zoom = area.zoom

    async def set_map(self, attempt: int = 0):
        if attempt >= 3:
            self.embed.set_footer(text="Sorry, there was an error loading the map")
            return
        self.hit_limit = False
        async with aiohttp.ClientSession() as session:
            async with session.post(self.url + "?pregenerate=true", json=self.get_data()) as resp:
                pregen_id = await resp.text()
                if "error" in pregen_id:
                    print("Tileserver threw an error. Retrying", pregen_id)
                    resp.close()
                    await session.close()
                    await self.set_map(attempt + 1)
                else:
                    self.embed.set_image(url=self.url + "/pregenerated/" + pregen_id)
                    footer = f"This took {round(time() - self.start, 3)}s"
                    if self.hit_limit:
                        footer += f"\nYou hit the marker limit of {bot.config.DMAP_MARKER_LIMIT}." \
                                  f" Try zooming in or decrease categories and filters"
                    self.embed.set_footer(text=footer)

    def set_gyms(self):
        bbox = self.get_bounds()
        self.display_gyms = []

        if self.levels:
            for gym in self.gyms:
                if gym.raid.end > arrow.utcnow() and gym.raid.level in self.levels and \
                        bbox[0] <= gym.lat <= bbox[1] and bbox[2] <= gym.lon <= bbox[3]:
                    self.display_gyms.append(gym)

    async def edit(self, interaction: discord.Interaction):
        await interaction.response.edit_message(embed=self.embed, view=self)

    async def send(self):
        self.set_gyms()
        await self.set_map()
        await self.interaction.response.send_message(embed=self.embed, view=self, ephemeral=True)

    async def update(self, interaction: discord.Interaction):
        self.set_gyms()
        await self.set_map()
        await self.edit(interaction)
