from __future__ import annotations
import random
from io import BytesIO
from typing import Union, Dict, Any, Optional, TYPE_CHECKING, List

import discord
import arrow
from PIL import Image, ImageDraw
from pogodata.objects import Move
from pogodata.pokemon import Pokemon

from taubsi.utils.utils import asyncget, calculate_cp
from taubsi.utils.logging import logging
from taubsi.taubsi_objects import tb

if TYPE_CHECKING:
    from start_taubsi import TaubsiBot

log = logging.getLogger("Raids")


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
            available_bosses = tb.pogodata.raids[self.level]
            if len(available_bosses) == 1:
                self.boss = available_bosses[0]
                self.is_predicted = True

        if self.boss:
            self.name = self.boss.name

            self.pokebattler_name = self.boss.base_template
            if self.boss.temp_evolution_id > 0:
                self.pokebattler_name += "_MEGA"

            if self.boss.temp_evolution_id > 0:
                stats = tb.pogodata.get_mon(template=self.boss.base_template).stats
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

    def __init__(self, bot: TaubsiBot, data: Dict[str, Any]):
        self._bot = bot
        self.id = data.get("id")
        self.name = data.get("name")
        self.img = data.get("url")
        self.lat = data.get("latitude")
        self.lon = data.get("longitude")
        self.team = 0

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


# TODO: remove below

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


    async def get_active_raid(self, level: int) -> Union[BaseRaid, ScannedRaid]:
        query = (
            f"select level, pokemon_id, form, costume, start, end, move_1, move_2, evolution "
            f"from raid "
            f"where gym_id = '{self.id}'"
        )
        result = await tb.queries.execute(query)
        db_level, mon_id, form, costume, start, end, move_1, move_2, evolution = result[0]
        start = arrow.get(start)
        end = arrow.get(end)

        if end > arrow.utcnow() and db_level == level:
            if mon_id:
                mon = tb.pogodata.get_mon(id=mon_id, form=form, costume=costume, temp_evolution_id=evolution)
                move1 = tb.pogodata.get_move(id=move_1)
                move2 = tb.pogodata.get_move(id=move_2)
            else:
                mon = None
                move1 = None
                move2 = None
            return ScannedRaid(self, move1, move2, start, end, mon, level)

        return BaseRaid(self, level)


class BaseRaid:
    def __init__(self, gym: Gym, level: int = 5):
        self.level = level
        self.gym = gym

        self.cp20 = 0
        self.cp25 = 0
        self.boss = None
        self.name = "?"
        self.pokebattler_name = "UNOWN"

        available_bosses = tb.pogodata.raids[level]
        boss = None
        if len(available_bosses) == 1:
            boss = available_bosses[0]
        self.make_boss(boss)

    def make_boss(self, boss=None):
        if boss:
            self.boss = boss
            self.name = self.boss.name

            self.pokebattler_name = self.boss.base_template
            if self.boss.temp_evolution_id > 0:
                self.pokebattler_name += "_MEGA"

            if boss.temp_evolution_id > 0:
                stats = tb.pogodata.get_mon(template=self.boss.base_template).stats
            else:
                stats = self.boss.stats
            self.cp20 = calculate_cp(20, stats, [15, 15, 15])
            self.cp25 = calculate_cp(25, stats, [15, 15, 15])
        else:
            if self.level != 6:
                self.name = f"Level {self.level} Ei"
            else:
                self.name = "Mega Ei"

    @property
    def compare(self):
        if self.boss:
            return str(self.boss.id) + "f" + str(self.boss.form) + "e" + str(self.boss.temp_evolution_id)
        else:
            return ""

    async def get_image(self):
        """
        Generate a circuar Gym Img with the boss in front of it.
        Similiar to how it'd show on the in-game nearby view.
        """
        if self.boss:
            mon_size = (105, 105)
        else:
            mon_size = (95, 95)
        boss_result = await asyncget(tb.uicons.raid(self, shiny_chance=30))
        log.info(f"Creating a Raid Icon for Gym {self.gym.name}")
        gym_result = await asyncget(self.gym.img)

        gymstream = BytesIO(gym_result)
        bossstream = BytesIO(boss_result)
        gym = Image.open(gymstream).convert("RGBA")

        # gym resizing
        size = min(gym.size)
        gym = gym.crop(((gym.width - size) // 2, (gym.height - size) // 2, (gym.width + size) // 2, (gym.height + size) // 2))

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
            image_msg = await tb.trash_channel.send(file=discord.File(stream, filename="raid-icon.png"))
            final_link = image_msg.attachments[0].url

        gymstream.close()
        bossstream.close()

        return final_link


class ScannedRaid(BaseRaid):
    def __init__(self, gym: Gym, move_1: Move, move_2: Move, start: arrow.Arrow, end: arrow.Arrow, mon: Pokemon,
                 level: int = 5):
        super().__init__(gym, level)
        self.moves = [move_1, move_2]
        self.start = start
        self.end = end

        if mon:
            self.make_boss(mon)

    @property
    def compare(self):
        compare = super().compare
        if self.moves[0]:
            return str(self.moves[0].id) + "-" + str(self.moves[1].id)
        else:
            return "s" + compare
