from __future__ import annotations

import random
import string
from copy import deepcopy
from enum import Enum
from typing import Dict, Any, Optional, TYPE_CHECKING

import arrow

from taubsi.pogodata import Pokemon, Move

if TYPE_CHECKING:
    from taubsi.core.bot import TaubsiBot
    from taubsi.core.config_classes import Server
    from taubsi.pogodata import PogoData


class Team(Enum):
    NOTEAM = 0
    MYSTIC = 1
    VALOR = 2
    INSTINCT = 3


class Moveset:
    quick: Optional[Move]
    charge: Optional[Move]

    def __init__(self, move_1: Optional[Move] = None, move_2: Optional[Move] = None):
        self.quick = move_1
        self.charge = move_2

    @classmethod
    def from_pokebattler(cls, pogodata: PogoData, **kwargs):
        """
        move_1: str
        move_2: str
        """

        for k, v in kwargs.items():
            move_id = pogodata.move_proto_to_id.get(v, 0)
            kwargs[k] = Move(move_id, pogodata)
        return cls(**kwargs)

    def get_name(self, split: str = " | ", with_markdown: bool = False) -> str:
        if with_markdown:
            return f"**{self.quick.name}**{split}**{self.charge.name}**"
        else:
            return f"{self.quick.name}{split}{self.charge.name}"

    def __str__(self):
        return self.get_name(with_markdown=True)

    def __bool__(self):
        return self.quick is not None or self.charge is not None

    def __getitem__(self, item):
        if item == 0:
            return self.quick
        elif item == 1:
            return self.charge
        raise IndexError


class Raid:
    is_scanned: bool
    is_predicted: bool = False

    level: int
    cp20: int = 0
    cp25: int = 0
    boss: Optional[Pokemon] = None
    name: str = "?"
    pokebattler_name: str = "UNOWN"

    start: Optional[arrow.Arrow]
    end: Optional[arrow.Arrow]
    moveset: Moveset

    def __init__(self, bot: TaubsiBot, raid_data: Dict[str, Any]):
        """
        raid_data:
        {
            "level": int,
            "start": any,
            "end": any,
            "move_1": none/id,
            "move_2": none/id,
            "pokemon_id" ...
        }
        """
        self.level = raid_data["level"]
        self.is_scanned = bool(raid_data.get("start"))

        if self.is_scanned:
            self.start = arrow.get(raid_data.get("start"))
            self.end = arrow.get(raid_data.get("end"))
            if raid_data.get("pokemon_id"):
                move1 = bot.pogodata.get_move(raid_data.get("move_1"))
                move2 = bot.pogodata.get_move(raid_data.get("move_2"))
                self.moveset = Moveset(move_1=move1, move_2=move2)
                self.boss = bot.pogodata.get_pokemon(raid_data)
            else:
                self.moveset = Moveset()

        if not raid_data.get("pokemon_id"):
            available_bosses = bot.pogodata.raids.get(self.level, [])
            if len(available_bosses) == 1:
                self.boss = available_bosses[0]
                self.is_predicted = True

        if self.boss:
            self.name = self.boss.name

            self.pokebattler_name = self.boss.proto_id
            if self.boss.mega_id > 0:
                self.pokebattler_name += "_MEGA"

            ivs = [15, 15, 15]
            self.cp20 = self.boss.cp(20, ivs)
            self.cp25 = self.boss.cp(25, ivs)
        else:
            if self.level != 6:
                self.name = bot.translate("level_egg").format(str(self.level))
            else:
                self.name = bot.translate("mega_egg")

    def __eq__(self, other: Raid):
        if other is None:
            return False
        if self.boss:
            if not other.boss:
                return False
            return self.boss.id == other.boss.id and self.is_predicted == other.is_predicted
        else:
            return not bool(other.boss)

    def copy(self) -> Raid:
        return deepcopy(self)

    @property
    def has_hatched(self) -> bool:
        if not self.is_scanned:
            return self.is_predicted
        return self.start < arrow.utcnow()


class Gym:
    ANONYMIZE = False
    raid: Optional[Raid] = None
    id: str
    name: str = ""
    img: str = ""
    lat: float = 0
    lon: float = 0
    team: Team = Team.NOTEAM
    server: Server
    _bot: TaubsiBot

    def __init__(self, bot_: TaubsiBot, server: Server, data: Dict[str, Any]):
        self._bot = bot_
        self.server = server
        self.id = data.get("id")
        self.update(data)

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

    def update(self, data: Dict[str, Any] = None):
        self.name = data.get("name", self.name)
        self.img = data.get("url", self.img)
        self.lat = data.get("latitude", self.lat)
        self.lon = data.get("longitude", self.lon)
        self.team = Team(data.get("team", self.team.value))

        if self.ANONYMIZE:
            images = [
                "hTi7Ke05iWKztGliRm8gDETLxxA78oC1uuyO4EKfX_ifew3dqSb0PUH4qASyKmHxtdXiwBlRKcZwEYTP5vUHHQiQrg",
                "rnvpFPW_XtAMbQGnu1QpKcj6Zf8NOpsvxp_e0L1OkyL5ZaFBuldXEL8rcd1CQ9qLAVNXt9oKnXelcy8fWjzKUK82dkg",
                "9eAK5n7GPJO726iFZp1HYdxPWvA5v__kFzohu2Q3zUB85IdoYj5FFwELoY7BhCxMLq7MF4-1OplpDJY7B8kODiH_AA",
                "5dwivXDFCOMCDQyMFpAU_p8bqLZODwVyoue1mx2L-JXLlKjSdFyCymxxtk7MDAQjeJ2zinVrTxEdiWXVkpxpvftJho0",
                "qmgitgrJ-Y01yOJqyzX6NC1bGBSk0VExoRuS-ny0T_KSkAMhXzsBVMBnovzHLY0twgbZTWVHJEsMyGs0aubCHqC-4_U",
                "Au3ot4tok-2VeRKVna4xO63CTyIZt0sRJdJrCKWNMPeUQtPaz6L8sTMWQ3Ce9XIxBKm7txiR8tDYp2BiApl9RipUZz8",
                "K_r4uLWXVlJyobkI0vqqWU_tG09gemyCqngWEru2OlW_Re-4oYi3gBtznAnI-0FjeOcwWlEsGsxrdzBAZ25ZWGkf8hsj",
                "4nvIiJgz8pxOzpXckYoOLXo8Y8s21ZFOTf54Eftgfe4exklayC3FMmGIXKoJ0zSitdN7J4hsaSrZQrrE1bC4o9l1IYQ",
                "ecPFbuSVHQoX4lBxyjo8-Q2cydGYxL8udx_akjekdPPsb7LkAFdBmcDK7lLxEcWp0q-gdRXdgsDeFQmFVOLw3x6_wMjn",
                "65WAErK4r9T2KaQuyK8NnyMAc1gh3nc4aBZQwtPTT4iG0OBc7cl7gXkmwRQdGJK4wiIC6wxwk74CIBZWA6vITJGQ3Sg"
            ]
            self.name = "".join(random.choice(string.ascii_uppercase + " .-") for _ in range(len(self.name))).title()
            self.img = "https://lh3.googleusercontent.com/" + random.choice(images)

        if not data.get("end"):
            return

        raid = Raid(self._bot, data)
        if raid != self.raid:
            self.raid = raid

    def get_raid(self, level: int = 0) -> Raid:
        """
        Returns current raid or makes one up
        """
        if self.raid.end < arrow.utcnow() or not self.raid or (level and self.raid.level != level):
            return Raid(self._bot, {"level": level})
        else:
            return self.raid.copy()
