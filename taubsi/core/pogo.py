from __future__ import annotations
from typing import Dict, Any, Optional, TYPE_CHECKING, List
from io import BytesIO
from enum import Enum
from datetime import datetime
from copy import deepcopy

import arrow
import discord
from PIL import Image, ImageDraw
from pogodata.objects import Move
from pogodata.pokemon import Pokemon

from taubsi.utils.utils import asyncget, calculate_cp
from taubsi.core.logging import log

if TYPE_CHECKING:
    from taubsi.core.bot import TaubsiBot
    from taubsi.core.config_classes import Server


class Team(Enum):
    NOTEAM = 0
    MYSTIC = 1
    VALOR = 2
    INSTINCT = 3


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
    moves: Optional[List[Move]] = None

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
                move1 = bot.pogodata.get_move(id=raid_data.get("move_1"))
                move2 = bot.pogodata.get_move(id=raid_data.get("move_2"))
                self.moves = [move1, move2]
                self.boss = bot.pogodata.get_mon(id=raid_data.get("pokemon_id"),
                                                 form=raid_data.get("form"),
                                                 costume=raid_data.get("costume"),
                                                 temp_evolution_id=raid_data.get("evolution"))

        if not raid_data.get("pokemon_id"):
            available_bosses = bot.pogodata.raids[self.level]
            if len(available_bosses) == 1:
                self.boss = available_bosses[0]
                self.is_predicted = True

        if self.boss:
            self.name = self.boss.name

            self.pokebattler_name = self.boss.base_template
            if self.boss.temp_evolution_id > 0:
                self.pokebattler_name += "_MEGA"

            if self.boss.temp_evolution_id > 0:
                stats = bot.pogodata.get_mon(template=self.boss.base_template).stats
            else:
                stats = self.boss.stats
            self.cp20 = calculate_cp(20, stats, [15, 15, 15])
            self.cp25 = calculate_cp(25, stats, [15, 15, 15])
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

    def update(self, data: Dict[str, Any] = None):
        self.name = data.get("name", self.name)
        self.img = data.get("url", self.img)
        self.lat = data.get("latitude", self.lat)
        self.lon = data.get("longitude", self.lon)
        self.team = Team(data.get("team", self.team.value))

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

    async def get_raid_image(self, raid: Optional[Raid] = None) -> str:
        """
        Generate a circuar Gym Img with the boss in front of it.
        Similiar to how it'd show on the in-game nearby view.
        """
        if raid is None:
            raid = self.raid
        if not raid:
            return ""

        boss_result = await asyncget(self._bot.uicons.raid(raid, shiny_chance=30))
        log.info(f"Creating a Raid Icon for Gym {self.name}")
        gym_result = await asyncget(self.img)

        gymstream = BytesIO(gym_result)
        bossstream = BytesIO(boss_result)
        gym = Image.open(gymstream).convert("RGBA")

        # gym resizing
        size = min(gym.size)
        gym = gym.crop(((gym.width - size) // 2,
                        (gym.height - size) // 2,
                        (gym.width + size) // 2,
                        (gym.height + size) // 2))

        mask = Image.new("L", (size*2, size*2), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size*2-2, size*2-2), fill=255)
        mask = mask.resize(gym.size, Image.ANTIALIAS)

        result = gym.copy()
        result.putalpha(mask)

        gym = result.resize((128, 128), Image.ANTIALIAS)
        bg = Image.new("RGBA", (150, 150), 0)
        bg.paste(gym)

        # boss resizing & combining
        mon = Image.open(bossstream).convert("RGBA")

        if raid.boss:
            size = 105
        else:
            size = 95
        multiplier = size / max(mon.size)
        mon_size = tuple([int(round(multiplier * s)) for s in mon.size])

        monbg = Image.new("RGBA", bg.size, 0)
        mon = mon.resize(mon_size, Image.ANTIALIAS)
        monbg.paste(mon, (bg.size[0]-mon.width, bg.size[1]-mon.height))

        final_img = Image.alpha_composite(bg, monbg)

        with BytesIO() as stream:
            final_img.save(stream, "PNG")
            stream.seek(0)
            image_msg = await self._bot.trash_channel.send(file=discord.File(stream, filename=f"{self.name}.png"))
            final_link = image_msg.attachments[0].url

        gymstream.close()
        bossstream.close()

        return final_link
