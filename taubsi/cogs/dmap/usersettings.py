from __future__ import annotations
from enum import Enum
from typing import List
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
        return cls("Vertikal", 400, 700)


class SizePreset(Enum):
    DEFAULT = Size.default()
    HD = Size.p720()
    FULL_HD = Size.p1080()
    R4_3 = Size.r4_3()
    VERTICAL = Size.vertical()


class UserSettings:
    zoom: float
    lat: float
    lon: float
    style: Style
    move_multiplier: float
    marker_multiplier: float
    levels: List[int]
    iconset: IconSet
    size: Size

    @classmethod
    def default(cls) -> UserSettings:
        self = cls()
        init_area = bot.config.DMAP_AREAS[0]
        self.jump_to_area(init_area)
        self.size = SizePreset.DEFAULT.value
        self.style = bot.config.DMAP_STYLES[0]

        self.levels = [5]
        self.move_multiplier = 1
        self.marker_multiplier = 1

        self.iconset = IconSet.POGO_OUTLINE

        return self

    def jump_to_area(self, area: Area):
        self.lat = area.lat
        self.lon = area.lon
        self.zoom = area.zoom
