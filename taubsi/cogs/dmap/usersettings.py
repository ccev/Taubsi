from __future__ import annotations
from enum import Enum
from typing import List, Dict, Any
from taubsi.core.config_classes import Style, Area
from taubsi.core.uicons import IconSet
from taubsi.core import bot


class Size:
    def __init__(self, name: str, width: int, height: int):
        self.name = name
        self.width = width
        self.height = height

    @classmethod
    def default(cls):
        return cls("Standard", 700, 400)

    @classmethod
    def p720(cls):
        return cls("720p", 1280, 720)

    @classmethod
    def p1080(cls):
        return cls("1080p", 1920, 1080)

    @classmethod
    def r4_3(cls):
        return cls("4:3", 800, 600)

    @classmethod
    def vertical(cls):
        return cls("Vertical", 400, 700)


class SizePreset(Enum):
    DEFAULT = Size.default()
    HD = Size.p720()
    FULL_HD = Size.p1080()
    R4_3 = Size.r4_3()
    VERTICAL = Size.vertical()


class UserSettings:
    user_id: int
    zoom: float
    lat: float
    lon: float
    style: Style
    move_multiplier: float
    marker_multiplier: float
    levels: List[int]
    iconset: IconSet
    size: Size

    def __init__(self, user_id: int):
        self.user_id = user_id

    @classmethod
    def default(cls, user_id: int) -> UserSettings:
        self = cls(user_id)
        init_area = bot.config.DMAP_AREAS[0]
        self.jump_to_area(init_area)
        self.size = SizePreset.DEFAULT.value
        self.style = bot.config.DMAP_STYLES[0]

        self.levels = [5]
        self.move_multiplier = 1
        self.marker_multiplier = 1

        self.iconset = IconSet.POGO_OUTLINE

        return self

    @classmethod
    def from_db(cls, data: Dict[str, Any]):
        self = cls(data["user_id"])
        self.size = SizePreset.DEFAULT.value
        self.zoom = data["zoom"]
        self.lat = data["lat"]
        self.lon = data["lon"]
        self.move_multiplier = data["move_multiplier"]
        self.marker_multiplier = data["marker_multiplier"]
        self.iconset = list(IconSet)[data["iconset"]]

        style: str = data["style"]
        self.style = bot.config.DMAP_STYLES[0]
        for possible_style in bot.config.DMAP_STYLES:
            if possible_style.id == style:
                self.style = possible_style

        levels: str = data["levels"]
        self.levels = list(map(int, levels.split(",")))  # "1,2,3" -> [1, 2, 3]

        return self

    async def update_db(self):
        icon_index = 0
        for index, iconset in enumerate(IconSet):
            if iconset == self.iconset:
                icon_index = index
                break
        args = {
            "user_id": self.user_id,
            "zoom": self.zoom,
            "lat": self.lat,
            "lon": self.lon,
            "style": self.style.id,
            "move_multiplier": self.move_multiplier,
            "marker_multiplier": self.marker_multiplier,
            "levels": ",".join(map(str, self.levels)),
            "iconset": icon_index
        }
        await bot.taubsi_db.insert("dmap", args)

    def jump_to_area(self, area: Area):
        self.lat = area.lat
        self.lon = area.lon
        self.zoom = area.zoom
