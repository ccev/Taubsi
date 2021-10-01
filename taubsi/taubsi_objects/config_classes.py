from enum import Enum
from typing import List, Dict, Optional
import discord


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

    def __init__(self,
                 name: str,
                 id_: int,
                 geofence: str,
                 raid_channels: List[RaidChannel],
                 info_channels: List[InfoChannel],
                 dmap_messages: List[DMapMessage]):
        self.name = name
        self.id = id_
        self.geofence = geofence
        self.raid_channels = raid_channels
        self.info_channels = info_channels
        self.dmap_messages = dmap_messages


class BaseConfig:
    TRASH_CHANNEL: discord.TextChannel
    TRASH_CHANNEL_ID: int
    LANGUAGE: Language = Language.ENGLISH
    BOT_TOKEN: str
    ADMIN_IDS = List[int]

    FRIEND_CODE: str

    MAD_DB_NAME: str
    TAUBSI_DB_NAME: str
    DB_HOST: str = "0.0.0.0"
    DB_PORT: int = 3306
    DB_USER: str
    DB_PASS: str
