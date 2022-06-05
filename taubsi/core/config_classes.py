from __future__ import annotations
from typing import List, Dict, Optional, TYPE_CHECKING, Tuple
import json
from enum import Enum

import discord
from thefuzz import process, fuzz, utils

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
    level: List[int] | int
    is_event: bool

    def __init__(self, id_: int, level: List[int] | int, is_event: bool = False):
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


class _MatcherMethods:
    @staticmethod
    def fp_ratio(s1, s2, force_ascii=True, full_process=True):
        """
        Return a measure of the sequences' similarity between 0 and 100, using fuzz.ratio and fuzz.partial_ratio.
        """

        if full_process:
            p1 = utils.full_process(s1, force_ascii=force_ascii)
            p2 = utils.full_process(s2, force_ascii=force_ascii)
        else:
            p1 = s1
            p2 = s2

        if not utils.validate_string(p1):
            return 0
        if not utils.validate_string(p2):
            return 0

        # should we look at partials?
        try_partial = True
        partial_scale = .9

        base = fuzz.ratio(p1, p2)
        len_ratio = float(max(len(p1), len(p2))-1) / min(len(p1), len(p2))

        # if strings are similar length, don't use partials
        if len_ratio < 1.3:
            try_partial = False

        if try_partial:
            partial = fuzz.partial_ratio(p1, p2) * partial_scale
            return utils.intr(max(base, partial))
        else:
            return utils.intr(base)

    @staticmethod
    def processor(s, **kwargs):
        return utils.full_process(str(s), **kwargs)


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
    gym_dict: Dict[str, Gym]
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
            f"where ST_CONTAINS(ST_GEOMFROMTEXT('POLYGON({self._sql_fence})'), point(latitude, longitude)) "
            f"order by name asc"
        )
        gyms = await bot.mad_db.execute(query)

        self.gyms = []
        self.gym_dict = {}
        for gym_data in gyms:
            gym = Gym(bot, self, gym_data)
            self._add_gym(gym)
        await self.update_gyms()

        self.guild = await bot.fetch_guild(self.id)

    def _add_gym(self, gym: Gym):
        self.gyms.append(gym)
        self.gym_dict[gym.id] = gym

    async def update_gyms(self):
        # query = (
        #     f"select gym.gym_id as id, url, team_id as team, latitude, longitude, raid.level, raid.start, raid.end, "
        #     f"raid.move_1, raid.move_2, raid.pokemon_id, raid.form, raid.costume, raid.evolution "
        #     f"from gym "
        #     f"left join gymdetails on gymdetails.gym_id = gym.gym_id "
        #     f"left join raid on raid.gym_id = gym.gym_id "
        #     f"where ST_CONTAINS(ST_GEOMFROMTEXT('POLYGON({self._sql_fence})'), point(latitude, longitude))"
        # )
        query = (
            f"select id, url, team_id as team, lat as latitude, lon as longitude, raid_level as level, "
            f"raid_battle_timestamp as start, raid_end_timestamp as end, raid_pokemon_move_1 as move_1, "
            f"raid_pokemon_move_2 as move_2, raid_pokemon_id as pokemon_id, raid_pokemon_form as form, "
            f"raid_pokemon_costume as costume, raid_pokemon_evolution as evolution "
            f"from gym "
            f"where ST_CONTAINS(ST_GEOMFROMTEXT('POLYGON({self._sql_fence})'), point(lat, lon))"
        )
        gyms = await self._bot.rdm_db.execute(query)
        for data in gyms:
            gym = self.get_gym(data["id"])
            if gym:
                gym.update(data)
            else:
                gym = Gym(self._bot, self, data)
                self._add_gym(gym)

    def get_gym(self, id_: str) -> Optional[Gym]:
        return self.gym_dict.get(id_)

    def match_gyms(self, word: str, limit: int = 10) -> List[Tuple[Gym, int]]:
        matches = process.extractBests(word, choices=self.gyms, scorer=_MatcherMethods.fp_ratio, limit=limit,
                                       score_cutoff=0, processor=_MatcherMethods.processor)

        best_matches = [m for m in matches if m[1] >= 95]
        if best_matches:
            return best_matches

        good_matches = [m for m in matches if m[1] >= 90]
        if good_matches:
            return good_matches

        return matches


class Area:
    name: str
    lat: float
    lon: float
    zoom: float

    def __init__(self, name: str, lat: float, lon: float, zoom: float):
        self.name = name
        self.lat = lat
        self.lon = lon
        self.zoom = zoom


class Style:
    name: str
    id: str

    def __init__(self, id_: str, name: str):
        self.id = id_
        self.name = name


class BaseConfig:
    TRASH_CHANNEL_ID: int
    TRASH_GUILD_ID: int
    LANGUAGE: Language = Language.ENGLISH
    BOT_TOKEN: str
    ADMIN_IDS = List[int]
    COGS: List[Cog]
    LOADING_GIF: str = "https://mir-s3-cdn-cf.behance.net/project_modules/disp/c3c4d331234507.564a1d23db8f9.gif"

    FRIEND_CODE: str

    MAD_DB_NAME: str
    TAUBSI_DB_NAME: str
    RDM_DB_NAME: str = "rdm"
    DB_HOST: str = "0.0.0.0"
    DB_PORT: int = 3306
    DB_USER: str
    DB_PASS: str

    DMAP_STYLES: List[Style]
    DMAP_MARKER_LIMIT: int
    DMAP_AREAS: List[Area]

    NUMBER_EMOJIS: Dict[int, str]
    CONTROL_EMOJIS: Dict[str, str]
    TEAM_EMOJIS: Dict[int, str]
    TEAM_COLORS: Dict[int, int]
    BADGE_LEVELS: Dict[int, str]
    DMAP_EMOJIS: Dict[str, str]
