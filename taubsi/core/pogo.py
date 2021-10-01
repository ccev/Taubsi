from __future__ import annotations
from typing import Union, Dict, Any, Optional, TYPE_CHECKING, List
from io import BytesIO
from enum import Enum
from datetime import datetime

import arrow
import discord
from PIL import Image, ImageDraw
from pogodata.objects import Move
from pogodata.pokemon import Pokemon

from taubsi.utils.utils import asyncget, calculate_cp
from taubsi.core.logging import log

if TYPE_CHECKING:
    from taubsi.core.bot import TaubsiBot


class Team(Enum):
    NOTEAM = 0
    MYSTIC = 1
    VALOR = 2
    INSTINCT = 3


class Raid:
    is_scanned: bool
    is_predicted: bool = False

    boss: Optional[Pokemon]

    level: int
    cp20: int = 0
    cp25: int = 0
    boss: Optional[Pokemon]
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
        else:
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
                self.name = f"Level {self.level} Ei"
            else:
                self.name = "Mega Ei"

    def __eq__(self, other: Raid):
        return True

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

    def __init__(self, bot: TaubsiBot, data: Dict[str, Any]):
        self._bot = bot
        self.id = data.get("id")
        self.update(data)

    def update(self, data: Dict[str, Any], raid_data: Optional[dict] = None):
        self.name = data.get("name", self.name)
        self.img = data.get("url", self.img)
        self.lat = data.get("latitude", self.lat)
        self.lon = data.get("longitude", self.lon)
        self.team = Team(data.get("team", self.team.value))

        if raid_data and raid_data["end"] > datetime.utcnow():
            self.set_raid(raid_data)
        else:
            if self.raid and self.raid.is_scanned:
                self.raid = None

    async def set_raid(self, raid_data: Optional[dict] = None):
        if raid_data:
            self.raid = Raid(self._bot, raid_data)
        else:
            query = (
                f"select level, pokemon_id, form, costume, start, end, move_1, move_2, evolution "
                f"from raid "
                f"where gym_id = '{self.id}' and end > utc_timestamp()"
            )
            raid = await self._bot.mad_db.execute(query)
            if not raid:
                return
            self.raid = Raid(self._bot, raid)

    def get_raid(self, level: int = 0) -> Raid:
        """
        Returns current raid or makes one up
        """
        if not self.raid or (level and self.raid.level != level):
            return Raid(self._bot, {"level": level})
        else:
            return self.raid

    async def get_raid_image(self) -> str:
        """
        Generate a circuar Gym Img with the boss in front of it.
        Similiar to how it'd show on the in-game nearby view.
        """
        if not self.raid:
            return ""

        if self.raid.boss:
            mon_size = (105, 105)
        else:
            mon_size = (95, 95)
        boss_result = await asyncget(self._bot.uicons.raid(self.raid, shiny_chance=30))
        log.info(f"Creating a Raid Icon for Gym {self.name}")
        gym_result = await asyncget(self.img)

        gymstream = BytesIO(gym_result)
        bossstream = BytesIO(boss_result)
        gym = Image.open(gymstream).convert("RGBA")

        # gym resizing
        size = min(gym.size)
        gym = gym.crop((gym.width - size) // 2,
                       (gym.height - size) // 2,
                       (gym.width + size) // 2,
                       (gym.height + size) // 2)

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

        monbg = Image.new("RGBA", bg.size, 0)
        mon = mon.resize(mon_size, Image.ANTIALIAS)
        monbg.paste(mon, (bg.size[0]-mon.width, bg.size[1]-mon.height))

        final_img = Image.alpha_composite(bg, monbg)

        with BytesIO() as stream:
            final_img.save(stream, "PNG")
            stream.seek(0)
            image_msg = await self._bot.trash_channel.send(file=discord.File(stream, filename="raid-icon.png"))
            final_link = image_msg.attachments[0].url

        gymstream.close()
        bossstream.close()

        return final_link
