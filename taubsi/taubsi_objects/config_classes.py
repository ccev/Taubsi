from __future__ import annotations
import json
from enum import Enum
from typing import List, Dict, Optional, TYPE_CHECKING
import discord

from taubsi.utils.logging import log
from taubsi.cogs.raids.pogo import Gym

if TYPE_CHECKING:
    from start_taubsi import TaubsiBot


class Cog(Enum):
    RAIDS = "taubsi.cogs.raids.raid_cog"
    SETUP = "taubsi.cogs.setup.setup_cog"
    MAIN_LOOPS = "taubsi.cogs.loop"
    RAIDINFO = "taubsi.cogs.raids.info_cog"
    DMAP = "taubsi.cogs.dmap.dmap_cog"
    AUTOSETUP = "taubsi.cogs.setup.auto_setup_cog"
    PLAYERSTATS = "taubsi.cogs.playerstats.playerstats_cog"
    ARTICLEPREVIEW = "taubsi.cogs.articlepreview.preview_cog"

    @classmethod
    def all(cls):
        return list(cls)

    @classmethod
    def basic(cls):
        return [cls.RAIDS, cls.SETUP, cls.MAIN_LOOPS, cls.RAIDINFO, cls.DMAP]

    @classmethod
    def v(cls):
        return list(cls)[:-1]


class Language(Enum):
    GERMAN = 0
    ENGLISH = 1


class RaidChannel:
    id: int
    level: int
    is_event: bool

    def __init__(self, id_: int, level: int, is_event: bool = False):
        self.id = id_
        self.level = level
        self.is_event = is_event


class InfoChannel:
    id: int
    levels: List[int]
    post_to: List[int]

    def __init__(self, id_: int, levels: List[int], post_to: Optional[List[int]] = None):
        self.id = id_
        self.levels = levels

        if post_to:
            self.post_to = post_to
        else:
            self.post_to = []


class DMapMessage:
    id: int
    post_to: Dict[int, List[int]]

    def __init__(self, id_: int, post_to: Optional[Dict[int, List[int]]] = None):
        self.id = id_
        if post_to:
            self.post_to = post_to
        else:
            self.post_to = {}


class Server:
    name: str
    id: int
    geofence: str
    raid_channels: List[RaidChannel]
    info_channels: List[InfoChannel]
    dmap_messages: List[DMapMessage]
    gyms: List[Gym]
    guild: discord.Guild
    _raw_fences: list

    def __init__(self,
                 name: str,
                 id_: int,
                 geofence: str,
                 raid_channels: List[RaidChannel],
                 info_channels: List[InfoChannel],
                 dmap_messages: List[DMapMessage]):
        self.name = name
        self.id = id_
        self.geofence = geofence.lower()
        self.raid_channels = raid_channels
        self.info_channels = info_channels
        self.dmap_messages = dmap_messages

        with open("geofence.json", "r") as f:
            self._raw_fences = json.load(f)

    @staticmethod
    def _convert_path_sql(fence):
        sql_fence = []
        for lat, lon in fence:
            sql_fence.append(f"{lat} {lon}")
        sql_fence.append(f"{fence[0][0]} {fence[0][1]}")

        return "(" + ",".join(sql_fence) + ")"

    async def load(self, bot: TaubsiBot):
        sql_fence = False
        for fence in self._raw_fences:
            if fence["name"].lower() == self.geofence.lower():
                sql_fence = self._convert_path_sql(fence["path"])
                break
        if not sql_fence:
            log.error(f"No geofence found for {self.name}")
            raise

        query = (
            f"select name, gym.gym_id as id, url, latitude, longitude "
            f"from gymdetails "
            f"left join gym on gym.gym_id = gymdetails.gym_id "
            f"where ST_CONTAINS(ST_GEOMFROMTEXT('POLYGON({sql_fence})'), point(latitude, longitude))"
        )
        gyms = await bot.mad_db.execute(query)

        self.gyms = []
        for gym_data in gyms:
            self.gyms.append(Gym(gym_data))

        self.guild = await bot.fetch_guild(self.id)


class BaseConfig:
    TRASH_CHANNEL_ID: int
    LANGUAGE: Language = Language.ENGLISH
    BOT_TOKEN: str
    ADMIN_IDS = List[int]
    COGS: List[Cog]

    FRIEND_CODE: str

    MAD_DB_NAME: str
    TAUBSI_DB_NAME: str
    DB_HOST: str = "0.0.0.0"
    DB_PORT: int = 3306
    DB_USER: str
    DB_PASS: str
