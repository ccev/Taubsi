from __future__ import annotations
from typing import List, Dict, Optional, TYPE_CHECKING
import json
from enum import Enum

import discord

from taubsi.core.logging import log
from taubsi.core.pogo import Gym
from taubsi.core.cogs import Cog

if TYPE_CHECKING:
    from taubsi.core.bot import TaubsiBot


class Language(Enum):
    GERMAN = "german"
    ENGLISH = "english"


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
    gyms: List[Gym]
    channel: discord.TextChannel

    def __init__(self, id_: int, levels: List[int], post_to: Optional[List[int]] = None):
        self.id = id_
        self.levels = levels

        if post_to:
            self.post_to = post_to
        else:
            self.post_to = []

    def set_gyms(self, gyms: List[Gym]):
        self.gyms = gyms


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
    team_choose_ids: List[int]
    gyms: List[Gym]
    guild: discord.Guild
    _bot: TaubsiBot
    _raw_fences: list
    _gym_dict: Dict[str, Gym]
    _sql_fence: Optional[str] = None

    def __init__(self,
                 name: str,
                 id_: int,
                 geofence: str,
                 raid_channels: List[RaidChannel],
                 info_channels: List[InfoChannel],
                 dmap_messages: List[DMapMessage],
                 team_choose: List[int]):
        self.name = name
        self.id = id_
        self.geofence = geofence.lower()
        self.raid_channels = raid_channels
        self.info_channels = info_channels
        self.dmap_messages = dmap_messages
        self.team_choose_ids = team_choose

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
        self._bot = bot
        for fence in self._raw_fences:
            if fence["name"].lower() == self.geofence.lower():
                self._sql_fence = self._convert_path_sql(fence["path"])
                break
        if not self._sql_fence:
            log.error(f"No geofence found for {self.name}")
            raise

        query = (
            f"select name, gym.gym_id as id, url, latitude, longitude "
            f"from gymdetails "
            f"left join gym on gym.gym_id = gymdetails.gym_id "
            f"where ST_CONTAINS(ST_GEOMFROMTEXT('POLYGON({self._sql_fence})'), point(latitude, longitude))"
        )
        gyms = await bot.mad_db.execute(query)

        self.gyms = []
        self._gym_dict = {}
        for gym_data in gyms:
            gym = Gym(bot, self, gym_data)
            self.gyms.append(gym)
            self._gym_dict[gym.id] = gym
        await self.update_gyms()

        self.guild = await bot.fetch_guild(self.id)

    async def update_gyms(self):
        query = (
            f"select gym.gym_id as id, url, team_id as team, latitude, longitude, raid.level, raid.start, raid.end, "
            f"raid.move_1, raid.move_2, raid.pokemon_id, raid.form, raid.costume, raid.evolution "
            f"from gym "
            f"left join gymdetails on gymdetails.gym_id = gym.gym_id "
            f"left join raid on raid.gym_id = gym.gym_id "
            f"where ST_CONTAINS(ST_GEOMFROMTEXT('POLYGON({self._sql_fence})'), point(latitude, longitude))"
        )
        gyms = await self._bot.mad_db.execute(query)
        for data in gyms:
            gym = self.get_gym(data["id"])
            if gym:
                gym.update(data)

    def get_gym(self, id_: str) -> Optional[Gym]:
        return self._gym_dict.get(id_)


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
